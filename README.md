# 공고그대로

> 지원할 때 본 채용공고와 받은 근로계약서를 항목별로 비교해, **달라진 조건을 서명 전에** 찾아 드립니다.

2026 고용24 국민참여 AI 고용서비스 발굴 온라인 해커톤 출품작 (MVP 개발 중)

## 왜 만들었나

공고에는 "월 250만 원, 정규직"이라고 써 있었는데, 계약서에는 수습 3개월 90%, 포괄임금, 계약직으로 바뀌어 있는 경우가 있습니다.
계약서를 받는 자리에서는 무엇이 달라졌는지 하나하나 대조하기 어렵고, 서명한 뒤에는 되돌리기 어렵습니다.

## 어떻게 동작하나

```
공고 캡처 ─┐
           ├─▶ ① AI가 읽기 ─▶ ② 인용 검증·마스킹 ─▶ ③ 규칙 엔진이 판정 ─▶ ④ AI가 쉬운 말로 설명
계약서 사진 ┘   (값 + 근거 인용)   (원문에 없는 값은 버림)   (법 기준·최저임금)     (질문 문구 제안)
```

- **판정은 규칙 엔진이, AI는 읽기와 설명만** 합니다. 같은 입력이면 항상 같은 결과가 나오고, 경고마다 근거 법 조문을 보여 줄 수 있습니다.
- AI가 읽은 값에는 원문 인용이 함께 붙고, 인용이 원문에 없으면 그 값은 쓰지 않습니다.
- 설명 문구에는 "위반·불법" 같은 단정 표현을 쓰지 않습니다. 걸러지면 다시 만들고, 그래도 걸리면 정해진 문구를 씁니다.

### 판정 결과 단계

| 단계 | 뜻 | 예 |
|---|---|---|
| 불리 변경 | 공고보다 나빠짐 | 월급 감액, 수습 신설, 정규직 → 계약직 |
| 법 기준 확인 | 법 기준에 못 미칠 수 있음 | 최저임금 미달, 위약·손해배상 조항 |
| 누락 | 계약서에 꼭 있어야 할 항목이 없음 | 임금 지급일, 휴일, 연차 |
| 모호 | 표현이 달라 확인이 필요함 | |
| 동일·유리 | 같거나 더 좋음 | |

비교 항목: 고용형태, 수습(기간·감액), 근무일, 주 근로시간, 포괄임금, 월 임금, 기본 시급, 최저임금, 근무지, 위약 조항, 필수 명시사항

## 화면 흐름

1. **공고 저장** — 공고 캡처(jpg·png·pdf)를 끌어다 놓거나 골라서 올리면, AI가 읽은 조건을 보여 줍니다.
2. **계약서 올리기** — 계약서를 아직 못 받았다면 교부를 요청하는 문구(근로기준법 제17조)를 복사할 수 있습니다.
3. **비교 결과** — 항목별 비교표, 단계별 요약, 근거 법 조문, 회사에 물어볼 질문 복사

## 기술 스택

| 영역 | 사용 |
|---|---|
| 백엔드 | Python 3.13, FastAPI, SQLAlchemy 2 + Alembic, SQLite |
| 프론트엔드 | Next.js 16 (App Router), React 19, Tailwind CSS v4 |
| AI | Google Gemini (`google-genai`) — 대회 제공 모델(엔노이아)로 교체 예정. 테스트·시연용 Mock 제공 |
| 공공데이터 | 국세청 사업자등록 상태조회, 법제처 법령 본문, 연도별 최저임금 |

## 폴더 구조

```
backend/
  app/
    ai/          # AI 제공자(Mock·Gemini), 프롬프트, 인용 검증, 마스킹, 표현 필터
    rules/       # 규칙 엔진 (정규화 + 항목별 판정)
    external/    # 국세청·법제처·최저임금
    services/    # 추출 → 판정 → 설명 흐름
    routers/     # API 엔드포인트
  data/          # 최저임금 CSV, 법 조문 캐시
  alembic/       # DB 마이그레이션
  tests/
frontend/src/
  app/           # 페이지 (/, /postings/[id], /comparisons/[id])
  components/
  lib/           # API 클라이언트, 업로드 검사, 법 조문 매핑
eval/            # 정확도 평가 (합성 데이터 40쌍)
samples/         # 예시 공고·계약서 3쌍과 정답
```

