import stripe
from fastapi import HTTPException
from fastapi import status
from utils.exceptions import DeclinedPaymentMethodException

# from config.settings import settings

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
    },
    "premium": {
        "name": "premium",
        "description": "Premium plan",
        "price": 1000,
        "product_id": "id",
        "price_id": "id",
    },
    "premium_plus": {
        "name": "premium_plus",
        "description": "Premium plus plan",
        "price": 2000,
        "product_id": "id",
        "price_id": "id",
    },
}


class StripeServices:
    def __init__(self):
        # stripe.api_key = settings.stripe_api_key
        stripe.api_key = "sk_test_51QLrGmCDsmArD3lWBcjVz5eZ1mOi1t5gxr5MxQofAKd9VnnQioKybcPIW59eQ9XohLTawvMiN3YeuQqKdGMqP88d00yiIrOTut"
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
                # print(f"Product already exists: {plan_name}")
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

    def get_customer(self, user_id: str) -> stripe.Customer:
        customers = stripe.Customer.list()
        for customer in customers.data:
            if customer.metadata.get("user_id") == user_id:
                return customer
        return None

    def create_subscription(
        self, customer_id: str, price_id: str, payment_method_id: str
    ) -> stripe.Subscription:
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

    def create_payment_method(self, type: str, token: str) -> stripe.PaymentMethod:
        return stripe.PaymentMethod.create(type=type, card={"token": token})

    def upgrade_plan(
        self, user_id: str, plan_name: str, payment_method_name: str, token: str
    ):
        plan = PLANS.get(plan_name)

        try:
            if not plan:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid plan name"
                )
            subscription = self.get_customer_plan(user_id)

            if payment_method_name not in PAYMENT_METHODS.keys():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid Payment Method",
                )
            payment_method = stripe.Source.create(type=payment_method_name, token=token)

            stripe.Customer.modify(user_id, source=payment_method.id)
            stripe.PaymentMethod.attach(payment_method.id, customer=user_id)
            stripe.Customer.modify(
                user_id, invoice_settings={"default_payment_method": payment_method.id}
            )
            plan_price = PLANS.get(plan_name).get("price_id")
            subscription = self.create_subscription(
                user_id, plan_price, payment_method.id
            )
            return subscription
        except stripe.InvalidRequestError as e:
            raise DeclinedPaymentMethodException()

        except Exception as e:
            raise Exception(f"Failed to upgrade plan: {str(e)}")
