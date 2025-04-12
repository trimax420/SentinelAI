from app.models.camera import Camera
from app.models.analytics import Analytics
from app.models.alert import Alert
from app.models.detection import DetectionEvent
from app.models.suspect import Suspect, SuspectImage, SuspectLocation, Case

# Import all models here to ensure proper relationship initialization
__all__ = ['Camera', 'Analytics', 'Alert', 'DetectionEvent', 'Suspect', 'SuspectImage', 'SuspectLocation', 'Case']