## 로컬에서 실행하기

필요: Python 3.13, Node.js, pnpm

### 백엔드

```powershell
cd backend
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
copy .env.example .env          # 아래 환경변수 참고
.venv\Scripts\alembic upgrade head
.venv\Scripts\uvicorn app.main:app --reload
```

http://localhost:8000/docs 에서 API를 확인할 수 있습니다.

### 프론트엔드

```powershell
cd frontend
pnpm install
pnpm dev
```

http://localhost:3000 에 접속합니다. 백엔드 주소가 다르면 `frontend/.env.local`에 `NEXT_PUBLIC_API_BASE_URL`을 지정합니다 (기본값 `http://localhost:8000`).

### 환경변수 (`backend/.env`)

| 이름 | 설명 |
|---|---|
| `AI_PROVIDER` | `mock`(기본, 키 없이 동작) 또는 `gemini` |
| `GEMINI_API_KEY` | Google AI Studio 키 |
| `GEMINI_MODEL` | 추출용 모델 |
| `GEMINI_EXPLAIN_MODEL` | 설명용 모델. 비우면 `GEMINI_MODEL` |
| `NTS_SERVICE_KEY` | 공공데이터포털 국세청 사업자등록 상태조회 키 (Decoding). 비우면 조회 생략 |
| `LAW_OC` | 법제처 Open API OC (법 조문 캐시 갱신용) |
| `DATABASE_URL` | 기본 `sqlite:///./local.db` |
| `CORS_ORIGINS` | 기본 `http://localhost:3000` |

> `AI_PROVIDER=mock`이면 `samples/`의 이미지는 정답 값으로, 그 밖의 이미지는 예시 값으로 처리합니다. 화면에 "MOCK 데이터" 안내가 표시됩니다.

## API

| 메서드 | 경로 | 설명 |
|---|---|---|
| GET | `/health` | 상태 확인 |
| POST | `/postings/extract` | 공고 이미지 업로드 → 추출·저장 |
| POST | `/postings` | 추출된 조건으로 공고 저장 |
| GET | `/postings/{id}` | 공고 조회 |
| POST | `/postings/{id}/business-check` | 사업자등록 상태조회 |
| POST | `/postings/{id}/compare` | 계약서 이미지 업로드 → 비교 |
| GET | `/comparisons/{id}` | 비교 결과 조회 |
| POST | `/rules/compare` | 조건 JSON 두 개로 판정만 (AI 없이) |
| GET | `/laws/{key}` | 법 조문 본문 |

## 테스트

```powershell
cd backend
.venv\Scripts\python -m pytest
```

규칙 엔진, 외부 API(녹화된 응답), DB, API, AI 응답 검증을 다룹니다 (276개).

## 정확도 (합성 데이터 기준)

공고·계약서 **40쌍(이미지 80장)**, 핵심 경고 50건으로 평가했습니다. 자세한 내용은 [`eval/README.md`](eval/README.md)에 있습니다.

| 모델 · 프롬프트 | 추출 정확도 | 핵심 경고 재현율 | 오탐 |
|---|---|---|---|
| gemini-3.5-flash-lite · v1 | 98.4% | 50/50 | 10 |
| gemini-3.5-flash-lite · **v2 (현재)** | **100%** | **50/50** | **0** |

> 양식 2~3종의 깨끗한 합성 문서로 잰 숫자입니다. 손글씨, 다양한 양식, 저화질 사진이 섞인 실제 문서의 정확도와 다를 수 있습니다.

## 개인정보

- 원본 이미지는 서버에 저장하지 않습니다. AI가 읽은 값과 원문 텍스트만 저장하고, 저장 전에 주민등록번호·휴대폰 번호·이메일을 가립니다.
- 개발과 평가에는 **합성 문서만** 사용합니다. 무료 티어 AI에는 실제 계약서를 넣지 않습니다.

## 진행 상황

- [x] 규칙 엔진, 공공데이터 연동, DB, AI 추출, 핵심 API
- [x] 화면 3종, 설명·질문 생성, 정확도 평가
- [ ] 배포
- [ ] 대회 제공 모델(엔노이아)로 교체 후 재평가

## 안내

이 서비스는 법률 자문이 아닙니다. 결과는 확인을 돕기 위한 참고용이며, 정확한 판단은 고용노동부 고객상담센터(국번 없이 1350)나 노무사에게 문의하세요.
