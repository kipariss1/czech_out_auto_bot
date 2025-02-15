from src import sqlite_db_handler
from src.models.models import CarModel
import requests
from bs4 import BeautifulSoup
import asyncio


async def request_for_id(id: str, car_manufacturer: str):
    url = f"https://m.mobile.de/consumer/api/search/reference-data/models/{id}"
    response = await asyncio.to_thread(requests.get, url, headers=headers)
    if response.status_code == 200:
        return {car_manufacturer: response.json()}
    return None


async def gather_and_request(id_list: list):
    tasks = [request_for_id(id.attrs["value"], id.contents[0]) for id in id_list]
    return await asyncio.gather(*tasks)


headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}


if __name__ == "__main__":
    mobile_de_page = requests.get("https://mobile.de/?lang=en", headers=headers)
    if mobile_de_page.status_code == 200:
        mobile_de_bs = BeautifulSoup(mobile_de_page.text, "html.parser")

        select_widget = mobile_de_bs.find("div", class_="W885w")
        if select_widget:
            car_manufacturer_list = select_widget.find(
                "optgroup", {"label": "All makes"}
            )
            car_models = asyncio.run(gather_and_request(car_manufacturer_list.contents))
            # TODO: save results in the database
            pass
