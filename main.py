import re
import json
import dataclasses
import time
import requests as req

from dataclasses import dataclass
from lxml import html


@dataclass
class Product:
    title: str
    price: str
    discounted_price: str
    image_url: str
    description: str
    category: str
    content: str
    alcohol_percentage: str
    brewer: str
    country: str


class EnhancedJSONEncoder(json.JSONEncoder):
    """ Class that makes dataclasses seriazible as json"""

    def default(self, o):
        if dataclasses.is_dataclass(o):
            return dataclasses.asdict(o)
        return super().default(o)


class Scraper:
    def __init__(self, start_url, num_pages, debug_on=False):
        self.start_url = start_url
        self.num_pages = num_pages
        self.products = []
        self.debugging = debug_on
        self.run()

    def run(self):
        """
        Main function of scraper
        1. Get a list of Listing Pages
        2. Scrape links to products from listing pages
        3. Scrape product data from product pages

        Raises:
        """

        listing_pages_urls = self.get_listing_pages()
        product_elements = []
        page_parser = ProductPageParser()

        with req.Session() as session:
            for listing_page_url in listing_pages_urls:
                page = session.get(listing_page_url)
                product_elements.extend(self.parse_listing_page(
                    html.fromstring(page.content)))

            if self.debugging:
                print('Found: ' + str(len(product_elements)) +
                      ' products in the listing pages.')

            for product_page in product_elements:
                actual_url = product_page.attrib['href']

                # Pack pages are completely different and are excluded
                matches = re.search('(pack)|(verpakking)', actual_url)

                if matches:
                    continue

                if self.debugging:
                    print('Scraping: ' + actual_url)

                page = session.get('https://www.beerwulf.com' + actual_url)
                product = page_parser.parse_page(html.fromstring(page.content))
                self.products.append(product)

            if self.debugging:
                print('Succesfully scraped ' +
                      str(len(self.products)) + ' products.')
                print('Serializing to json')

            with open('output.json', 'w') as fp:
                json.dump(self.products, fp, cls=EnhancedJSONEncoder)

    def get_listing_pages(self):
        """
        Generates a list of string with all listing page url based on detected routing scheme
        """

        listing_pages = []

        for i in range(1, self.num_pages):
            listing_page_url = self.start_url + '/?page=' + str(i)
            listing_pages.append(listing_page_url)

        return listing_pages

    def parse_listing_page(self, page):
        """
        Returns all links to products on a listing page

        Args:
            page: html document object of listing page
        """

        parent = page.find_class('product-items-container')
        children = parent[0].getchildren()
        return children


class ProductPageParser:
    """
    Class that groups together methods for parsing the product page
    """

    @classmethod
    def parse_page(cls, page_content):
        """
        Parses the page and returns data object

        Args:
            page_content: html document of the product page

        Returns:
            Product (or None in case of malformed page)
        """

        title = cls.get_title(page_content)
        if title is None:
            return None

        price_data = cls.get_price(page_content)
        url = cls.get_url(page_content)
        data = cls.get_additional(page_content)

        if not data:
            return None

        return Product(title,
                       price_data['price'],
                       price_data['discounted_price'],
                       url,
                       data['description'],
                       data['category'],
                       data['content'],
                       data['alcohol_percentage'],
                       data['brewer'],
                       data['country'])

    @classmethod
    def get_title(cls, page_content):
        parent = page_content.find_class('product-detail-info-title')

        # Fallback for broken pages, that will also not have a title
        if not parent:
            return None

        child = parent[0].getchildren()
        return child[0].text

    @classmethod
    def get_price(cls, page_content):
        price_data = {'discounted_price': None}
        discount = page_content.find_class('price from-price')

        if discount:
            price_data['discounted_price'] = page_content.find_class('price')[0].text
            price_data['price'] = discount[0].text
        else:
            price_data['price'] = page_content.find_class('price')[0].text

        return price_data

    @classmethod
    def get_url(cls, page_content):
        parent = page_content.find_class(
            'product-image-sticky image-container js-sticky')
        children = parent[0].getchildren()

        if len(children) > 1:
            image_url = children[1].attrib['src']
        else:
            image_url = children[0].attrib['src']

        image_url_stripped = image_url.split('?')[0]
        return ('https://www.beerwulf.com' + image_url_stripped)

    @classmethod
    def get_additional(cls, page_content):
        """Parses row product-info div that contains the rest of the product data"""

        data = {}
        table_data = None

        parent = page_content.find_class('row product-info')
        child_div = parent[0].getchildren()[0]
        child_div_data = child_div.getchildren()

        if len(child_div_data) > 1 and child_div_data[0].tag != 'dl':
            data['description'] = child_div_data[0].text

            for i in range(1, 5):
                if child_div_data[i].tag == 'dl':
                    table_data = child_div_data[1].findall('dd')
                    break

        else:
            data['description'] = child_div.text.strip()
            table_data = child_div_data[0].findall('dd')

        try:
            data['category'] = table_data[0].getchildren(
            )[0].text.replace(" ", "-").lower()
        except Exception:
            return None

        data['content'] = table_data[1].text
        data['alcohol_percentage'] = table_data[2].text
        data['country'] = cls.get_country(table_data[3])
        data['brewer'] = cls.get_brewer(table_data[4])

        return data

    @classmethod
    def get_country(cls, data):
        country_children = data.getchildren()
        if country_children:
            return country_children[0].text
        else:
            return data.text

    @classmethod
    def get_brewer(cls, data):
        brewer_children = data.getchildren()
        if brewer_children:
            return brewer_children[0].text
        else:
            return data.text.strip()


if __name__ == "__main__":
    scraper = Scraper('https://www.beerwulf.com/nl/c/bier', 21, True)
