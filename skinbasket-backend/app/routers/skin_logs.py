import uuid
from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.security import get_current_profile_id
from app.db.session import get_db
from app.models.skin_log import SkinLog
from app.schemas.skin_log import SkinLogCreate, SkinLogOut

router = APIRouter(prefix="/skin-logs", tags=["skin-logs"])


@router.post("", response_model=SkinLogOut)
def create_skin_log(
    body: SkinLogCreate,
    profile_id: uuid.UUID = Depends(get_current_profile_id),
    db: Session = Depends(get_db),
):
    """photo_url은 Supabase Storage에 프론트가 먼저 업로드하고 그 URL만 여기로 보낸다는 전제
    (사진 바이너리 자체를 이 API로 넘기지 않음). 사진 저장 위치가 기기로 바뀌면 이 필드는
    빠지거나 optional 유지로 충분히 대응 가능."""
    skin_log = SkinLog(
        profile_id=profile_id,
        logged_at=body.logged_at or datetime.utcnow(),
        trouble_level=body.trouble_level,
        oil_level=body.oil_level,
        dryness_level=body.dryness_level,
        photo_url=body.photo_url,
        memo=body.memo,
    )
    db.add(skin_log)
    db.commit()
    db.refresh(skin_log)
    return skin_log


@router.get("", response_model=list[SkinLogOut])
def list_skin_logs(
    profile_id: uuid.UUID = Depends(get_current_profile_id),
    db: Session = Depends(get_db),
):
    return (
        db.query(SkinLog)
        .filter(SkinLog.profile_id == profile_id)
        .order_by(SkinLog.logged_at.asc())
        .all()
    )
