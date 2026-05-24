import csv
import datetime as dt
import os
from typing import Any

from rich.progress import track

from jafgen.customers.customer import Customer, CustomerId
from jafgen.customers.order import Order
from jafgen.customers.tweet import Tweet
from jafgen.stores.inventory import Inventory
from jafgen.stores.market import Market
from jafgen.stores.stock import Stock
from jafgen.stores.store import Store
from jafgen.time import (
    Day,
    DayHoursOfOperation,
    WeekHoursOfOperation,
    time_from_total_minutes,
)

T_7AM = time_from_total_minutes(60 * 7)
T_8AM = time_from_total_minutes(60 * 8)
T_3PM = time_from_total_minutes(60 * 15)
T_8PM = time_from_total_minutes(60 * 20)

class Simulation:
    def __init__(self, years: int, days: int, prefix: str):
        self.years = years
        self.days = days
        self.scale = 100
        self.prefix = prefix
        self.stores = [
            # name | popularity | opened | TAM | tax
            ("Philadelphia", 0.85, 0, 9 * self.scale, 0.06),
            ("Brooklyn", 0.95, 192, 14 * self.scale, 0.04),
            ("Chicago", 0.92, 605, 12 * self.scale, 0.0625),
            ("San Francisco", 0.87, 615, 11 * self.scale, 0.075),
            ("New Orleans", 0.92, 920, 8 * self.scale, 0.04),
            ("Los Angeles", 0.87, 1107, 8 * self.scale, 0.08),
        ]

        self.markets: list[Market] = [
            Market(
                Store(
                    name=store_name,
                    base_popularity=popularity,
                    hours_of_operation=WeekHoursOfOperation(
                        week_days=DayHoursOfOperation(opens_at=T_7AM, closes_at=T_8PM),
                        weekends=DayHoursOfOperation(opens_at=T_8AM, closes_at=T_3PM),
                    ),
                    opened_day=Day(opened_date),
                    tax_rate=tax,
                ),
                num_customers=market_size,
            )
            for store_name, popularity, opened_date, market_size, tax in self.stores
        ]

        self.customers: dict[CustomerId, Customer] = {}
        self.orders: list[Order] = []
        self.tweets: list[Tweet] = []
        self.sim_days = 365 * self.years + self.days

    def run_simulation(self):
        for i in track(
            range(self.sim_days), description=f"🥪 Pressing {self.sim_days} days of fresh jaffles..."
        ):
            for market in self.markets:
                day = Day(i)
                for order, tweet in market.sim_day(day):
                    if order:
                        self.orders.append(order)
                        if order.customer.id not in self.customers:
                            self.customers[order.customer.id] = order.customer
                    if tweet:
                        self.tweets.append(tweet)

    def save_results(
        self,
        center_on: dt.date | None = None,
        export_from: dt.date | None = None,
    ) -> None:
        epoch_date = Day.EPOCH.date()
        shift = (center_on - epoch_date) if center_on is not None else None

        def _shift_date(iso_str: str) -> str:
            if shift is None:
                return iso_str
            return (dt.datetime.fromisoformat(iso_str) + shift).isoformat()

        def _keep(iso_str: str) -> bool:
            if export_from is None:
                return True
            return dt.datetime.fromisoformat(iso_str).date() >= export_from

        orders_dicts: list[dict[str, Any]] = []
        for order in self.orders:
            row = order.to_dict()
            row["ordered_at"] = _shift_date(row["ordered_at"])
            if _keep(row["ordered_at"]):
                orders_dicts.append(row)

        kept_ids = {row["id"] for row in orders_dicts}
        order_items_dicts = [
            item_row
            for order in self.orders
            for item_row in order.order_items_to_dict()
            if item_row["order_id"] in kept_ids
        ]

        tweets_dicts: list[dict[str, Any]] = []
        for tweet in self.tweets:
            row = tweet.to_dict()
            row["tweeted_at"] = _shift_date(row["tweeted_at"])
            if _keep(row["tweeted_at"]):
                tweets_dicts.append(row)

        stores_dicts: list[dict[str, Any]] = []
        for market in self.markets:
            row = market.store.to_dict()
            row["opened_at"] = _shift_date(row["opened_at"])
            stores_dicts.append(row)

        stock: Stock = Stock()
        inventory: Inventory = Inventory()
        entities: dict[str, list[dict[str, Any]]] = {
            "customers": [customer.to_dict() for customer in self.customers.values()],
            "orders": orders_dicts,
            "order_items": order_items_dicts,
            "stores": stores_dicts,
            "supplies": stock.to_dict(),
            "products": inventory.to_dict(),
            "tweets": tweets_dicts,
        }

        if not os.path.exists("./jaffle-data"):
            os.makedirs("./jaffle-data")
        for entity, data in track(
            entities.items(), description="Delivering jaffles..."
        ):
            if data:
                file = f"./jaffle-data/{self.prefix}_{entity}.csv"
                writer = csv.DictWriter(open(file, "w", newline=""), fieldnames=data[0].keys())
                writer.writeheader()
                writer.writerows(data)
