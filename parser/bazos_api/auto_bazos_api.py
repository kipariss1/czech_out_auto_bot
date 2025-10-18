import requests
from typing import TypedDict
import aiohttp
from bs4 import BeautifulSoup as bs
import re


class AutoPageSearchArgs(TypedDict):
    model: str
    locality: str
    range: str
    price_from: str
    price_to: str


class AutoAdvertisementPage:

    id: str
    name: str
    
    def __init__(self, link: str):
        self.link = link
        self.text: str
        for key, value in self._get_attrs_from_link().items():
            setattr(self, key, value)

    def _get_attrs_from_link(self) -> dict[str, str]:
        pattern = r'href="/inzerat/(\d+)/([^.]+)\.php"'
        match = re.search(pattern, self.link)
        if match:
            return {'id': match.group(1), 'name': match.group(2)}

    async def get_page_text(self):
        async with aiohttp.ClientSession() as session:
            async with session.get() as response:
                html = await response.text()
                parsed = bs(html, "html.parser")
                details = parsed.find("div", class_="popisdetail")
                # TODO: add here parsing of the PSC of the ad
                self.text = details.text




class AutoPage:

    def __init__(self, **kwargs: AutoPageSearchArgs):
        self.page = 0
        for key, value in kwargs.items():
            setattr(self, key, value)
        self.html = self._get_html()

    def _get_html(self):
        self.url = self._construct_link(self.page)
        return requests.get(self.url)

    def _construct_link(self, page=0):
        url = f'https://auto.bazos.cz/{f"{page*20}/" if page else ""}?hledat={self.model.replace(" ", "+")}&' 
        + f"rubriky=auto&hlokalita={self.locality}&humkreis={self.range}&" 
        + f"cenaod={self.price_from}&cenado={self.price_to}&Submit=Hledat&order=&crp=&kitx=ano"
        return url

    def get_advertisements(self) -> list[str]:
        parsed = bs(self.html, "html.parser")
        advertisements = parsed.find("div", class_="inzeratynadpis")
        return map(lambda ad: ad.find("a")["href"].text, advertisements)
    
    def next_page(self):
        self.page += 1
        self.html = self._get_html()
