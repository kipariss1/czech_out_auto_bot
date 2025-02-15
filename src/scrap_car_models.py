from src import sqlite_db_handler
from src.models.models import CarModel
import requests
from bs4 import BeautifulSoup

# TODO: do this assyncronous
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}
mobile_de_page = requests.get("https://mobile.de/?lang=en", headers=headers)
if mobile_de_page.status_code == 200:
    mobile_de_bs = BeautifulSoup(mobile_de_page.text, "html.parser")

    select_widget = mobile_de_bs.find("div", class_="W885w")
    pass
