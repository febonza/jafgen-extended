import csv
import datetime as dt
import os

import pytest

from jafgen.simulation import Simulation
from jafgen.time import Day

SIM_DAYS = 7


def _run(tmp_path, center_on=None, export_from=None):
    orig = os.getcwd()
    os.chdir(tmp_path)
    try:
        sim = Simulation(0, SIM_DAYS, "raw")
        sim.run_simulation()
        sim.save_results(center_on=center_on, export_from=export_from)

        orders = []
        orders_path = tmp_path / "jaffle-data" / "raw_orders.csv"
        if orders_path.exists():
            with open(orders_path) as f:
                orders = list(csv.DictReader(f))

        tweets = []
        tweets_path = tmp_path / "jaffle-data" / "raw_tweets.csv"
        if tweets_path.exists():
            with open(tweets_path) as f:
                tweets = list(csv.DictReader(f))

        return orders, tweets
    finally:
        os.chdir(orig)


def _order_date(row):
    return dt.date.fromisoformat(row["ordered_at"][:10])


def _tweet_date(row):
    return dt.date.fromisoformat(row["tweeted_at"][:10])


def test_no_flags_dates_in_epoch(tmp_path):
    orders, tweets = _run(tmp_path)
    epoch = Day.EPOCH.date()
    assert orders, "expected orders in output"
    for row in orders:
        assert _order_date(row) >= epoch
    for row in tweets:
        assert _tweet_date(row) >= epoch


def test_center_on_shifts_dates(tmp_path):
    center = dt.date(2022, 1, 1)
    orders, tweets = _run(tmp_path, center_on=center)
    assert orders, "expected orders in output"
    earliest = min(_order_date(r) for r in orders)
    assert earliest == center
    for row in orders:
        assert _order_date(row) >= center
    for row in tweets:
        assert _tweet_date(row) >= center


def test_export_from_filters_rows(tmp_path):
    export = dt.date(2023, 9, 5)
    orders, tweets = _run(tmp_path, export_from=export)
    for row in orders:
        assert _order_date(row) >= export
    for row in tweets:
        assert _tweet_date(row) >= export


def test_both_flags_compose(tmp_path):
    center = dt.date(2022, 1, 1)
    export = dt.date(2022, 1, 4)
    orders, tweets = _run(tmp_path, center_on=center, export_from=export)
    for row in orders:
        d = _order_date(row)
        assert d >= export
        assert d >= center
    for row in tweets:
        d = _tweet_date(row)
        assert d >= export
        assert d >= center
