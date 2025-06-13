import logging
from sqlalchemy.orm import Session
from .models import ActionLog

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    handlers=[
        logging.FileHandler("user_actions.log")
    ]
)

logger = logging.getLogger("user-management")

def log_action(db: Session, action: str, status: str = "success", ip: str | None = None, user_id: int | None = None, username: str | None = None):
    log = ActionLog(user_id=user_id, username=username, action=action, status=status, ip_address=ip)
    db.add(log)
    db.commit()
