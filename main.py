"""
FastAPI 애플리케이션 엔트리포인트.
라우터를 등록하여 사용자, 게시글, 댓글 관련 API를 제공합니다.
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from routers.user_router import router as user_router
from routers.post_router import router as post_router
from routers.comment_router import router as comment_router
from routers.ai_post_router import router as ai_router

app = FastAPI(title="잡담의 화원 API", version="0.1.0")

# 정적 파일 서빙 (이미지 접근용)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================
# 🚨 전역 에러 핸들러
# ============================================
@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError):
    """Pydantic ValidationError를 422 응답으로 변환."""
    errors = []
    for error in exc.errors():
        errors.append({
            "field": ".".join(str(loc) for loc in error["loc"]),
            "message": error["msg"],
            "type": error["type"]
        })
    
    return JSONResponse(
        status_code=422,
        content={
            "detail": "입력값 검증 실패",
            "errors": errors
        }
    )


# 라우터 등록
app.include_router(user_router, tags=["users"])
app.include_router(post_router, tags=["posts"])
app.include_router(comment_router, tags=["comments"])
app.include_router(ai_router, tags=["ai"])