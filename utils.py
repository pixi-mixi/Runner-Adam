import configparser
import logging
import os
from typing import Any

import click
import time
import unidecode
from selenium import webdriver
from selenium.common import NoSuchElementException
# from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from termcolor import cprint
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager
from webdriver_manager.firefox import GeckoDriverManager
from selenium.webdriver.firefox.options import Options



logging.basicConfig()
logging.getLogger().setLevel(logging.INFO)


def get_path(file):
    return os.path.join(
        os.environ.get("_MEIPASS", os.path.abspath(".")),
        file,
    )


def log(msg: Any, color: str = None, err: bool = False) -> None:
    if isinstance(msg, Exception):
        cprint(str(msg), 'red')
        logging.error(msg)
        return

    if color:
        cprint(str(msg), color)
    else:
        print(str(msg))
    if err:
        logging.error(msg)
    else:
        logging.info(msg)


def get_config():
    config_path = os.getenv('CONFIG_INI', '')
    if not config_path:
        config_path = get_path('config.ini')
    config = configparser.ConfigParser()
    config.read(config_path)
    return config


def init_and_log_in(headless: bool = True, page_load: str = None, login_: str = None, password_: str = None) -> WebDriver:
    log('Starting web browser...', 'cyan')
    config = get_config()
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-gpu")
    if headless:
        chrome_options.add_argument("--headless")
    if page_load:
        chrome_options.page_load_strategy = page_load

    from selenium.webdriver.firefox.service import Service
    service = Service(executable_path='/root/.wdm/drivers/geckodriver/linux64/0.31/geckodriver')
    # webdriver_service = Service(f"/mnt/c/users/mateusz/operator/runner/chromedriver/stable/chromedriver")
    # a = ChromeDriverManager().install()
    # print('a')
    driver = webdriver.Firefox(options=chrome_options)
    driver.set_window_size(1920, 1200)
    log('Trying to sign in...', 'cyan')
    driver.get("https://www.operatorratunkowy.pl/users/sign_in")

    login = driver.find_element(By.XPATH, '//*[@id="user_email"]')
    if not login_:
        login_ = config['AUTH']['login']
    login.send_keys(login_)

    password = driver.find_element(By.XPATH, '//*[@id="user_password"]')
    if not password_:
        password_ = config['AUTH']['password']
    password.send_keys(password_)

    driver.find_element(By.XPATH, '//*[@id="new_user"]/input').submit()
    driver.save_screenshot(f"login.png")
    time.sleep(5)
    driver.save_screenshot(f"login.png")
    return driver


def do_click(driver, element):
    driver.execute_script("arguments[0].click();", element)


def normalize(element):
    return unidecode.unidecode(element.text.strip())


def get_table_rows(driver, table_id=None, class_name=None):
    try:
        if table_id:
            table = driver.find_element(By.ID, table_id)
        else:
            table = driver.find_element(By.CLASS_NAME, class_name)
        table = table.find_element(By.TAG_NAME, "tbody")
        return table.find_elements(By.TAG_NAME, "tr")
    except NoSuchElementException as err:
        return []


# Print iterations progress
def printProgressBar(
    iteration, total, prefix="", suffix="", decimals=1, length=100, fill="-", printEnd="\r"
):
    """
    Call in a loop to create terminal progress bar
    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        length      - Optional  : character length of bar (Int)
        fill        - Optional  : bar fill character (Str)
        printEnd    - Optional  : end character (e.g. "\r", "\r\n") (Str)
    """
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + "-" * (length - filledLength)
    print(f"\r{prefix} |{bar}| {percent}% {suffix}", end=printEnd)
    # Print New Line on Complete
    if iteration == total:
        print()


class RangeType(click.ParamType):
    name = "range"

    def convert(self, value, param, ctx):
        if "-" not in value:
            self.fail("Please provide valid range: 0-20k or 10-100 or different", param, ctx)
        try:
            parse_credits = lambda c: int(c.replace("k", "000"))
            min_credits, max_credits = tuple(value.split("-"))
            return parse_credits(min_credits), parse_credits(max_credits)
        except Exception:
            self.fail("Please provide valid range: 0-20k or 10-100 or different", param, ctx)


class TimeRangeType(click.ParamType):
    name = "time-range"

    def convert(self, value, param, ctx):
        print(value)
        if value and '-' in value:
            sleep_from, sleep_to = tuple(value.split('-'))
            return int(sleep_from), int(sleep_to)
        return None, None