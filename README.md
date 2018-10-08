# Beerwulf scraper
Beerwulf scraper is a data scraper that scrapes product information from Beerwulf.com, a large Dutch online beer retailer.

The scraper scrapes all available products, which are about 930 items. Packages of beer are excluded from the scrape.

A json file of the data is included in the repository. The product data that is scraped includes:

| Tables              |
| ------------------- |
| Title               | 
| Price               | 
| Discounted Price    | 
| Description         | 
| Category            | 
| Content             | 
| Alchohol Percentage | 
| Brewer              | 
| Country             |

## Installation
You'll need Python 3.7 for this tool to work, because it makes use of the new @dataclass functionalities.

Also you'll need lxml and requests libraries. You can install them using:

```
pip install requests
pip install lxml
```

## Notes
Please note that this is not a greatly optimized tool. It does scrape a lot of pages, but some of the operations are blocking.

Since we are not making use of Scrapy of async requests it can take a while. Internally this tool was meant for a one-time scrape, therefore no time will be invested in optimizing.

Also note that this tool is based on the exact structure of the html pages. Therefore it is most likely that this tool will break in the future.
