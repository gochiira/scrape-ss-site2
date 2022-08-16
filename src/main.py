from logging import getLogger, Logger
from dataclasses import dataclass
from dataclasses_json import dataclass_json
from typing import List, Any, Optional
from httpx import AsyncClient
from asyncio import Semaphore
import logging
import lxml.html
import httpx
import feedparser
import asyncio
import random
import re

logging.basicConfig(level=logging.DEBUG)


@dataclass
class FeedEntryAuthorResponse():
    name: str


@dataclass
class FeedEntryTagResponse():
    term: str
    scheme: str
    label: None


@dataclass_json
@dataclass
class FeedEntryResponse():
    authors: List[FeedEntryAuthorResponse]
    author_detail: FeedEntryAuthorResponse
    author: str
    title: str
    title_detail: dict
    links: List[dict]
    link: str
    id: str
    guidislink: bool
    updated: str
    updated_parsed: List[int]
    published: str
    published_parsed: List[int]
    tags: List[FeedEntryTagResponse]
    summary: str
    summary_detail: dict
    content: List[dict]
    thr_total: str


@dataclass_json
@dataclass
class FeedResponse():
    bozo: bool
    entries: List[FeedEntryResponse]
    feed: dict
    headers: dict
    href: str
    status: int
    version: str
    encoding: str
    namespaces: dict
    updated: Optional[str] = None
    updated_parsed: Optional[List[int]] = None


@dataclass_json
@dataclass
class SS():
    title: str
    sentences: List[str]


class GochiusaSSS():
    logger: Logger
    endpoint: str

    def __init__(
        self,
        endpoint: str = "https://gochiusa-ss.com/category/gochiusa/feed/atom/"
    ) -> None:
        self.logger = getLogger(__name__)
        self.endpoint = endpoint

    def get_feeds(self, page: int) -> FeedResponse:
        self.logger.debug(f"Getting feeds {page}")
        ret: Any = feedparser.parse(self.endpoint + f"?paged={page}")
        feeds = FeedResponse(**ret)
        self.logger.debug(f"Getting feeds {page} success")
        return feeds

    async def parse_page(
        self, semaphore: Semaphore, client: AsyncClient, url: str
    ) -> SS:
        async with semaphore:
            await asyncio.sleep(random.randint(3, 5))
            self.logger.debug(f"Getting {url}")
            resp = await client.get(url)
            html = lxml.html.fromstring(resp.text)
            title = html.xpath('//h1[@class="entry-title"]/text()')[0]
            title = re.sub(r'[\\|/|:|?|.|"|<|>|\|]', '-', title)
            body: List[str] = html.xpath(
                '//div[@class="entry-content cf"]/p/text()')
            body = [b for b in body if b != "\xa0"]
            self.logger.debug(f"Getting {url} success")
            return SS(title, body)

    async def run(self) -> List[SS]:
        page = 1
        sem = asyncio.Semaphore(5)
        feeds = self.get_feeds(page)
        ret: List[SS] = []
        while feeds.status != 404:
            self.logger.debug(f"Processing page {page}")
            async with httpx.AsyncClient() as client:
                tasks = [
                    self.parse_page(sem, client, e.link)
                    for e in feeds.entries
                ]
                resp = await asyncio.gather(*tasks, return_exceptions=False)
                ret.extend(resp)
                page += 1
                feeds = self.get_feeds(page)
            self.logger.debug(f"Page {page} done")
            await asyncio.sleep(random.randint(3, 8))
        return ret


async def main() -> None:
    cl = GochiusaSSS()
    ss_objects = await cl.run()
    for ss in ss_objects:
        cl.logger.debug(f"Writing {ss.title}.txt")
        with open(f"out/{ss.title}.txt", "w", encoding="utf-8") as f:
            for s in ss.sentences:
                f.write(s + "\n")
        cl.logger.debug(f"Written {ss.title}.txt")

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
