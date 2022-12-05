import os
import traceback
from contextlib import suppress
from datetime import datetime, time as dtime
from functools import partial
from typing import List

from missing_cars import get_missing_cars_map
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.common import exceptions
from termcolor import cprint
from utils import init_and_log_in, do_click, RangeType, printProgressBar, TimeRangeType, log
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.action_chains import ActionChains
import time
from enum import Enum
import json
import copy
import sys
import click
import logging


class MissionStatus(str, Enum):
    NEW = "red"
    IN_PROGRESS = "yellow"
    FINISHING = "green"


COLORS = {
    "mission_panel_red": MissionStatus.NEW,
    "mission_panel_yellow": MissionStatus.IN_PROGRESS,
    "mission_panel_green": MissionStatus.FINISHING,
}


class OnlyVehicles(str, Enum):
    MEDIC = "medic"
    GBA = "gba"
    ALL = "all"
    MISSION = "mission"
    MISSING = "missing"


class TakingPart(str, Enum):
    RESEND = "resend"
    DONT_SEND = "dont_send"
    IGNORE = "ignore"


class TakingPartStatus(str, Enum):
    YES = "yes"
    NO = "no"


VEHICLES_MAP = {
    "GBA": os.getenv("GBA", "aao_1666464"),
    "GCBART": "aao_1666797",
    "SLOP": "aao_1666528",
    "POWODZ": "aao_1666788",
    "SH": "aao_1666526",
    "OPI": "aao_1666465",
    "SCCN": "aao_1666530",
    "PR": "aao_1666838",
    "WRD": "aao_1806682",
    "SW": "aao_1666821",
    "AMBULANS": "aao_1666958",
    "AMBULANSx10": "aao_1666959",
    "LPRx10": "aao_1776594",
    "APRD": "aao_1806681",
    "RCHEM": "aao_1666527",
    "SCDZ": "aao_1666579",
    "SRWYS": "aao_1666628",
    "SPGAZ": "aao_1666467",
    "DIL": "aao_1666529",
    "LPR": "aao_1666525",
    "HELIP": "aao_1666468",
    "K9": "aao_1666552",
    "SPKP": "aao_1666469",
}


def load_missions_data():
    with open("missions.json", "r") as f:
        return json.loads(f.read())


def get_actual_status(driver):
    try:
        img = driver.find_element(By.XPATH, '//*[@id="mission_general_info"]/div/img')
        img_src = img.get_attribute("src")
        if "yellow_images" in img_src:
            return MissionStatus.IN_PROGRESS
        if "red_images" in img_src:
            return MissionStatus.NEW
        if "green_images" in img_src:
            return MissionStatus.FINISHING
    except Exception as err:
        log(err)
        return MissionStatus.NEW


def get_missing_cars(driver):
    element = driver.find_element(By.CLASS_NAME, 'alert-missing-vehicles')
    return get_missing_cars_map(element.text.strip())


def get_missing_lpr(driver) -> int:
    elements = driver.find_elements(By.CLASS_NAME, 'alert-danger')
    count = 0
    for element in elements:
        if 'Śmigłowiec LPR' in element.text.strip():
            count += 1
    return count


def get_mission_base_data(mission):
    mission_status_attributes = mission.find_element(By.CLASS_NAME, "panel-default").get_attribute(
        "class"
    )
    mission_status = next(
        (
            COLORS[class_name]
            for class_name in mission_status_attributes.split(" ")
            if COLORS.get(class_name)
        ),
        MissionStatus.NEW,
    )

    mission_header = mission.find_element(By.CLASS_NAME, "panel-heading")
    mission_title = (
        mission_header.find_element(By.CLASS_NAME, "map_position_mover")
        .get_attribute("innerHTML")
        .strip()
    )
    alliance_mission = "[Sojusz]" in str(mission_title)
    event_mission = "[Wydarzenie]" in str(mission_title)
    own_mission = alliance_mission is False and event_mission is False
    shared_mission = "panel-success" in mission_status_attributes
    taking_part_icon_class = mission_header.find_element(
        By.CLASS_NAME, "glyphicon-user"
    ).get_attribute("class")
    taking_part = (
        TakingPartStatus.YES if "hidden" not in taking_part_icon_class else TakingPartStatus.NO
    )
    missing_stuff_alerts = mission.find_elements(By.CLASS_NAME, "alert-danger")
    missing_stuff_parsed = [a.text.strip() for a in missing_stuff_alerts]
    mission_missing_stuff = len(missing_stuff_alerts) > 0

    alarm, name = mission.find_elements(By.TAG_NAME, "a")
    mission_href = alarm.get_attribute("href")
    mission_name = name.get_attribute("innerHTML").split(",")[0]
    mission_name = mission_name.replace("[Sojusz]", "").replace("[Wydarzenie]", "").strip()
    mission_name = mission_name.replace(" (ALARM NIEPOTWIERDZONY)", "")
    mission_id = mission.get_attribute("mission_id")

    missing_cars = mission.find_element(By.ID, f"mission_missing_{mission_id}")

    return {
        "name": mission_name,
        "status": mission_status,
        "mission_id": mission_id,
        "href": mission_href,
        "own_mission": own_mission,
        "alliance_mission": alliance_mission,
        "taking_part": taking_part,
        "shared_mission": shared_mission,
        "missing_stuff": mission_missing_stuff,
        "event_mission": event_mission,
        "missing_stuff_data": missing_stuff_parsed,
        "missing_cars": missing_cars.text.strip(),
    }


