from jafgen.time import Day
from jafgen.customers.customer import Customer, BrunchCrowd, RemoteWorker, Student
from jafgen.customers.order import Order, OrderItem
from jafgen.stores.product import ProductType
from jafgen.stores.inventory import Inventory
from jafgen.stores.store import Store


def test_order_totals(default_store: Store):
    """Ensure order totals are equivalent to the sum of the item prices and tax paid."""
    inventory = Inventory()
    orders: list[Order] = []
    customer_types: list[type[Customer]] = [RemoteWorker, BrunchCrowd, Student]
    for i in range(1000):
        for CustType in customer_types:
            order_items = [
                OrderItem(product=p, quantity=1)
                for p in (
                    inventory.get_item_type(ProductType.JAFFLE, 2)
                    + inventory.get_item_type(ProductType.BEVERAGE, 1)
                )
            ]
            orders.append(
                Order(
                    customer=CustType(store=default_store),
                    order_items=order_items,
                    store=default_store,
                    day=Day(date_index=i),
                )
            )

    for order in orders:
        expected_subtotal = sum(i.product.price * i.quantity for i in order.order_items)
        assert order.subtotal == expected_subtotal
        assert order.tax_paid == order.subtotal * order.store.tax_rate
        assert order.total == order.subtotal + order.tax_paid
        assert round(float(order.total), 2) == round(
            float(order.subtotal), 2
        ) + round(float(order.tax_paid), 2)
        order_dict = order.to_dict()
        assert (
            order_dict["order_total"] == order_dict["subtotal"] + order_dict["tax_paid"]
        )
