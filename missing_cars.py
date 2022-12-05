from const import MISSING_CARS_MAP, Cars
from termcolor import cprint


class NeededCars:
    def __init__(self, cars: dict) -> None:
        self.cars = cars

    def __add__(self, other: "NeededCars") -> dict:
        new_cars = {**self.cars, **other.cars}
        for k, c in new_cars.items():
            new_cars[k] = max(self.cars.get(k, 0), other.cars.get(k, 0))
        return new_cars


def parse_missing_cars(missing_cars: str) -> NeededCars:
    missing_cars = missing_cars.replace('Potrzebne pojazdy: ', '').replace('.', '').replace('-', '').replace('–', '')
    needed_cars = {}
    for missing_car in missing_cars.split(','):
        car_split = missing_car.strip().split(' ')
        count = car_split[0].strip()
        name = ' '.join(car_split[1:]).strip()
        car = MISSING_CARS_MAP.get(name)
        if car:
            if car == Cars.SPKP:
                needed_cars[car.name] = round(int(count)/6)
            else:
                needed_cars[car.name] = int(count)
        elif car is None:
            cprint(f"{missing_car} {count} |{name}| {car}", "red")

    return NeededCars(needed_cars)


def parse_missing_policemen(missing_policemen: str) -> NeededCars:
    missing_policemen = missing_policemen.strip().replace('Potrzeba jeszcze ', '').split(' ')
    count = missing_policemen[0]
    return NeededCars({Cars.OPI.name: round(int(count)/2)})


def get_missing_cars_map(missing_cars_text: str) -> dict:
    parts = missing_cars_text.split('.')
    needed_cars = NeededCars({})
    for part in parts:
        if "Potrzebne pojazdy:" in part:
            part_needed_cars = parse_missing_cars(part)
            needed_cars.cars = needed_cars + part_needed_cars

        if "Potrzeba jeszcze" in part:
            part_needed_cars = parse_missing_policemen(part)
            needed_cars.cars = needed_cars + part_needed_cars

    return needed_cars.cars
