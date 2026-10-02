"""Gemini 연습: 샘플 이미지 한 장의 글자를 그대로 옮겨 적게 해서 OCR 품질을 눈으로 확인한다.

    python scripts/try_gemini.py                       # case1_contract.png
    python scripts/try_gemini.py case2_contract.png

합성 샘플만 넣을 것. 무료 티어 입력은 Google 제품 개선에 쓰일 수 있다.
"""

import sys
from pathlib import Path

from google import genai
from google.genai import types

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))   # backend/ 를 import 경로에
from app.config import settings  # noqa: E402

SAMPLES = Path(__file__).resolve().parents[2] / "samples"
PROMPT = "이 문서의 모든 글자를 줄바꿈까지 그대로 옮겨 적어줘. 표는 한 행을 한 줄로, 칸 사이는 ' | '로. 설명하지 마."


def main(name: str = "case1_contract.png") -> None:
    client = genai.Client(api_key=settings.gemini_api_key)
    image = (SAMPLES / name).read_bytes()
    res = client.models.generate_content(
        model=settings.gemini_model,
        contents=[types.Part.from_bytes(data=image, mime_type="image/png"), PROMPT],
        config=types.GenerateContentConfig(temperature=0),
    )
    print(res.text)


if __name__ == "__main__":
    main(*sys.argv[1:])
