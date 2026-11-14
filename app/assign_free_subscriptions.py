from datetime import datetime, timezone

from app import create_app
from app.extensions import db
from app.models import User, SubscriptionPlan, UserSubscription

app = create_app()

with app.app_context():
    free_plan = SubscriptionPlan.query.filter_by(
        code="free_monthly",
        is_active=True
    ).first()

    if not free_plan:
        raise RuntimeError("Active Free monthly plan was not found.")

    users = User.query.all()
    assigned = 0
    skipped = 0

    for user in users:
        active_subscription = UserSubscription.query.filter_by(
            user_id=user.id,
            status="active"
        ).first()

        if active_subscription:
            skipped += 1
            continue

        subscription = UserSubscription(
            user_id=user.id,
            plan_id=free_plan.id,
            status="active",
            starts_at=datetime.now(timezone.utc),
            ends_at=None,
            auto_renew=False
        )

        db.session.add(subscription)
        assigned += 1

    db.session.commit()

    print(f"Users checked: {len(users)}")
    print(f"Free subscriptions assigned: {assigned}")
    print(f"Users with an active subscription skipped: {skipped}")
