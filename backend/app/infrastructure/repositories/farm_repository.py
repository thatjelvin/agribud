from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.domain.models import Farm, FarmSnapshot, RiskAlert, YieldPrediction


class FarmRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_farm(self, farm: Farm) -> Farm:
        self.db.add(farm)
        self.db.commit()
        self.db.refresh(farm)
        return farm

    def list_farms_for_owner(self, owner_id: int) -> list[Farm]:
        return list(self.db.scalars(select(Farm).where(Farm.owner_id == owner_id)))

    def get_farm(self, farm_id: int) -> Farm | None:
        return self.db.get(Farm, farm_id)

    def add_snapshot(self, snapshot: FarmSnapshot) -> FarmSnapshot:
        self.db.add(snapshot)
        self.db.commit()
        self.db.refresh(snapshot)
        return snapshot

    def list_snapshots(self, farm_id: int) -> list[FarmSnapshot]:
        return list(self.db.scalars(select(FarmSnapshot).where(FarmSnapshot.farm_id == farm_id).order_by(desc(FarmSnapshot.captured_at))))

    def add_prediction(self, prediction: YieldPrediction) -> YieldPrediction:
        self.db.add(prediction)
        self.db.commit()
        self.db.refresh(prediction)
        return prediction

    def add_alerts(self, alerts: list[RiskAlert]) -> list[RiskAlert]:
        self.db.add_all(alerts)
        self.db.commit()
        for alert in alerts:
            self.db.refresh(alert)
        return alerts

    def list_alerts(self, farm_id: int) -> list[RiskAlert]:
        return list(self.db.scalars(select(RiskAlert).where(RiskAlert.farm_id == farm_id).order_by(desc(RiskAlert.created_at))))
