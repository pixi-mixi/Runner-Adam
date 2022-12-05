import dataclasses
import traceback

import click
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.common import exceptions
from selenium.webdriver.remote.webelement import WebElement
from utils import init_and_log_in, do_click, log
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.action_chains import ActionChains
import time
from enum import Enum
import json
import copy
from selenium.webdriver.chrome.options import Options


@dataclasses.dataclass
class Hospital:
    name: str
    distance: float
    fee: int
    link: WebElement
    category: str

    def __str__(self):
        return f"[{self.category.upper()}] {self.name} ({self.distance}km, {self.fee}%)"


@dataclasses.dataclass
class Prison:
    link: WebElement


def _get_li_href(li_element):
    return li_element.find_element(By.CLASS_NAME, "lightbox-open").get_attribute("href")


def get_transport_calls(driver):
    driver.get("https://www.operatorratunkowy.pl/")

    try:
        radio_list = driver.find_element(By.ID, "radio_messages_important").find_elements(
            By.TAG_NAME, "li"
        )
        return [
            _get_li_href(li_element) for li_element in radio_list if "Żądanie transportu" in li_element.text.strip()
        ]
    except Exception as err:
        log(err)
        return None


OWN_HOSPITALS = "own-hospitals"
ALLIANCE_HOSPITALS = "alliance-hospitals"


def get_transport_target(driver):
    own = _get_transport_target(driver, OWN_HOSPITALS)
    if own and own.distance <= 50:
        return own

    alliance = _get_transport_target(driver, ALLIANCE_HOSPITALS)
    if alliance:
        return alliance

    if not own and not alliance:
        return get_prisoner_target(driver)

    return None


def get_prisoner_target(driver):
    try:
        links = driver.find_element(By.CLASS_NAME, "col-md-9").find_elements(By.TAG_NAME, "a")
        return Prison(link=links[1])
    except Exception as err:
        log(err)
        return None


def _get_transport_target(driver, hospitals):
    try:
        links = (
            driver.find_element(By.ID, hospitals)
            .find_element(By.TAG_NAME, "tbody")
            .find_elements(By.TAG_NAME, "tr")
        )
        for link in links:
            cells = link.find_elements(By.TAG_NAME, "td")
            name = cells[0].text.strip()
            distance = float(cells[1].text.replace(" km", "").replace(",", "."))
            link = cells[-1].find_element(By.TAG_NAME, "a")
            fee = int(cells[3].text.replace(" %", "")) if len(cells) > 5 else 0

            if link.text == "Transportuj pacjenta":
                return Hospital(
                    name=name,
                    distance=distance,
                    fee=fee,
                    link=link,
                    category=hospitals.split('-')[0]
                )

    except Exception as err:
        log(err)

    return None


def get_next_call(driver):
    try:
        links = driver.find_elements(By.TAG_NAME, "a")
        for link in links:
            if link.text == "Przejdź do kolejnego pojazdu z żądaniem transportu":
                return link
    except Exception as err:
        log(err)
        return None


def _check_divisor(call, divisor):
    if not divisor:
        return True
    return int(call.split('/')[-1:]) % divisor == 0


@click.command()
@click.option("--divisor", "divisor", default=None, type=click.INT)
@click.option("--headless", "headless", default=True, type=click.BOOL)
def dispatcher(divisor, headless):
    driver = init_and_log_in(headless, page_load='eager')
    i = 0
    while True:
        try:
            transports = get_transport_calls(driver)

            if transports:
                for transport in transports:
                    if _check_divisor(transport, divisor):
                        driver.get(transport)
                        target = get_transport_target(driver)
                        if not target:
                            continue
                        log(target)
                        do_click(driver, target.link)
            else:
                # no calls
                time.sleep(5)
        except Exception as err:
            log(err)
            log(traceback.format_exc(), 'red')
        i += 1

        # clear memory every 50 runs
        if i == 50:
            i = 0
            driver.quit()
            time.sleep(5)
            driver = init_and_log_in(headless, page_load='eager')

