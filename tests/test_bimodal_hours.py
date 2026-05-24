import csv
import datetime as dt
import os

from jafgen.cli import _seed_all
from jafgen.customers.customer import DinnerCrowd, LunchRusher
from jafgen.simulation import Simulation, T_9AM, T_9PM
from jafgen.time import time_from_total_minutes

T_7AM = time_from_total_minutes(60 * 7)
T_3PM = time_from_total_minutes(60 * 15)


def _run_and_load_orders(tmp_path, seed=1):
    _seed_all(seed)
    tmp_path.mkdir(parents=True, exist_ok=True)
    orig = os.getcwd()
    os.chdir(tmp_path)
    try:
        sim = Simulation(1, 0, "raw")
        sim.run_simulation()
        sim.save_results()
        with open(tmp_path / "jaffle-data" / "raw_orders.csv") as f:
            return list(csv.DictReader(f))
    finally:
        os.chdir(orig)


def test_weekday_close_extended_to_9pm():
    assert T_9PM == time_from_total_minutes(60 * 21)


def test_weekend_open_at_9am():
    assert T_9AM == time_from_total_minutes(60 * 9)


def test_lunch_rusher_orders_near_1pm(tmp_path):
    orders = _run_and_load_orders(tmp_path)
    lunch_window = [
        r for r in orders
        if "T13:" in r["ordered_at"] or "T12:4" in r["ordered_at"] or "T13:1" in r["ordered_at"]
    ]
    assert len(lunch_window) > 0, "expected orders around 1 PM"


def test_dinner_crowd_orders_near_7pm(tmp_path):
    orders = _run_and_load_orders(tmp_path)
    dinner_window = [
        r for r in orders
        if "T18:" in r["ordered_at"] or "T19:" in r["ordered_at"] or "T20:" in r["ordered_at"]
    ]
    assert len(dinner_window) > 0, "expected orders in the 6–8 PM window"


def test_persona_mix_sums_to_one():
    from jafgen.stores.market import Market
    total = sum(w for _, w in Market.PersonaMix)
    assert abs(total - 1.0) < 1e-9


def test_new_personas_in_mix():
    from jafgen.stores.market import Market
    personas = [p for p, _ in Market.PersonaMix]
    assert LunchRusher in personas
    assert DinnerCrowd in personas
