import asyncio
import aiohttp
import logging
import json


class ImageDownloader:
    def __init__(self):
        self.session = aiohttp.ClientSession()
        self.bounded_sempahore = asyncio.BoundedSemaphore(200)
        self.data_tuples = []
        self.seen_images = set()
        self.run()

    def run(self):
        self.get_urls()
        future = asyncio.Task(self._start())
        loop = asyncio.get_event_loop()
        loop.run_until_complete(future)
        loop.close()
        self.session.close()

    def get_urls(self):
        data_dict = []
        with open('output.json', 'r') as f:
            data_dict = json.load(f)

        for data in data_dict:
            self.data_tuples.append((data['image_url'], data['title']))

    async def _start(self):
        futures = []

        for data in self.data_tuples:
            if data[0] in self.seen_images:
                continue
            self.seen_images.add(data[0])
            futures.append(self._get_image(data))

        for future in asyncio.as_completed(futures):
            try:
                done = await future
            except Exception as e:
                logging.error(
                    f'Exception caught : {e}')

    async def _get_image(self, data_tuple):
        image = await self._http_get(data_tuple[0])
        # Very dirty, much ow
        filename = data_tuple[1].lower().replace(" ", "-").replace("/", "-").replace(
            ".", "-").replace("!", "-").replace("?", "-").replace("*", "-").replace(":", "-")
        with open(filename + '.png', 'wb+') as fr:
            fr.write(image)
        return True

    async def _http_get(self, url):
        """ Async get request helper function"""
        async with self.bounded_sempahore:
            try:
                async with self.session.get(url, timeout=30) as response:
                    content = await response.read()
                    return content
            except Exception as e:
                logging.error(f'Exception caught trying to get {url}: {e}')


if __name__ == "__main__":
    imageDownloader = ImageDownloader()
