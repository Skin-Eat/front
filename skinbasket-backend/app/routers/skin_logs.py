import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.envelope import EnvelopeRoute
from app.core.security import get_current_profile_id
from app.db.session import get_db
from app.models.skin_log import SkinLog
from app.schemas.skin_log import SkinLogCreate, SkinLogOut

router = APIRouter(prefix="/skin-logs", tags=["skin-logs"], route_class=EnvelopeRoute)


@router.post("", response_model=SkinLogOut)
def create_skin_log(
    body: SkinLogCreate,
    profile_id: uuid.UUID = Depends(get_current_profile_id),
    db: Session = Depends(get_db),
):
    """photo_url은 Supabase Storage에 프론트가 먼저 업로드하고 그 URL만 여기로 보낸다는 전제
    (사진 바이너리 자체를 이 API로 넘기지 않음). 사진 저장 위치가 기기로 바뀌면 이 필드는
    빠지거나 optional 유지로 충분히 대응 가능. photoConsent=false인 유저는 프론트가 그냥
    photo_url을 안 보내면 됨(백엔드에서 강제 검증은 안 함)."""
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
    from_: datetime | None = Query(default=None, alias="from"),
    to: datetime | None = None,
    profile_id: uuid.UUID = Depends(get_current_profile_id),
    db: Session = Depends(get_db),
):
    query = db.query(SkinLog).filter(SkinLog.profile_id == profile_id)
    if from_ is not None:
        query = query.filter(SkinLog.logged_at >= from_)
    if to is not None:
        query = query.filter(SkinLog.logged_at <= to)
    return query.order_by(SkinLog.logged_at.asc()).all()


@router.delete("/{skin_log_id}")
def delete_skin_log(
    skin_log_id: int,
    profile_id: uuid.UUID = Depends(get_current_profile_id),
    db: Session = Depends(get_db),
):
    skin_log = db.get(SkinLog, skin_log_id)
    if skin_log is None or skin_log.profile_id != profile_id:
        raise HTTPException(status_code=404, detail="피부 기록이 없습니다.")
    db.delete(skin_log)
    db.commit()
    return None
