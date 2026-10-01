"""국세청 사업자등록 상태조회 (공공데이터포털 odcloud API)."""

import httpx

from app.config import settings

NTS_URL = "https://api.odcloud.kr/api/nts-businessman/v1/status"


def get_business_status(b_no: str) -> dict | None:
    """사업자번호 한 개의 상태(b_stt_cd: 01 계속, 02 휴업, 03 폐업)를 돌려준다.

    키가 없거나 외부 API가 실패하면 None — 호출하는 쪽은 '확인 불가'로 처리한다.
    """
    b_no = b_no.replace("-", "").strip()
    if len(b_no) != 10 or not b_no.isdigit():
        raise ValueError("사업자등록번호는 숫자 10자리")
    if not settings.nts_service_key:
        return None
    try:
        r = httpx.post(NTS_URL, params={"serviceKey": settings.nts_service_key},
                       json={"b_no": [b_no]}, timeout=5)
        r.raise_for_status()
        data = r.json().get("data") or []
    except (httpx.HTTPError, ValueError):  # 네트워크·HTTP 오류, JSON이 아닌 응답
        return None  # 외부 API 실패가 서비스 전체를 막지 않게
    return data[0] if data else None
