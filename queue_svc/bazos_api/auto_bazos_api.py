import requests
from typing import TypedDict
import aiohttp
from bs4 import BeautifulSoup as bs
import re


def get(link):
    response = requests.get(link)
    text = response.text
    if response.status_code != 200:
        raise AssertionError(f"[{response.status_code}] Get request to {link} was not successful, reason: \n{text}")
    return text


async def aget(link):
    async with aiohttp.ClientSession() as session:
        async with session.get(link) as response:
            text = await response.text()
            if response.status != 200:
                raise AssertionError(f"[{response.status}] Async Get request to {link} was not successful, reason: \n{text}")
            return text

class AutoAdvertisementPage:

    id: str
    name: str
    
    def __init__(self, link: str):
        self.psc: str
        self.parsed: bs
        self.link = link
        self.text: str = None
        self.price: str = None
        self._is_deleted: bool | None = None
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
        topped_signs = self.parsed.find_all("span", class_="ztop")
        if len(topped_signs) > 0 and topped_signs[0].text == 'TOP':
            return True
        return False

    async def is_deleted(self) -> bool:
        if self._is_deleted is None:
            await self.get_page_text()
            breadcrumb = self.parsed.find("div", class_="drobky")
            add_title = breadcrumb.find("b")
            if not add_title:
                self._is_deleted = True
            else:
                self._is_deleted = False
        return self._is_deleted
    
    def _find_price(self) -> int:
        left_table = self.parsed.find("td", class_="listadvlevo")
        price_text = left_table.contents[1].contents[9].text
        price = re.sub(r"\D", "", price_text)
        return int(price)

    async def get_page_text(self):
        html = await aget(self.link)
        self.parsed = bs(html, "html.parser")
        title = self.parsed.find("h1", class_="nadpisdetail")
        if title:
            title = title.text
            details = self.parsed.find("div", class_="popisdetail").text
            self.psc = self.parsed.find("a", {"title": "Přibližná lokalita"}).text
            self.price = self._find_price() 
            self.text = f"{title}\n\n{details}"
            self._is_deleted = False
        else:
            self._is_deleted = True


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
        return get(self.url)

    def _construct_link(self, page=0):
        model = self.model.replace(" ", "+")
        locality = self.locality if self.locality is not None else ""
        range = self.range if self.range is not None else 25
        if page == 0:
            url = f'{self.base_url}/?hledat={model}&' \
                + f"rubriky=auto&hlokalita={locality}&humkreis={range}&" \
                + f"cenaod={self.price_from}&cenado={self.price_to}&Submit=Hledat&order=&crp=&kitx=ano"
        else:
            url = f"{self.base_url}/{page*20}/?hledat={model}&hlokalita={locality}&" \
                  + f"humkreis={range}&cenaod={self.price_from}&cenado={self.price_to}&order="
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
