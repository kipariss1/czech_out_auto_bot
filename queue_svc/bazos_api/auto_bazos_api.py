import requests
from typing import TypedDict
import aiohttp
from bs4 import BeautifulSoup as bs
import re
import asyncio


class AutoAdvertisementPage:

    id: str
    name: str
    
    def __init__(self, link: str):
        self.location_link: str
        self.parsed: bs
        self.link = link
        self.text: str = None
        for key, value in self._get_attrs_from_link().items():
            setattr(self, key, value)

    def _get_attrs_from_link(self) -> dict[str, str]:
        pattern = r'/inzerat/(\d+)/([^.]+)\.php'
        match = re.search(pattern, self.link)
        if match:
            return {'id': match.group(1), 'name': match.group(2)}
        
    async def is_toped(self) -> bool:
        if not self.text:
            await self.get_page_text()
        topped_sign = self.parsed.find("span", class_="ztop", string="TOP")
        if not topped_sign:
            return False
        return True
        
    async def is_deleted(self) -> bool:
        if not self.text:
            await self.get_page_text()
        breadcrumb = self.parsed.find("div", class_="drobky")
        add_title = breadcrumb.find("b")
        if not add_title:
            return True
        return False

    async def get_page_text(self):
        async with aiohttp.ClientSession() as session:
            async with session.get(self.link) as response:
                html = await response.text()
                self.parsed = bs(html, "html.parser")
                title = self.parsed.find("h1", class_="nadpisdetail").text
                details = self.parsed.find("div", class_="popisdetail").text
                self.location_link = self.parsed.find("a", {"title": "Přibližná lokalita"}).text
                # TODO: add here parsing of the PSC of the ad
                self.text = f"{title}\n\n{details}"


class AutoPageSearchArgs(TypedDict):
    model: str
    locality: str
    range: str
    price_from: int
    price_to: int


class AutoPage:

    def __init__(self, **kwargs: AutoPageSearchArgs):
        self.page = 0
        self.base_url = 'https://auto.bazos.cz'
        for key, value in kwargs.items():
            setattr(self, key, value)
        self.html = self._get_html()

    def _get_html(self):
        self.url = self._construct_link(self.page)
        response = requests.get(self.url)
        return response.text

    def _construct_link(self, page=0):
        url = f'{self.base_url}/{f"{page*20}/" if page else ""}?hledat={self.model.replace(" ", "+")}&' \
            + f"rubriky=auto&hlokalita={self.locality}&humkreis={self.range}&" \
            + f"cenaod={self.price_from}&cenado={self.price_to}&Submit=Hledat&order=&crp=&kitx=ano"
        return url

    def get_advertisements(self) -> list[str]:
        parsed = bs(self.html, "html.parser")
        advertisements = parsed.find_all("div", class_="inzeratynadpis")
        advertisements = list(filter(lambda ad: ad.find("a"), advertisements))
        return list(map(lambda ad: self.base_url + ad.find("a")["href"], advertisements))
    
    def go_next_page(self):
        self.page += 1
        self.html = self._get_html()

    def go_previous_page(self):
        if self.page == 0:
            return False
        self.page -= 1
        self.html = self._get_html()
        return True
