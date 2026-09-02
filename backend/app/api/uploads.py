"""k6 multipart용 바이너리 업로드. API 서버 디스크에 저장 후 절대 경로 반환."""

import logging
import mimetypes
import uuid
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.config import K6_FIXTURE_DIR

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/uploads", tags=["uploads"])

_MAX_BYTES = 50 * 1024 * 1024


def _safe_filename(name: str) -> str:
    base = Path(name).name.strip()
    if not base or base in (".", ".."):
        raise HTTPException(status_code=400, detail="유효하지 않은 파일 이름입니다.")
    return base[:200]


def _guess_content_type(filename: str, header_ct: str | None) -> str:
    h = (header_ct or "").strip()
    if h and h.lower() != "application/octet-stream":
        return h
    guessed, _ = mimetypes.guess_type(filename)
    return guessed or "application/octet-stream"


@router.post("/k6-fixture")
async def upload_k6_fixture(file: UploadFile = File(...)) -> dict:
    """multipart 파일을 저장하고 k6 open()에 넘길 절대 경로·원본 파일명·Content-Type을 반환."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="파일 이름이 없습니다.")
    safe = _safe_filename(file.filename)
    K6_FIXTURE_DIR.mkdir(parents=True, exist_ok=True)
    unique = f"{uuid.uuid4().hex}_{safe}"
    root = K6_FIXTURE_DIR.resolve()
    dest = (K6_FIXTURE_DIR / unique).resolve()
    try:
        dest.relative_to(root)
    except ValueError:
        raise HTTPException(status_code=400, detail="잘못된 저장 경로입니다.") from None
    except OSError:
        raise HTTPException(status_code=500, detail="저장 경로를 확인할 수 없습니다.") from None

    total = 0
    try:
        with dest.open("wb") as out:
            while True:
                chunk = await file.read(1024 * 1024)
                if not chunk:
                    break
                total += len(chunk)
                if total > _MAX_BYTES:
                    raise HTTPException(
                        status_code=413,
                        detail=f"파일 크기는 {_MAX_BYTES // (1024 * 1024)}MB 를 넘을 수 없습니다.",
                    )
                out.write(chunk)
    except HTTPException:
        dest.unlink(missing_ok=True)
        raise
    except OSError as e:
        dest.unlink(missing_ok=True)
        logger.exception("k6_fixture_write_failed")
        raise HTTPException(status_code=500, detail="파일 저장에 실패했습니다.") from e
    finally:
        await file.close()

    content_type = _guess_content_type(safe, file.content_type)
    abs_path = str(dest)
    logger.info("k6_fixture_uploaded path=%s name=%s", abs_path, safe)
    return {
        "filePath": abs_path,
        "fileName": safe,
        "contentType": content_type,
    }
