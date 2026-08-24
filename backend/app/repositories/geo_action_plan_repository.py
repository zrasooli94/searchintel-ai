from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.geo_action_item import GeoActionItem
from app.models.geo_action_plan import GeoActionPlan


class GeoActionPlanRepository:

    @staticmethod
    def create_plan(
        db: Session,
        **data,
    ) -> GeoActionPlan:

        plan = GeoActionPlan(
            **data
        )

        db.add(plan)
        db.flush()

        return plan

    @staticmethod
    def create_item(
        db: Session,
        **data,
    ) -> GeoActionItem:

        item = GeoActionItem(
            **data
        )

        db.add(item)
        db.flush()

        return item

    @staticmethod
    def latest(
        db: Session,
        experiment_id: int,
    ) -> GeoActionPlan | None:

        statement = (
            select(GeoActionPlan)
            .where(
                GeoActionPlan.experiment_id
                == experiment_id
            )
            .order_by(
                GeoActionPlan.created_at.desc(),
                GeoActionPlan.id.desc(),
            )
            .limit(1)
        )

        return db.scalar(statement)

    @staticmethod
    def list_items(
        db: Session,
        action_plan_id: int,
    ) -> list[GeoActionItem]:

        statement = (
            select(GeoActionItem)
            .where(
                GeoActionItem.action_plan_id
                == action_plan_id
            )
            .order_by(
                GeoActionItem.sort_order,
                GeoActionItem.id,
            )
        )

        return list(
            db.scalars(statement).all()
        )
