import stripe
from config.settings import settings

PAYMENT_METHODS = {
    "card": {"name": "pm_card_visa", "id": "card_id"},
    "multibanco": {"name": "pm_multibanco", "id": "multibanco_id"},
    "paypal": {"name": "pm_paypal", "id": "paypal_id"},
}

PLANS = {
    "free": {
        "name": "free",
        "description": "Free plan",
        "price": 0,
        "product_id": "id",
        "price_id": "id",
    }
}


class StripeServices:
    def __init__(self):
        stripe.api_key = settings.stripe_api_key
        self.init_stripe()

    def init_stripe(self):
        products = stripe.Product.list().data
        products_name = [product.get("name") for product in products]
        prices = stripe.Price.list().data

        for plan_name, plan_details in PLANS.items():
            if plan_name not in products_name:
                print(f"Creating product: {plan_details['name']}")
                product = self.create_product(
                    plan_details["name"], plan_details["description"]
                )
                price = self.create_prices(
                    product.id, plan_details["price"], "eur", "month"
                )
                PLANS[plan_name]["product_id"] = product.id
                PLANS[plan_name]["price_id"] = price.id
            else:
                product = next(filter(lambda x: x.get("name") == plan_name, products))
                price = next(filter(lambda x: x.get("product") == product.id, prices))
                PLANS[plan_name]["product_id"] = product.id
                PLANS[plan_name]["price_id"] = price.id

    def create_customer(self, email: str, user_id: str, name: str) -> stripe.Customer:
        return stripe.Customer.create(
            email=email, name=name, metadata={"user_id": user_id}
        )

    def get_customer_plan(self, customer_id: str) -> stripe.Subscription:
        subscriptions = stripe.Subscription.list(customer=customer_id)
        if subscriptions.data:
            return subscriptions.data[0]
        return None

    def create_subscription(
        self, customer_id: str, plan_name: str, payment_method_id: str
    ) -> stripe.Subscription:
        price_id = PLANS.get(plan_name).get("price_id")
        print(price_id)
        return stripe.Subscription.create(
            customer=customer_id,
            items=[{"price": price_id}],
            expand=["latest_invoice.payment_intent"],
            default_payment_method=payment_method_id,
        )

    def update_subscription(
        self, subscription_id: str, price_id: str
    ) -> stripe.Subscription:
        return stripe.Subscription.modify(
            subscription_id,
            items=[{"price": price_id}],
            expand=["latest_invoice.payment_intent"],
        )

    def create_product(self, name: str, description: str) -> stripe.Product:
        return stripe.Product.create(name=name, description=description)

    def create_prices(
        self, product_id: str, unit_amount: int, currency: str, interval: str
    ) -> stripe.Price:
        return stripe.Price.create(
            product=product_id,
            unit_amount=unit_amount,
            currency=currency,
            recurring={"interval": interval},
        )

    def attach_payment_method(self, customer_id: str, payment_method_id: str):
        stripe.PaymentMethod.attach(payment_method_id, customer=customer_id)
        stripe.Customer.modify(
            customer_id, invoice_settings={"default_payment_method": payment_method_id}
        )
