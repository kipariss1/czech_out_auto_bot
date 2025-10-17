import requests
from typing import TypedDict


class AutoPageSearchArgs(TypedDict):
    model: str
    locality: str
    range: str
    price_from: str
    price_to: str


class AutoAdvertisementPage:
    pass


class AutoPage:

    def __init__(self, **kwargs: AutoPageSearchArgs):
        for key, value in kwargs.items():
            setattr(self, key, value)
        self.url = f"https://auto.bazos.cz/?hledat={self.model.replace(' ', '+')}&" 
        + f"rubriky=auto&hlokalita={self.locality}&humkreis={self.range}&" 
        + f"cenaod={self.price_from}&cenado={self.price_to}&Submit=Hledat&order=&crp=&kitx=ano"
        self.page = requests.get(self.url)

    def get_advertisements(self):
        # TODO: implement parsing for links to advertisements
        pass