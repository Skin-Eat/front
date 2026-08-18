from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class CamelModel(BaseModel):
    """요청/응답 JSON 필드를 camelCase로 주고받기 위한 베이스.

    API 명세서 v2(프론트 작성)가 photoConsent/skinType/accessToken처럼 camelCase를
    쓰기 때문에 도입함 — Python 쪽 필드명은 계속 snake_case로 쓰고, 이 클래스를
    상속하면 FastAPI 응답 직렬화/요청 파싱에서 자동으로 camelCase <-> snake_case 변환된다.

    새로 만드는 스키마는 이걸 상속할 것. 기존 스키마(BaseModel 직접 상속, 예: schemas/basket.py,
    schemas/recipe.py 등)는 아직 snake_case로 나가는데, 명세서 반영 작업을 마저 진행하면서
    점진적으로 이걸로 옮길 것 — 한 번에 다 바꾸면 리뷰가 너무 커져서 auth부터 먼저 적용함.
    """

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, from_attributes=True)