def get_missions_list(
        driver, mission_requirements, include_own_mission, include_alliance_mission, include_event,
):
    driver.get("https://www.operatorratunkowy.pl/")
    time.sleep(2)
    driver.save_screenshot(f"load3.png")

    mission_list = []
    if include_own_mission:
        mission_list += _get_missions_elements(driver, "mission_list")

    if include_alliance_mission:
        mission_list += _get_missions_elements(driver, "mission_list_alliance")

    if include_event:
        mission_list += _get_missions_elements(driver, "mission_list_alliance_event")

    parsed_missions = []

    l = len(mission_list)
    _missing_missions = []
    printProgressBar(0, l, prefix="Parsing missions:", suffix="Complete", length=50)
    for i, mission in enumerate(mission_list):
        mission_parsed_data = get_mission_base_data(mission)
        mission_requirements_data = mission_requirements.get(mission_parsed_data["name"], {})
        mission_parsed_data["requirements"] = mission_requirements_data.get("cars", {})
        mission_parsed_data["info"] = mission_requirements_data.get("info", {})
        if mission_parsed_data['missing_stuff']:
            _missing_missions.append(mission_parsed_data)
        parsed_missions.append(mission_parsed_data)
        printProgressBar(i + 1, l, prefix="Parsing missions:", suffix="Complete", length=50)

    with open('missing_mission_data.json', 'w+', encoding='utf-8') as f:
        f.write(json.dumps(_missing_missions))

    return parsed_missions


def _get_missions_elements(driver, missions_id) -> List:
    with suppress(exceptions.NoSuchElementException):
        return driver.find_element(By.ID, missions_id).find_elements(
            By.CLASS_NAME, "missionSideBarEntry"
        )
    return []


def can_proceed_mission(
    mission,
    include_alliance_mission,
    include_own_mission,
    taking_part_in_mission,
    only_new_missions,
    credits_range,
    only_shared_missions,
    only_not_shared_missions,
    include_event,
):
    conditions = []
    conditions_matrix = []
    if not include_own_mission:
        conditions.append(mission["own_mission"] is False)
        conditions_matrix.append(f"own_mission is False")
    if not include_alliance_mission:
        conditions.append(mission["alliance_mission"] is False)
    if taking_part_in_mission == TakingPart.RESEND:
        conditions.append(mission["taking_part"] is TakingPartStatus.YES)
    elif taking_part_in_mission == TakingPart.DONT_SEND:
        conditions.append(mission["taking_part"] is TakingPartStatus.NO)
    if only_new_missions:
        conditions.append(mission["status"] is MissionStatus.NEW)
    else:
        conditions.append(mission["status"] is not MissionStatus.FINISHING)

    if only_shared_missions:
        conditions.append(mission["shared_mission"] is True)
    elif only_not_shared_missions:
        conditions.append(mission["shared_mission"] is False)

    if not include_event:
        conditions.append(mission["event_mission"] is False)

    if len(mission["info"].keys()) != 0:
        conditions.append(mission["info"]["avg_credits"] >= credits_range[0])
        conditions.append(mission["info"]["avg_credits"] < credits_range[1])
    return all(conditions)


def get_condition():
    pass


def filter_missions(
    missions_list,
    include_alliance_mission,
    include_own_mission,
    taking_part_in_mission,
    only_new_missions,
    credits_range,
    only_shared_missions,
    only_not_shared_missions,
    include_event,
):
    can_proceed_mission_partial = partial(
        can_proceed_mission,
        include_alliance_mission=include_alliance_mission,
        include_own_mission=include_own_mission,
        taking_part_in_mission=taking_part_in_mission,
        only_new_missions=only_new_missions,
        credits_range=credits_range,
        only_shared_missions=only_shared_missions,
        only_not_shared_missions=only_not_shared_missions,
        include_event=include_event,
    )
    new_missions = []
    for mission in missions_list:
        can_proceed = can_proceed_mission_partial(mission)
        if not can_proceed:
            log(f'SKIPPING {mission["name"]} {mission}')
            continue
        new_missions.append(mission)
    return new_missions


