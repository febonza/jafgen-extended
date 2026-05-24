import uuid
from abc import ABC, abstractmethod
from collections import Counter
from dataclasses import dataclass, field
from typing import Any, NewType

import numpy as np
from faker import Faker

from jafgen.customers.order import Order, OrderItem
from jafgen.customers.tweet import Tweet
from jafgen.stores.inventory import Inventory
from jafgen.stores.product import Product, ProductType
from jafgen.stores.store import Store
from jafgen.time import Day, Season

fake = Faker()

CustomerId = NewType("CustomerId", uuid.UUID)


def _to_order_items(products: list[Product]) -> list[OrderItem]:
    return [OrderItem(product=p, quantity=q) for p, q in Counter(products).items()]


@dataclass(frozen=True)
class Customer(ABC):
    store: Store
    id: CustomerId = field(default_factory=lambda: CustomerId(fake.uuid4()))
    name: str = field(default_factory=fake.name)
    favorite_number: int = field(default_factory=lambda: fake.random.randint(1, 100))
    fan_level: int = field(default_factory=lambda: fake.random.randint(1, 5))

    def p_buy_season(self, day: Day):
        return self.store.p_buy(day)

    def p_buy(self, day: Day) -> float:
        p_buy_season = self.p_buy_season(day)
        p_buy_persona = self.p_buy_persona(day)
        p_buy_on_day = (p_buy_season * p_buy_persona) ** 0.5
        return p_buy_on_day

    @abstractmethod
    def p_buy_persona(self, day: Day) -> float:
        raise NotImplementedError()

    @abstractmethod
    def p_tweet_persona(self, day: Day) -> float:
        raise NotImplementedError()

    def p_tweet(self, day: Day) -> float:
        return self.p_tweet_persona(day)

    def get_order(self, day: Day) -> Order | None:
        order_items = self.get_order_items(day)

        order_minute = self.get_order_minute(day)
        order_day = day.at_minute(order_minute)

        if not self.store.is_open_at(order_day):
            return None

        return Order(
            customer=self,
            order_items=order_items,
            store=self.store,
            day=order_day,
        )

    def get_tweet(self, order: Order) -> Tweet:
        minutes_delta = int(fake.random.random() * 20)
        tweet_day = order.day.at_minute(order.day.total_minutes + minutes_delta)
        return Tweet(
            customer=self,
            order=order,
            day=tweet_day,
        )

    @abstractmethod
    def get_order_items(self, day: Day) -> list[OrderItem]:
        raise NotImplementedError()

    @abstractmethod
    def get_order_minute(self, day: Day) -> int:
        raise NotImplementedError()

    def sim_day(self, day: Day):
        p_buy = self.p_buy(day)
        p_buy_threshold = np.random.random()
        p_tweet = self.p_tweet(day)
        p_tweet_threshold = np.random.random()
        if p_buy > p_buy_threshold:
            if p_tweet > p_tweet_threshold:
                order = self.get_order(day)
                if order and len(order.order_items) > 0:
                    return order, self.get_tweet(order)
                else:
                    return None, None
            else:
                return self.get_order(day), None
        else:
            return None, None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": str(self.id),
            "name": str(self.name),
        }


class RemoteWorker(Customer):
    """This person works from a coffee shop"""

    def p_buy_persona(self, day: Day):
        buy_propensity = (self.favorite_number / 100) * 0.4
        return 0.001 if day.is_weekend else buy_propensity

    def p_tweet_persona(self, day: Day):
        return 0.01

    def get_order_minute(self, day: Day) -> int:
        avg_time = 60 * 7
        order_time = np.random.normal(loc=avg_time, scale=180)
        return max(0, int(order_time))

    def get_order_items(self, day: Day) -> list[OrderItem]:
        num_drinks = 1
        food: list[Product] = []

        if fake.random.random() > 0.7:
            num_drinks = 2

        if fake.random.random() > 0.7:
            food = Inventory.get_item_type(ProductType.JAFFLE, 1)

        products = Inventory.get_item_type(ProductType.BEVERAGE, num_drinks) + food
        return _to_order_items(products)


