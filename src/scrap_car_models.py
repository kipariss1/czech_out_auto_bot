from src import sqlite_db_handler
from src.models.models import CarModel
import requests
from bs4 import BeautifulSoup

# TODO: do this assincronous
mobile_de_page = requests.get("https://mobile.de/?lang=en")
if mobile_de_page.status_code == 200:
    mobile_de_bs = BeautifulSoup(mobile_de_page.text, "html.parser")

    select_widget = mobile_de_bs.find("div", class_="W885w")
    pass
