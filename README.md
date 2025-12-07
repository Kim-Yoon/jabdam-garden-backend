# 잡담의 화원 Backend

## 🚀 기술 스택

| 분류           | 기술                   |
| -------------- | ---------------------- |
| Framework      | FastAPI                |
| Database       | MySQL + SQLAlchemy ORM |
| Authentication | JWT (쿠키 기반)        |
| Security       | bcrypt, python-jose    |
| AI             | Google Gemini API      |
| Python         | 3.11+                  |

## 📁 프로젝트 구조

```
backend/
├── main.py                     # FastAPI 앱 엔트리포인트
├── config.py                   # 환경 설정 (pydantic-settings)
├── database.py                 # DB 연결 및 세션 관리
├── requirements.txt            # 의존성 목록
│
├── controllers/                # 비즈니스 로직
│   ├── user_controller.py      # 사용자 관련 로직
│   ├── post_controller.py      # 게시물 관련 로직
│   ├── comment_controller.py   # 댓글 관련 로직
│   └── genai_controller.py     # AI 게시물 생성 로직
│
├── models/                     # SQLAlchemy 모델
│   ├── user_model.py           # 사용자 모델
│   ├── post_model.py           # 게시물 모델
│   ├── post_like.py            # 좋아요 모델
│   └── comment_model.py        # 댓글 모델
│
├── routers/                    # API 엔드포인트
│   ├── user_router.py          # /users 라우터
│   ├── post_router.py          # /posts 라우터
│   ├── comment_router.py       # /posts/{id}/comments 라우터
│   └── ai_post_router.py       # /ai-posts 라우터
│
├── schemas/                    # Pydantic 스키마
│   ├── user_schema.py          # 사용자 요청/응답 스키마
│   ├── post_schema.py          # 게시물 요청/응답 스키마
│   └── comment_schema.py       # 댓글 요청/응답 스키마
│
├── utils/                      # 유틸리티
│   ├── auth.py                 # JWT 토큰 생성/검증
│   ├── db_utils.py             # DB 유틸리티
│   ├── img_validators.py       # 이미지 검증/저장
│   ├── user_validators.py      # 사용자 인증 검증
│   ├── post_validators.py      # 게시물 유효성 검증
│   ├── comment_validators.py   # 댓글 유효성 검증
│   └── pwd_validators.py       # 비밀번호 유효성 검증
│
├── uploads/                    # 업로드 파일 저장소
│   ├── posts/                  # 게시물 이미지
│   └── profiles/               # 프로필 이미지
│
└── tests/                      # 테스트
```

### 설치

```bash
pip install -r requirements.txt
```

### 환경 변수 설정

`.env` 파일을 생성하고 다음 내용을 설정합니다:

```env
DATABASE_URL=mysql+pymysql://user:password@localhost:3306/dbname
SECRET_KEY=your-secret-key
DEBUG=True
GEMINI_API_KEY=your-gemini-api-key
```

### 서버 실행

```bash
uvicorn main:app --reload
```

서버 실행 후 http://127.0.0.1:8000/docs 에서 Swagger API 문서 확인 가능

## 📄 API 엔드포인트

### 👤 Users (`/users`)

| 메서드   | 경로                 | 설명             | 인증 |
| -------- | -------------------- | ---------------- | ---- |
| `GET`    | `/users`             | 전체 사용자 조회 | ❌   |
| `POST`   | `/users`             | 회원가입         | ❌   |
| `GET`    | `/users/check-email` | 이메일 중복 확인 | ❌   |
| `GET`    | `/users/check-name`  | 이름 중복 확인   | ❌   |
| `POST`   | `/users/login`       | 로그인           | ❌   |
| `POST`   | `/users/logout`      | 로그아웃         | ✅   |
| `GET`    | `/users/me`          | 내 정보 조회     | ✅   |
| `PATCH`  | `/users/me`          | 내 정보 수정     | ✅   |
| `PATCH`  | `/users/me/password` | 비밀번호 변경    | ✅   |
| `DELETE` | `/users/me`          | 회원 탈퇴        | ✅   |

### 📝 Posts (`/posts`)

| 메서드   | 경로                | 설명             | 인증 |
| -------- | ------------------- | ---------------- | ---- |
| `GET`    | `/posts`            | 전체 게시물 조회 | ❌   |
| `GET`    | `/posts/{id}`       | 게시물 상세 조회 | ❌   |
| `POST`   | `/posts`            | 게시물 작성      | ✅   |
| `PATCH`  | `/posts/{id}`       | 게시물 수정      | ✅   |
| `DELETE` | `/posts/{id}`       | 게시물 삭제      | ✅   |
| `POST`   | `/posts/{id}/like`  | 좋아요           | ✅   |
| `DELETE` | `/posts/{id}/like`  | 좋아요 취소      | ✅   |
| `GET`    | `/posts/{id}/likes` | 좋아요 목록 조회 | ❌   |

### 💬 Comments (`/posts/{post_id}/comments`)

| 메서드   | 경로                             | 설명      | 인증 |
| -------- | -------------------------------- | --------- | ---- |
| `GET`    | `/posts/{post_id}/comments`      | 댓글 목록 | ❌   |
| `POST`   | `/posts/{post_id}/comments`      | 댓글 작성 | ✅   |
| `PATCH`  | `/posts/{post_id}/comments/{id}` | 댓글 수정 | ✅   |
| `DELETE` | `/posts/{post_id}/comments/{id}` | 댓글 삭제 | ✅   |

### 🤖 AI Posts (`/ai-posts`)

| 메서드 | 경로                       | 설명                | 인증 |
| ------ | -------------------------- | ------------------- | ---- |
| `POST` | `/ai-posts/generate-draft` | AI 게시물 초안 생성 | ❌   |

## ✨ 주요 기능

### 🤖 AI 기능

- Google Gemini API 연동
- 이미지/텍스트 기반 게시물 초안 생성
- 다양한 스타일 지원 (casual, formal 등)

### 🔐 인증

- 쿠키 기반 JWT 세션 인증
- bcrypt 비밀번호 해싱
- 로그인 상태 자동 유지

### 📝 게시물

- 게시물 CRUD
- 이미지 업로드 (최대 10MB)
- 조회수 카운트
- 좋아요 기능

### 💬 댓글

- 댓글 CRUD
- 페이지네이션 지원 (page, limit)

### 📷 이미지 업로드

- 지원 형식: JPEG, PNG, GIF, WEBP
- 최대 파일 크기: 10MB
- 최대 해상도: 4096x4096
- 정적 파일 서빙: `/uploads/...`(로컬에 저장)

## 📦 주요 의존성

- `fastapi`: >=0.121.0
- `uvicorn`: >=0.38.0
- `sqlalchemy`: >=2.0.0
- `pydantic-settings`: >=2.3.0
- `python-jose[cryptography]`: >=3.3.0
- `bcrypt`: >=4.0.0

## 🔗 관련 프로젝트

- **Frontend**: React + Vite 기반 프론트엔드 (`../frontend`)
