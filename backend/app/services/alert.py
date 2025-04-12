from typing import List, Optional
from datetime import datetime
from app.models.alert import Alert
from app.schemas.alert import AlertCreate
from sqlalchemy.orm import Session

class AlertService:
    def __init__(self):
        self.alert_threshold = 0.8  # Configurable threshold for generating alerts

    def create_alert(self, db: Session, alert: AlertCreate) -> Alert:
        db_alert = Alert(
            alert_type=alert.alert_type,
            severity=alert.severity,
            track_id=alert.track_id,
            description=alert.description,
            timestamp=datetime.utcnow()
        )
        db.add(db_alert)
        db.commit()
        db.refresh(db_alert)
        return db_alert

    def get_alerts(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[Alert]:
        query = db.query(Alert)
        
        if start_time:
            query = query.filter(Alert.timestamp >= start_time)
        if end_time:
            query = query.filter(Alert.timestamp <= end_time)
            
        return query.order_by(Alert.timestamp.desc()).offset(skip).limit(limit).all()

    def process_detection(self, detection: dict) -> Optional[AlertCreate]:
        """
        Process a detection and create an alert if necessary
        """
        if detection.get('confidence', 0) > self.alert_threshold:
            return AlertCreate(
                alert_type='warning',
                severity=3,
                track_id=detection.get('track_id', 'unknown'),
                description=f"High confidence detection at {detection.get('location', 'Unknown')}"
            )
        return None 