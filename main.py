from dataclasses import dataclass
import requests as req
from lxml import html


@dataclass
class Product:
    title: str
    price: str
    image_url: str
    description: str
    category: str
    content: str
    alcohol_percentage: str
    brewer: str

    def transform_category(self, category):
        pass


class Scraper:
    def __init__(self, start_url, num_pages):
        self.start_url = start_url
        self.num_pages = num_pages
        self.products = []

        self.run()

    def run(self):
        listing_pages = self.get_listing_pages()
        product_pages = []

        with req.Session() as session:
            for listing_page in listing_pages:
                page = session.get(listing_page)
                product_pages.append(self.parse_listing_page(
                    html.fromstring(page.content)))

    def get_listing_pages(self):
        listing_pages = []

        for i in range(1, self.num_pages):
            listing_page_url = self.start_url + '/?page=' + str(i)
            listing_pages.append(listing_page_url)

        return listing_pages

    def parse_listing_page(self, page):
        parent = page.find_class('product-items-container')
        children = parent[0].getchildren()

        print(children[0])

    def parse_product_page(self, page):
        pass


if __name__ == "__main__":
    scraper = Scraper('https://www.beerwulf.com/nl/c/bier', 21)