def get_patients(driver) -> int:
    try:
        small_info = driver.find_element(
            By.XPATH, '//*[@id="mission_general_info"]/small/img'
        ).parent.find_element(By.TAG_NAME, "small")
        return int(small_info.text.split("|")[1].strip())
    except Exception:
        return 0


def _click_vehicles(driver, mission_requirements):
    try:
        for vehicle, count in mission_requirements.items():
            count = int(count)
            vehicle_id = VEHICLES_MAP[vehicle]
            if vehicle_id:
                vehicle_element = driver.find_element(By.ID, VEHICLES_MAP[vehicle])
                for _ in range(0, count):
                    do_click(driver, vehicle_element)
                    time.sleep(0.3)
    except Exception as err:
        log(f"Missing car {err}", 'red')
        return False
    return True


def _adjust_gba(mission_requirements):
    gba_count = mission_requirements.get("GBA", 0)
    gcbart_count = mission_requirements.get("GCBART", 0)
    return max(0, gba_count - gcbart_count) + 1


def _get_medic_count(patients_number, lpr_needed):
    if patients_number <= 0:
        return {}

    half_patients = patients_number // 2 + 2
    return {
        "AMBULANS": patients_number % 10,
        "AMBULANSx10": patients_number // 10,
        "LPR": half_patients % 10 if lpr_needed else 0,
        "LPRx10": half_patients // 10 if lpr_needed else 0,
    }


def _adjust_required_vehicles(
        mission_info, vehicles, patients_number, mission_requirements, missing_cars,
        missing_lpr,
):
    new_requirements = {}
    if OnlyVehicles.MISSION in vehicles:
        new_requirements = mission_requirements
        new_requirements["GBA"] = _adjust_gba(mission_requirements)
    if OnlyVehicles.GBA in vehicles:
        new_requirements["GBA"] = 1
    if OnlyVehicles.MEDIC in vehicles and patients_number > 0:
        new_requirements = {
            **new_requirements,
            **_get_medic_count(patients_number, mission_info.get("LPR", False)),
        }
        if missing_lpr and new_requirements.get('LPR', 0) < missing_lpr:
            new_requirements['LPR'] = missing_lpr
    if OnlyVehicles.MISSING in vehicles:
        missing_cars_map = missing_cars()
        new_requirements = {
            **missing_cars_map,
            **new_requirements,
        }
    if OnlyVehicles.ALL in vehicles:
        return {
            **mission_requirements,
            **_get_medic_count(patients_number, mission_info.get("LPR", False)),
            "GBA": _adjust_gba(mission_requirements),
        }
    return new_requirements


def dispatch_vehicles(driver, mission_data, vehicles, only_new_missions, dry_run, share_missions):
    try:
        driver.get(mission_data["href"])
        time.sleep(2)
        actual_status = get_actual_status(driver)
        if actual_status != MissionStatus.NEW and only_new_missions:
            log(f"SKIPPING actual status changed {actual_status} {mission_data}")

        missing_cars = partial(get_missing_cars, driver)
        patients_number = get_patients(driver)
        missing_lpr = get_missing_lpr(driver)

        # load more vehicles - orange label
        try:
            element = driver.find_element(By.CLASS_NAME, "missing_vehicles_load")
            driver.execute_script("arguments[0].click();", element)
            time.sleep(2)
        except exceptions.NoSuchElementException:
            pass

        mission_requirements = copy.copy(mission_data["requirements"])
        mission_requirements = _adjust_required_vehicles(
            mission_data["info"], vehicles, patients_number,
            mission_requirements,
            missing_cars,
            missing_lpr,
        )

        mark_vehicles = _click_vehicles(driver, mission_requirements)
        if not mark_vehicles:
            log(f"Some errors {mission_data}", "red")
            return False

        # submit mission and send vehicles
        if not dry_run:
            do_click(driver, driver.find_element(By.ID, "mission_alarm_btn"))
            time.sleep(2)
            try:
                log(driver.find_element(By.CLASS_NAME, 'alert-success').text.replace('×', '').strip(), 'green')
            except exceptions.NoSuchElementException:
                log('No vehicles sent', 'yellow')
                with suppress(exceptions.NoSuchElementException):
                    log(driver.find_element(By.CLASS_NAME, 'alert-danger').text.replace('×', '').strip(), 'red')
            if share_missions:
                do_click(driver, driver.find_element(By.ID, "mission_alliance_share_btn"))
                time.sleep(1)

    except exceptions.UnexpectedAlertPresentException as err:
        log(f"No vehicle {mission_data}, {err}")
    except exceptions.ElementClickInterceptedException as err:
        log(f"No vehicle {mission_data}, {err}")
    except exceptions.NoSuchElementException as err:
        log(f"Mission ended? {mission_data}, {err}")
    else:
        mission_str = f'{mission_data["name"]} {mission_data["status"].name} {mission_data["href"]}'
        log(f'SUCCESS {mission_str} patients: {patients_number} {mission_requirements}', 'green')


