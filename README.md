# Special beer scraper
Beerwulf scraper is a data scraper that scrapes product information from Beerwulf.com, a large Dutch online beer retailer. The site is owned by Heiniken, one of the largest beer producers in the world. 

The scraper scrapes all available products, which are about 930 items. Packages of beer are excluded from the scrape.

A json file of the data is included in the repository. This data has been cleaned manually. Anomalies and such have been removed. The product data that is scraped includes:

| Fields              |
| ------------------- |
| Url                 | 
| Title               | 
| Price               | 
| Discounted Price    | 
| Image Url           |
| Description         | 
| Category            | 
| Content             | 
| Alchohol Percentage | 
| Brewer              | 
| Country             |
| Serving Temperature | 
| Serving Glass       | 
| Beer Colour (Hex)   | 

## Installation
You'll need Python 3.7 for this tool to work, because it makes use of the new @dataclass functionalities.

Also you'll need lxml and requests libraries. You can install them using:

```
pip install requests
pip install lxml
```

## Notes
Please do not spam this tool. It is optimized with async requests and therefore will send a large amount of request in a short period of time.

Also note that this tool is based on the exact structure of the html pages. Therefore it is most likely that this tool will break in the future.
