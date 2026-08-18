from fastapi import APIRouter

from app.core.envelope import EnvelopeRoute

router = APIRouter(tags=["health"], route_class=EnvelopeRoute)


@router.get("/health")
def health_check():
    return {"status": "ok"}