@click.command()
@click.option(
    "--send",
    "send_vehicles",
    multiple=True,
    type=click.Choice(OnlyVehicles),
    help="Select what vehicles will be send.",
    default=[],
)
@click.option("--alliance", "include_alliance_mission", type=click.BOOL, default=False, help="")
@click.option("--own", "include_own_mission", type=click.BOOL, default=True, help="")
@click.option("--event", "include_event", type=click.BOOL, default=False, help="")
@click.option(
    "--taking-part",
    "taking_part_in_mission",
    type=click.Choice(TakingPart),
    default=TakingPart.IGNORE,
    help="Will send vehicles to the missions that you're not participating",
)
@click.option(
    "--only-new-missions",
    "only_new_missions",
    type=click.BOOL,
    default=True,
    help="Will proceed with only RED missions",
)
@click.option(
    "--shared-missions",
    "only_shared_missions",
    is_flag=True,
    default=False,
)
@click.option(
    "--not-shared-missions",
    "only_not_shared_missions",
    is_flag=True,
    default=False,
)
@click.option("--credits-range", "credits_range", type=RangeType(), default="0-20k")
@click.option("--headless", "headless", default=True, type=click.BOOL)
@click.option("--reverse", "reverse_order", is_flag=True, default=False)
@click.option("--dry-run", "dry_run", is_flag=True, default=False)
@click.option("--sleep", "sleep", type=click.INT, default=None)
@click.option("--sleep-between", "sleep_between", type=TimeRangeType(), default="")
@click.option("--exit-at-end", "exit_at_end", is_flag=True, default=False)
@click.option("--just-once", "just_once", is_flag=True, default=False)
@click.option("--share-missions", "share_missions", is_flag=True, default=False)
def runner(
    send_vehicles,
    include_alliance_mission,
    include_own_mission,
    include_event,
    taking_part_in_mission,
    only_new_missions,
    only_shared_missions,
    only_not_shared_missions,
    credits_range,
    headless,
    reverse_order,
    dry_run,
    sleep,
    sleep_between,
    exit_at_end,
    just_once,
    share_missions,
):
    driver = init_and_log_in(headless)
    i = 0
    while True:
        try:
            driver.save_screenshot(f"load.png")
            mission_requirements = load_missions_data()
            missions_list = get_missions_list(driver, mission_requirements, include_own_mission, include_alliance_mission, include_event)
            filtered_missions = filter_missions(
                missions_list,
                include_alliance_mission,
                include_own_mission,
                taking_part_in_mission,
                only_new_missions,
                credits_range,
                only_shared_missions,
                only_not_shared_missions,
                include_event,
            )

            if reverse_order:
                filtered_missions.reverse()

            if exit_at_end and len(filtered_missions) <= 0:
                driver.quit()
                return

            for mission in filtered_missions:
                dispatch_vehicles(driver, mission, send_vehicles, only_new_missions, dry_run, share_missions)
        except Exception as err:
            log(f"Unexpected error {err}", 'red')
            log(traceback.format_exc(), 'red')
            driver.save_screenshot(f"error.png")
            log(traceback.format_exc(), 'red')
        if sleep:
            log(f"Sleeping {round(sleep/60)} from {datetime.now()}", 'yellow')
            driver.quit()
            time.sleep(sleep)
            driver = init_and_log_in(headless)

        now_hour = datetime.now().hour
        if sleep_between[0] and sleep_between[0] <= now_hour < sleep_between[1]:
            log(f"Sleeping between {sleep_between} from {datetime.now()}", 'yellow')
            driver.quit()
            time.sleep((datetime.combine(datetime.now(), dtime(sleep_between[1])) - datetime.now()).seconds)
            driver = init_and_log_in(headless)

        if just_once:
            driver.quit()
            return

        i += 1

        if i == 50:
            driver.quit()
            time.sleep(5)
            driver = init_and_log_in(headless)


if __name__ == "__main__":
    runner()
