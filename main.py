from dataclasses import dataclass


@dataclass
class Product:
    title: str
    price: str
    image_url: str
    description: str
    category: transform_category(str)
    content: str
    alcohol_percentage: str
    brewer: str


def transform_category(category):
    pass


class Scraper:
    def __init__(self):
        pass
    
    def main(self):
        pass
