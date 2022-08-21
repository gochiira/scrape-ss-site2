from logging import getLogger, Logger
from dataclasses import dataclass
from dataclasses_json import dataclass_json
from typing import Dict, List, Optional
from httpx import AsyncClient
from asyncio import Semaphore
import logging
import lxml.html
import httpx
import asyncio
import random
import re

logging.basicConfig(level=logging.DEBUG)


@dataclass_json
@dataclass
class FeedResponse():
    urls: List[str]
    current_page: int
    total_pages: int = -1


@dataclass_json
@dataclass
class SS():
    title: str
    sentences: List[str]


class MorikinokoSSS():
    logger: Logger
    endpoint: str

    def __init__(
        self,
        endpoint: str = "http://morikinoko.com/archives/cat_50053820.html"
    ) -> None:
        self.logger = getLogger(__name__)
        self.endpoint = endpoint

    async def get_feeds(self, page: int) -> FeedResponse:
        self.logger.debug(f"Getting feeds {page}")
        async with httpx.AsyncClient() as client:
            params: Optional[Dict] = None
            if page != 1:
                params = {"p": page}
            resp = await client.get(
                self.endpoint,
                params=params
            )
        html = lxml.html.fromstring(resp.text)  # type: ignore
        total_pages_objects: List[str] = html.xpath(
            '//li[@class="paging-last"]/a/@href')  # type: ignore
        total_pages = -1
        if len(total_pages_objects) > 0:
            total_pages = int(total_pages_objects[0].split("?p=")[1])
        urls: List[str] = html.xpath(
            '//h1[@class="card-title mr-2 article-list-title"]/a/@href')  # type: ignore
        feed = FeedResponse(urls, page, total_pages)
        self.logger.debug(f"Getting feeds {page} success")
        return feed

    async def parse_page(
        self, semaphore: Semaphore, client: AsyncClient, url: str
    ) -> SS:
        async with semaphore:
            await asyncio.sleep(random.randint(3, 5))
            self.logger.debug(f"Getting {url}")
            resp = await client.get(url)
            html = lxml.html.fromstring(resp.text)
            title: str = html.xpath(
                '//h1[@class="card-title article-title mt-4"]/a/text()'
            )[0].strip()
            title = re.sub(r'[\\|/|:|?|.|"|<|>|\|]', '-', title)
            sentences_objects: List[str] = html.xpath(
                '//div[@class="mtex mtex-link"]/text()'
            )
            sentences = [obj for obj in sentences_objects if obj != "\n"]
            self.logger.debug(f"Getting {url} success")
            return SS(title, sentences)

    async def run(self) -> List[SS]:
        page = 1
        sem = asyncio.Semaphore(5)
        feeds = await self.get_feeds(page)
        ret: List[SS] = []
        while feeds.total_pages != -1:
            self.logger.debug(f"Processing page {page}")
            async with httpx.AsyncClient() as client:
                tasks = [
                    self.parse_page(sem, client, url)
                    for url in feeds.urls
                ]
                resp = await asyncio.gather(*tasks, return_exceptions=False)
                ret.extend(resp)
                page += 1
                feeds = await self.get_feeds(page)
            self.logger.debug(f"Page {page} done")
            await asyncio.sleep(random.randint(3, 8))
        return ret


async def main(dryRun: bool = True) -> None:
    cl = MorikinokoSSS()
    ss_objects = await cl.run()
    if dryRun:
        return
    for ss in ss_objects:
        cl.logger.debug(f"Writing {ss.title}.txt")
        with open(f"out/{ss.title}.txt", "w", encoding="utf-8") as f:
            for s in ss.sentences:
                f.write(s + "\n")
        cl.logger.debug(f"Written {ss.title}.txt")

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(dryRun=False))
