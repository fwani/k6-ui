"""FastAPI 앱 진입점. CORS, 전역 예외 처리, 라우터 플레이스홀더."""

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

import app.database  # noqa: F401 - ensure DB init on import
from app.api.config import router as config_router
from app.api.runs import router as runs_router
from app.api.tests import router as tests_router
from app.api.uploads import router as uploads_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

app = FastAPI(title="성능 테스트 API", version="0.0.1")
app.include_router(tests_router)
app.include_router(runs_router)
app.include_router(config_router)
app.include_router(uploads_router)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(_request: Request, exc: StarletteHTTPException) -> JSONResponse:
    code = "NOT_FOUND" if exc.status_code == 404 else "BAD_REQUEST"
    message = exc.detail if isinstance(exc.detail, str) else "리소스를 찾을 수 없습니다." if exc.status_code == 404 else "잘못된 요청입니다."
    return JSONResponse(
        status_code=exc.status_code,
        content={"message": message, "code": code},
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    _request: Request, exc: RequestValidationError
) -> JSONResponse:
    errors = exc.errors()
    msg = "; ".join(
        f"{e.get('loc', ())}: {e.get('msg', '')}" for e in (errors or [])
    ) or "검증 오류"
    return JSONResponse(
        status_code=422,
        content={"message": msg, "code": "VALIDATION_ERROR", "details": errors},
    )


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
