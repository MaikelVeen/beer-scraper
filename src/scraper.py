from dataclasses import dataclass
import dataclasses
import asyncio
import aiohttp
import re
import json
import logging
import time
from lxml import html
from lxml import etree


@dataclass
class Product:
    url: str
    title: str
    price: float
    discounted_price: float
    image_url: str
    description: str
    category: str
    content: float
    alcohol_percentage: float
    brewer: str
    country: str
    serving_temperature: int
    serving_glass: str
    beer_colour: str


class BeerwulfScraper:
    def __init__(self, start_url="https://www.beerwulf.com/nl/api/search/searchProducts?pageSize=48", num_pages=22, max_concurrency=200):
        self.start_url = start_url
        self.num_pages = num_pages

        self.seen_listpages = set()
        self.seen_product_pages = set()

        self.session = aiohttp.ClientSession()
        self.bounded_sempahore = asyncio.BoundedSemaphore(max_concurrency)
        self.scraped_products = []

        self.page_scraper = PageScraper()

        self._start_scraper()

    def _start_scraper(self):
        """ Starts the asynchronous scraping process"""
        start_time = time.time()

        future = asyncio.Task(self._run_scraper_async())
        loop = asyncio.get_event_loop()
        loop.run_until_complete(future)
        loop.close()

        with open('output.json', 'w') as fp:
            json.dump(self.scraped_products, fp, cls=EnhancedJSONEncoder)

        print(
            f"Scraped {len(self.scraped_products)} products in {time.time() - start_time} seconds.")

    async def _run_scraper_async(self):
        incomplete_products = await self._get_incomplete_products()
        logging.info(
            "Pagination API responses parsed, continuin to scrape individual product pages")
        self.scraped_products = await self._get_info_products(incomplete_products)
        await self.session.close()

    async def _get_info_products(self, incomplete_products):
        futures = []
        products = []

        for product in incomplete_products:
            if product.url in self.seen_product_pages:
                continue
            self.seen_product_pages.add(product.url)
            futures.append(self._scrape_product_page(product))

        for future in asyncio.as_completed(futures):
            try:
                complete_product = await future
                if complete_product:
                    products.append(complete_product)
            except Exception as e:
                logging.error(
                    f'Exception caught trying to get product urls: {e}')

        return products

    async def _scrape_product_page(self, product):
        page_content = await self._http_get(product.url)
        if page_content:
            return self.page_scraper.parse_page(page_content, product)

    async def _get_incomplete_products(self):
        """ Returns all products with some missing fields that have to be scraped from the product page itself"""
        listing_pages_urls = self._generate_listing_page_urls()

        futures = []
        incomplete_products = []

        for url in listing_pages_urls:
            if url in self.seen_listpages:
                continue
            self.seen_listpages.add(url)
            futures.append(self._extract_products(url))

        for future in asyncio.as_completed(futures):
            try:
                incomplete_products.extend(await future)
            except Exception as e:
                logging.error(
                    f'Exception caught trying to get product urls: {e}')

        return incomplete_products

    async def _extract_products(self, url):
        """ Get product information based on the response from the pagination api"""
        page_content = await self._http_get(url)
        if page_content:
            return self._parse_api_response(page_content)

    def _generate_listing_page_urls(self):
        listing_pages = []

        for i in range(1, self.num_pages):
            listing_page_url = self.start_url + '&page=' + str(i)
            listing_pages.append(listing_page_url)

        return listing_pages

    def _parse_api_response(self, page_content):
        products = []

        # Parse page content bytes to json object
        json_object = json.loads(page_content)

        for item in json_object["items"]:
            # Check against regular expression
            if self._filter_title(item["title"]):
                product = Product(item["contentReference"],
                                  item["title"],
                                  self._parse_price(
                    item["displayInformationPrice"]["price"]),
                    self._parse_price(
                    item["displayInformationPrice"]["discountPrice"]),
                    item["images"][0]["image"],
                    "description",
                    item["style"],
                    item["volume"],
                    item["alcoholPercentage"],
                    "brewer",
                    "country",
                    "serving_temperature",
                    "serving_glass",
                    "beer_colour",)
                products.append(product)
        return products

    def _parse_price(self, price_string):
        if price_string:
            return float(price_string[2:])
        else:
            return ""

    def _filter_title(self, title):
        """ Regular Expression to filter out products that are packs"""
        matches = re.search('(pack)|(verpakking)', title, re.IGNORECASE)
        return not matches

    async def _http_get(self, url):
        """ Async get request helper function"""
        async with self.bounded_sempahore:
            try:
                async with self.session.get(url, timeout=30) as response:
                    content = await response.read()
                    return content
            except Exception as e:
                logging.error(f'Exception caught trying to get {url}: {e}')


