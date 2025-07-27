from bs4 import BeautifulSoup
import asyncio
import requests
import csv


headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}



async def request_for_id(id: str, car_manufacturer: str):
    url = f"https://m.mobile.de/consumer/api/search/reference-data/models/{id}"
    response = await asyncio.to_thread(requests.get, url, headers=headers)
    if response.status_code == 200:
        return {car_manufacturer: response.json()}
    return None


async def gather_and_request(id_list: list):
    tasks = [request_for_id(id.attrs["value"], id.contents[0]) for id in id_list]
    return await asyncio.gather(*tasks)


def filter_car_names(el):
    if "label" in el.keys():
        return el["label"]
    add_car_models_to_csv(car_models=el["items"])


def add_car_models_to_csv(
    car_manufacturer: str = None,
    car_models: list = [],
    filename="cars.csv"
):
    if car_manufacturer:
        setattr(add_car_models_to_csv, "car_manufacturer", car_manufacturer)

    car_models = list(map(filter_car_names, car_models))
    stuff = ["(alle)", "(Alle)", "Andere"]

    def remove_stuff(el: str):
        for m in stuff:
            el = el.replace(m, "")
        return el.strip()

    car_models = list(filter(lambda el: not (el is None), car_models))
    car_models = list(map(remove_stuff, car_models))
    car_models = list(filter(lambda el: len(el) > 0, car_models))
    car_models = list(set(car_models))

    with open(filename, mode="a", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            for car_model in car_models:
                writer.writerow([add_car_models_to_csv.car_manufacturer, car_model])


def prepare_csv(filename="cars.csv"):
    with open(filename, mode="a", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(["Manufacturer", "Model"])


def read_page_from_file():
    # page from "https://mobile.de/?lang=en"
    with open('src/db/mobile_de_page.html', mode='r', encoding="utf-8") as file:
        text = file.read()
    return text


if __name__ == "__main__":
    mobile_de_page = read_page_from_file()
    mobile_de_bs = BeautifulSoup(mobile_de_page, "html.parser")
    select_widget = mobile_de_bs.find("div", class_="W885w")
    if select_widget:
        car_manufacturer_list = select_widget.find(
            "optgroup", {"label": "All makes"}
        )
        cars = asyncio.run(gather_and_request(car_manufacturer_list.contents))
        # save results in the .csv
        for el in cars:
            if not el:
                continue
            car_manufacturer = list(el.keys())[0]
            car_models = el[car_manufacturer]["data"]
            add_car_models_to_csv(car_manufacturer, car_models)