class BrunchCrowd(Customer):
    """Do you sell mimosas?"""

    def p_buy_persona(self, day: Day):
        buy_propensity = 0.2 + (self.favorite_number / 100) * 0.2
        return buy_propensity if day.is_weekend else 0

    def p_tweet_persona(self, day: Day):
        return 0.8

    def get_order_minute(self, day: Day) -> int:
        avg_time = 300 + ((self.favorite_number - 50) / 50) * 120
        order_time = np.random.normal(loc=avg_time, scale=120)
        return max(0, int(order_time))

    def get_order_items(self, day: Day) -> list[OrderItem]:
        num_customers = 1 + int(self.favorite_number / 20)
        products = (
            Inventory.get_item_type(ProductType.JAFFLE, num_customers)
            + Inventory.get_item_type(ProductType.BEVERAGE, num_customers)
        )
        return _to_order_items(products)


class Commuter(Customer):
    """the regular, thanks"""

    def p_buy_persona(self, day: Day):
        buy_propensity = 0.5 + (self.favorite_number / 100) * 0.3
        return 0.001 if day.is_weekend else buy_propensity

    def p_tweet_persona(self, day: Day):
        return 0.2

    def get_order_minute(self, day: Day) -> int:
        avg_time = 60
        order_time = np.random.normal(loc=avg_time, scale=30)
        return max(0, int(order_time))

    def get_order_items(self, day: Day) -> list[OrderItem]:
        products = Inventory.get_item_type(ProductType.BEVERAGE, 1)
        return _to_order_items(products)


class Student(Customer):
    """coffee might help"""

    def p_buy_persona(self, day: Day):
        if day.season == Season.SUMMER:
            return 0

        buy_propensity = 0.1 + (self.favorite_number / 100) * 0.4
        return buy_propensity

    def p_tweet_persona(self, day: Day):
        return 0.8

    def get_order_minute(self, day: Day) -> int:
        avg_time = 9 * 60
        order_time = np.random.normal(loc=avg_time, scale=120)
        return max(0, int(order_time))

    def get_order_items(self, day: Day) -> list[OrderItem]:
        food: list[Product] = []
        if fake.random.random() > 0.5:
            food = Inventory.get_item_type(ProductType.JAFFLE, 1)

        products = Inventory.get_item_type(ProductType.BEVERAGE, 1) + food
        return _to_order_items(products)


class Casuals(Customer):
    """just popping in"""

    def p_buy_persona(self, day: Day):
        return 0.1

    def p_tweet_persona(self, day: Day):
        return 0.1

    def get_order_minute(self, day: Day) -> int:
        avg_time = 5 * 60
        order_time = np.random.normal(loc=avg_time, scale=120)
        return max(0, int(order_time))

    def get_order_items(self, day: Day) -> list[OrderItem]:
        num_drinks = int(fake.random.random() * 10 / 3)
        num_food = int(fake.random.random() * 10 / 3)
        products = (
            Inventory.get_item_type(ProductType.BEVERAGE, num_drinks)
            + Inventory.get_item_type(ProductType.JAFFLE, num_food)
        )
        return _to_order_items(products)


class HealthNut(Customer):
    """A light beverage in the sunshine as a treat"""

    def p_buy_persona(self, day: Day):
        if day.season == Season.SUMMER:
            buy_propensity = 0.1 + (self.favorite_number / 100) * 0.4
            return buy_propensity
        return 0.2

    def p_tweet_persona(self, day: Day):
        return 0.6

    def get_order_minute(self, day: Day) -> int:
        avg_time = 5 * 60
        order_time = np.random.normal(loc=avg_time, scale=120)
        return max(0, int(order_time))

    def get_order_items(self, day: Day) -> list[OrderItem]:
        products = Inventory.get_item_type(ProductType.BEVERAGE, 1)
        return _to_order_items(products)