class PageScraper:
    """
    Class that groups together methods for parsing the product page
    """

    # Manually copied from css file
    colours = ["#f0eebc", "#f7e385", "#dcb236", "#d5a435", "#c88b2d", "#bb7531",
               "#a7582e", "#984626", "#813124", "#682519", "#501113", "#311214", "#0e0506"]

    @classmethod
    def parse_page(cls, page_content, product):
        try:
            page_parsed = html.fromstring(page_content)

            description = ""
            table_data = None

            parent_product_info = page_parsed.find_class('row product-info')
            child_div = parent_product_info[0].getchildren()[0]
            child_div_data = child_div.getchildren()

            if len(child_div_data) > 1 and child_div_data[0].tag != 'dl':
                description = child_div_data[0].text
                for i in range(1, 5):
                    if child_div_data[i].tag == 'dl':
                        table_data = child_div_data[i].findall('dd')
                        break
            else:
                description = child_div.text.strip()
                table_data = child_div_data[0].findall('dd')

            product.description = description
            product.country = cls.get_country(table_data[3])
            product.brewer = cls.get_brewer(table_data[4])

            serving_parent = cls.get_serving_list(page_parsed)
            product.serving_glass = cls.get_serving_glass(serving_parent)
            product.serving_temperature = cls.get_serving_temp(serving_parent)
            product.beer_colour = cls.get_beer_colour(page_parsed)

            return product

        except Exception as e:
            logging.error(
                f'Exception caught in page parsing: {e} on page {product.url}')
            return None

    @classmethod
    def get_country(cls, data):
        country_children = data.getchildren()
        if country_children:
            return country_children[0].text
        else:
            return data.text

    @classmethod
    def get_serving_list(cls, page):
        return page.find_class('serving no-bullet')[0]

    @classmethod
    def get_serving_temp(cls, parent):
        return parent.getchildren()[0].getchildren()[1].xpath(
            "string()").replace(" ", "").strip('\n\r\s')[12:]

    @classmethod
    def get_serving_glass(cls, parent):
        non_stripped = parent.getchildren()[1].getchildren()[1].xpath(
            "string()").replace(" ", "")
        matches = re.search('(lekker)', non_stripped, re.IGNORECASE)

        if matches:
            return None
        else:
            return non_stripped.strip('\n\r\s')[5:]

    @classmethod
    def get_brewer(cls, data):
        brewer_children = data.getchildren()
        if brewer_children:
            return brewer_children[0].text
        else:
            return data.text.strip()

    @classmethod
    def get_beer_colour(cls, page):
        ebc_children = page.find_class('ebc')[0].getchildren()

        for index, child_div in enumerate(ebc_children):
            if child_div.get('class') == 'active':
                return cls.colours[index]


class EnhancedJSONEncoder(json.JSONEncoder):
    """ Class that makes dataclasses seriazible as json"""

    def default(self, o):
        if dataclasses.is_dataclass(o):
            return dataclasses.asdict(o)
        return super().default(o)


if __name__ == "__main__":
    scraper = BeerwulfScraper()
