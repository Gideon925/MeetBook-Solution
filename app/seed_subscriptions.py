from decimal import Decimal

from app import create_app
from app.extensions import db
from app.models import SubscriptionPlan


plans = [
    {
        "code": "free_monthly",
        "name": "Free",
        "billing_cycle": "monthly",
        "price": Decimal("0.00"),
        "message_limit": 30,
        "description": "Free MeetBook AI access.",
        "is_active": True,
    },
    {
        "code": "free_yearly",
        "name": "Free",
        "billing_cycle": "yearly",
        "price": Decimal("0.00"),
        "message_limit": 30,
        "description": "Free MeetBook AI access.",
        "is_active": True,
    },
    {
        "code": "standard_monthly",
        "name": "Standard",
        "billing_cycle": "monthly",
        "price": Decimal("0.00"),
        "message_limit": 500,
        "description": "Standard MeetBook AI subscription.",
        "is_active": False,
    },
    {
        "code": "standard_yearly",
        "name": "Standard",
        "billing_cycle": "yearly",
        "price": Decimal("0.00"),
        "message_limit": 500,
        "description": "Standard MeetBook AI subscription.",
        "is_active": False,
    },
    {
        "code": "pro_monthly",
        "name": "Pro",
        "billing_cycle": "monthly",
        "price": Decimal("0.00"),
        "message_limit": 2000,
        "description": "Professional MeetBook AI subscription.",
        "is_active": False,
    },
    {
        "code": "pro_yearly",
        "name": "Pro",
        "billing_cycle": "yearly",
        "price": Decimal("0.00"),
        "message_limit": 2000,
        "description": "Professional MeetBook AI subscription.",
        "is_active": False,
    },
]


app = create_app()

with app.app_context():
    for plan_data in plans:
        code = plan_data["code"]

        plan = SubscriptionPlan.query.filter_by(
            code=code
        ).first()

        if plan:
            for key, value in plan_data.items():
                setattr(plan, key, value)
        else:
            db.session.add(
                SubscriptionPlan(**plan_data)
            )

    db.session.commit()

    print("MeetBook AI subscription plans created successfully.")

    for plan in SubscriptionPlan.query.order_by(
        SubscriptionPlan.id
    ).all():
        print(
            f"{plan.name} | "
            f"{plan.billing_cycle} | "
            f"{plan.message_limit} messages | "
            f"Active: {plan.is_active}"
        )
