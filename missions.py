import time
from dataclasses import dataclass
from enum import Enum
import json

# import requests
# import requests_cache
from bs4 import BeautifulSoup
from requests_cache import CachedSession

BASE_URL = 'https://www.operatorratunkowy.pl'

session = CachedSession('missions', backend='filesystem')
requests = session
# requests_cache.install_cache('missions', backend='filesystem')

with requests.cache_disabled():
    result = requests.get(f"{BASE_URL}/einsaetze")

html = BeautifulSoup(result.text, "html.parser")


class Cars(str, Enum):
    GCBART = 'Wymagane samochody ratownictwa technicznego'
    PR = 'Wymagane samochody ze zbiornikiem na piane'
    WRD = 'Wymagane radiowozy WRD'
    OPI = "Wymagane radiowozy"
    HELIP = "Potrzeba Helikopteru Policyjnego"
    ARMATKI = "Wymagane armatki wodne"
    RSD = "Wymagane Ruchome Stanowisko Dowodzenia"
    OPPPICKUP = "Wymagany specjalistyczny sprzęt OPP (Pickup)"
    APRD = "Wymagane APRD"
    K9 = "Potrzeba Jednostki K-9"
    SH = "Wymagany SH lub SD"
    SW = "Wymagane samochody wężowe"
    RCHEM = "Wymagane SP Rchem"
    AMBULANS = "Wymagane ambulanse"
    SCDZ = "Potrzebny Dźwig SP"
    SLOP = "Wymagane SLOp lub SLRr"
    DIL = "Wymagane samochody dowodzenia i łączności"
    SRWYS = 'Potrzebne Ratownictwo Wyskościowe'
    GBA = "Wymagane samochody pożarnicze"
    POWODZ = 'Wymagany sprzęt przeciwpowodziowy'
    SPGAZ = "Wymagane samochody SPGaz"
    SCCN = "Wymagane cysterny z wodą"

missions_ids_urls = [link['href'] for link in html.find_all('a', "btn-default")]
# missions_ids_urls = ['/einsaetze/392']
all_possible_requirements = set()
requirements = dict()
missions_requirements = dict()

for mission_id_url in missions_ids_urls:
    result = requests.get(f"{BASE_URL}{mission_id_url}")

    if "(810) Please try again in a minute" in result.text:
        print(result.text)
        time.sleep(15)
        result = requests.get(f"{BASE_URL}{mission_id_url}")

    html = BeautifulSoup(result.text, "html.parser")
    try:
        mission_type = html.find("td", text="Budynek generujący").find_next_sibling("td")
    except Exception:
        print(html)
        raise

    mission_name = html.find('h1').text.strip()

    if "Jednostka Ratowniczo-Gaśnicza" not in mission_type.text.strip():
        continue

    mission_requirements = {}
    mission_requirements2 = {}
    additional_info = {
        'LPR': False, 'LPR_chances': 0, 'max_patients': 0,
        'SM_replace': 0,
    }

    general_info = html.find('th', text="Nagroda i wymagania wstępne").find_parent('table')
    for tr in general_info.find_all("tr"):
        _, title, _, count, _ = tuple(tr.children)
        if "Średnie kredyty" in str(title).strip():
            avg_credits = int(count.text.strip())
            additional_info['avg_credits'] = avg_credits
            break

    other_informations = html.find('th', text="Inne informacje").find_parent("table")
    for tr in other_informations.find_all("tr"):
        _, title, _, count, _ = tuple(tr.children)
        title_f = str(title).strip()
        if 'Maks. Pacjenci' in title_f:
            additional_info['max_patients'] = int(count.text.strip())

        if 'LPR' in title_f:
            additional_info['LPR'] = True
            additional_info['LPR_chances'] = int(count.text.strip())

        if 'zastąpione przez Radiowozy straży miejskiej' in title_f:
            additional_info['SM_replace'] = int(count.text.strip())

    requirement_table = html.find('th', text="Wymagania pojazdów i personelu").find_parent("table")

    for tr in requirement_table.find_all("tr"):
        trs = tuple(tr.children)
        _, car, _, count, _ = tuple(tr.children)

        try:
            car_enum = Cars(car.text.strip())
            current_count = requirements.get(car_enum, 0)
            count = int(count.text.strip())
            if current_count < count:
                requirements[car_enum] = count
            mission_requirements[car_enum] = count
            mission_requirements2[car_enum.name] = count
        except ValueError as err:
            pass
        # all_possible_requirements.add(td.text.strip())
    if missions_requirements.get(mission_name) is not None:
        missions_requirements[mission_name]['cars'] = {**missions_requirements[mission_name]['cars'], **{
            vehicle_key: max(
                missions_requirements[mission_name]['cars'].get(vehicle_key, 0),
                new_count) for vehicle_key, new_count in mission_requirements2.items()
        }}
    else:
        missions_requirements[mission_name] = {'cars': mission_requirements2, 'info': additional_info}

print(json.dumps(missions_requirements))
with open('missions.json', 'w+', encoding='utf-8') as f:
    f.write(json.dumps(missions_requirements))
