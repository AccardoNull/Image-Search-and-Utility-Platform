import json
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from fastapi.staticfiles import StaticFiles
from algorithms.kmp import kmp_steps, kmp_contains
from fastapi.middleware.cors import CORSMiddleware
import subprocess
from fastapi.responses import FileResponse, RedirectResponse
from pathlib import Path
from PIL import Image, UnidentifiedImageError
import shutil
import uuid
from fastapi import UploadFile, File, Form
from search_engine import score_image
import ipaddress
import os
import socket
from urllib.parse import urljoin, urlparse
import httpx
from dotenv import load_dotenv
from search_providers.serpapi_images import (
    ExternalSearchError,
    search_google_images,
)
from index_images import build_image_index
from typing import Annotated
from uuid import UUID
from fastapi import BackgroundTasks
from mimetypes import guess_type

load_dotenv()

UPLOAD_ROOT = Path("temporary_uploads")
UPLOAD_ROOT.mkdir(parents=True, exist_ok=True)
IMAGE_DIR = Path("static/images")
CONVERTED_DIR = Path("static/converted")
CONVERTED_DIR.mkdir(parents=True, exist_ok=True)
UPLOAD_DIR = Path("static/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
ONLINE_UPLOAD_DIR = Path("static/uploads/online")
ONLINE_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

SUPPORTED_OUTPUTS = {"png", "jpg", "jpeg", "webp", "ico", "pdf"}
IMAGE_OUTPUT_FORMATS = {
    "png",
    "jpg",
    "jpeg",
    "webp",
    "ico",
    "pdf",
}

ALLOWED_REMOTE_IMAGE_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/gif": ".gif",
    "image/x-icon": ".ico",
    "image/vnd.microsoft.icon": ".ico",
}

MAX_REMOTE_IMAGE_SIZE = 15 * 1024 * 1024
MAX_REDIRECTS = 3

MAX_FILES = 250
MAX_FILE_SIZE = 10 * 1024 * 1024
MAX_TOTAL_SIZE = 200 * 1024 * 1024

ALLOWED_IMAGE_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
    "image/gif",
    "image/bmp",
    "image/tiff",
    "image/x-icon",
}

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "https://interactive-algorithm-visualizer-im.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class KMPRequest(BaseModel):
    text: str
    pattern: str

class OpenFileRequest(BaseModel):
    filepath: str

class ConvertOnlineImageRequest(BaseModel):
    image_url: str
    output_format: str

class UploadedImageConversionRequest(BaseModel):
    session_id: str
    relative_path: str
    output_format: str

@app.get("/")
def root():
    return {"message": "Algorithm Visualizer API is running"}

@app.post("/kmp")
def run_kmp(request: KMPRequest):
    return {
        "steps": kmp_steps(request.text, request.pattern)
    }

app.mount("/images", StaticFiles(directory="static/images"), name="images")

@app.get(
    "/uploaded-images/{session_id}/{relative_path:path}"
)
def preview_uploaded_image(
    session_id: str,
    relative_path: str,
):
    safe_session_id = validate_session_id(session_id)
    safe_relative_path = sanitize_relative_path(relative_path)

    files_directory = (
        UPLOAD_ROOT
        / safe_session_id
        / "files"
    ).resolve()

    file_path = (
        files_directory
        / safe_relative_path
    ).resolve()

    try:
        file_path.relative_to(files_directory)
    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail="Invalid image path.",
        ) from error

    if not file_path.is_file():
        raise HTTPException(
            status_code=404,
            detail="Image not found.",
        )

    return FileResponse(file_path)

@app.get("/search")
def search_images(
    q: str,
    session_id: str,
):
    safe_session_id = validate_session_id(session_id)

    index_path = (
        UPLOAD_ROOT
        / safe_session_id
        / "images.json"
    )

    if not index_path.exists():
        raise HTTPException(
            status_code=404,
            detail=(
                "No indexed folder was found. "
                "Upload a folder before searching."
            ),
        )

    with index_path.open("r", encoding="utf-8") as file:
        images = json.load(file)

    cleaned_query = q.strip()

    if not cleaned_query:
        return {
            "query": q,
            "count": 0,
            "results": [],
        }

    scored_results = []

    for image in images:
        score = score_image(image, cleaned_query)

        if score > 0:
            image_with_score = image.copy()
            image_with_score["score"] = score
            scored_results.append(image_with_score)

    scored_results.sort(
        key=lambda item: item["score"],
        reverse=True,
    )

    return {
        "query": cleaned_query,
        "count": len(scored_results),
        "results": scored_results,
    }

@app.get("/search-online")
async def search_online_images(
    q: str = Query(..., min_length=1, max_length=200),
    page: int = Query(0, ge=0, le=99),
):
    try:
        results = await search_google_images(
            query=q,
            page=page,
        )

    except ExternalSearchError as error:
        raise HTTPException(
            status_code=502,
            detail=str(error),
        ) from error

    return {
        "query": q,
        "source": "serpapi",
        "page": page,
        "has_previous": page > 0,
        "has_next": len(results) > 0 and page < 99,
        "count": len(results),
        "results": results,
    }

@app.get("/preview-online")
async def preview_online_image(
    url: str,
    background_tasks: BackgroundTasks,
):
    temporary_path: Path | None = None

    try:
        # Download using the existing protected downloader
        temporary_path = await download_online_image(url)

        # Confirm that the downloaded resource is really an image
        verify_image_file(temporary_path)

        # Determine the actual image format
        with Image.open(temporary_path) as image:
            image_format = image.format

        media_types = {
            "JPEG": "image/jpeg",
            "PNG": "image/png",
            "WEBP": "image/webp",
            "GIF": "image/gif",
            "BMP": "image/bmp",
            "TIFF": "image/tiff",
            "ICO": "image/x-icon",
        }

        media_type = media_types.get(
            image_format,
            "application/octet-stream",
        )

        # Delete temp file AFTER FileResponse finishes
        background_tasks.add_task(
            temporary_path.unlink,
            missing_ok=True,
        )

        return FileResponse(
            path=temporary_path,
            media_type=media_type,
            headers={
                "Content-Disposition": "inline"
            },
            background=background_tasks,
        )

    except HTTPException:
        # If Railway cannot fetch the image,
        # let the user's browser try the original URL.
        return RedirectResponse(
            url=url,
            status_code=302,
        )

    except Exception:
        if temporary_path and temporary_path.exists():
            temporary_path.unlink(missing_ok=True)

        return RedirectResponse(
            url=url,
            status_code=302,
        )

def validate_public_host(url: str) -> None:
    parsed = urlparse(url)

    if parsed.scheme not in {"http", "https"}:
        raise HTTPException(
            status_code=400,
            detail="Only HTTP and HTTPS image URLs are allowed.",
        )

    if not parsed.hostname:
        raise HTTPException(
            status_code=400,
            detail="The image URL has no valid hostname.",
        )

    try:
        resolved_addresses = socket.getaddrinfo(
            parsed.hostname,
            parsed.port or 443,
        )
    except socket.gaierror as error:
        raise HTTPException(
            status_code=400,
            detail="The image hostname could not be resolved.",
        ) from error

    for resolved_address in resolved_addresses:
        address_text = resolved_address[4][0]
        address = ipaddress.ip_address(address_text)

        if (
            address.is_private
            or address.is_loopback
            or address.is_link_local
            or address.is_reserved
            or address.is_multicast
            or address.is_unspecified
        ):
            raise HTTPException(
                status_code=400,
                detail="Internal or private network URLs are not allowed.",
            )

async def download_online_image(image_url: str) -> Path:
    current_url = image_url
    temporary_path: Path | None = None

    try:
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(25.0),
            follow_redirects=False,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 LocalImageSearchPlatform/1.0"
                )
            },
        ) as client:

            for redirect_count in range(MAX_REDIRECTS + 1):
                validate_public_host(current_url)

                async with client.stream(
                    "GET",
                    current_url,
                ) as response:

                    if response.status_code in {
                        301,
                        302,
                        303,
                        307,
                        308,
                    }:
                        if redirect_count >= MAX_REDIRECTS:
                            raise HTTPException(
                                status_code=502,
                                detail="The image URL redirected too many times.",
                            )

                        location = response.headers.get("location")

                        if not location:
                            raise HTTPException(
                                status_code=502,
                                detail="The image host returned an invalid redirect.",
                            )

                        current_url = urljoin(current_url, location)
                        continue

                    response.raise_for_status()

                    content_type = (
                        response.headers
                        .get("content-type", "")
                        .split(";")[0]
                        .strip()
                        .lower()
                    )

                    if content_type not in ALLOWED_REMOTE_IMAGE_TYPES:
                        raise HTTPException(
                            status_code=400,
                            detail=(
                                "The remote resource is not a supported "
                                f"image type: {content_type or 'unknown'}."
                            ),
                        )

                    declared_length = response.headers.get(
                        "content-length"
                    )

                    if declared_length:
                        try:
                            declared_size = int(declared_length)
                        except ValueError:
                            declared_size = 0

                        if declared_size > MAX_REMOTE_IMAGE_SIZE:
                            raise HTTPException(
                                status_code=413,
                                detail="The remote image exceeds 15 MB.",
                            )

                    suffix = ALLOWED_REMOTE_IMAGE_TYPES[content_type]
                    temporary_path = (
                        ONLINE_UPLOAD_DIR
                        / f"{uuid.uuid4().hex}{suffix}"
                    )

                    downloaded_size = 0

                    with temporary_path.open("wb") as output_file:
                        async for chunk in response.aiter_bytes():
                            downloaded_size += len(chunk)

                            if downloaded_size > MAX_REMOTE_IMAGE_SIZE:
                                raise HTTPException(
                                    status_code=413,
                                    detail="The remote image exceeds 15 MB.",
                                )

                            output_file.write(chunk)

                    return temporary_path

        raise HTTPException(
            status_code=502,
            detail="The remote image could not be retrieved.",
        )

    except httpx.TimeoutException as error:
        raise HTTPException(
            status_code=504,
            detail="The remote image download timed out.",
        ) from error

    except httpx.HTTPStatusError as error:
        raise HTTPException(
            status_code=502,
            detail=(
                "The image host returned HTTP "
                f"{error.response.status_code}."
            ),
        ) from error

    except httpx.RequestError as error:
        raise HTTPException(
            status_code=502,
            detail="The image host could not be reached.",
        ) from error

    except Exception:
        if temporary_path and temporary_path.exists():
            temporary_path.unlink()

        raise

def verify_image_file(image_path: Path) -> None:
    try:
        with Image.open(image_path) as image:
            image.verify()

    except (UnidentifiedImageError, OSError) as error:
        raise HTTPException(
            status_code=400,
            detail="The downloaded resource is not a valid image.",
        ) from error

def convert_image_file(
    input_path: Path,
    output_format: str,
) -> Path:
    normalized_format = output_format.lower()

    if normalized_format not in IMAGE_OUTPUT_FORMATS:
        raise HTTPException(
            status_code=400,
            detail="Unsupported output image format.",
        )

    output_extension = (
        "jpg"
        if normalized_format == "jpeg"
        else normalized_format
    )

    output_filename = (
        f"{input_path.stem}_{uuid.uuid4().hex[:8]}"
        f".{output_extension}"
    )

    output_path = CONVERTED_DIR / output_filename

    try:
        with Image.open(input_path) as image:
            if normalized_format in {"jpg", "jpeg", "pdf"}:
                image = image.convert("RGB")

            save_format = normalized_format.upper()

            if normalized_format in {"jpg", "jpeg"}:
                save_format = "JPEG"

            image.save(output_path, save_format)

    except (UnidentifiedImageError, OSError, ValueError) as error:
        output_path.unlink(missing_ok=True)

        raise HTTPException(
            status_code=400,
            detail=f"Image conversion failed: {error}",
        ) from error

    return output_path

def validate_session_id(session_id: str) -> str:
    try:
        return str(UUID(session_id))
    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail="Invalid upload session ID.",
        ) from error


def sanitize_relative_path(relative_path: str) -> Path:
    normalized = relative_path.replace("\\", "/")
    path = Path(normalized)

    if path.is_absolute() or ".." in path.parts:
        raise HTTPException(
            status_code=400,
            detail="Invalid relative file path.",
        )

    safe_parts = [
        part
        for part in path.parts
        if part not in {"", ".", "/"}
    ]

    if not safe_parts:
        raise HTTPException(
            status_code=400,
            detail="Invalid uploaded filename.",
        )

    return Path(*safe_parts)

@app.post("/open-file")
def open_file(request: OpenFileRequest):

    subprocess.run(
        ["explorer", f"/select,{request.filepath}"]
    )

    return {"status": "success"}

@app.post("/convert-image")
def convert_image(request: UploadedImageConversionRequest):
    output_format = request.output_format.lower()

    # 1. Validate requested output format
    if output_format not in SUPPORTED_OUTPUTS:
        raise HTTPException(
            status_code=400,
            detail="Unsupported output format"
        )

    # 2. Validate session ID
    safe_session_id = validate_session_id(
        request.session_id
    )

    # 3. Validate relative image path
    safe_relative_path = sanitize_relative_path(
        request.relative_path
    )

    # 4. Locate image inside this user's upload session
    input_path = (
        UPLOAD_ROOT
        / safe_session_id
        / "files"
        / safe_relative_path
    )

    if not input_path.is_file():
        raise HTTPException(
            status_code=404,
            detail="Uploaded image not found."
        )

    # 5. Open image
    try:
        image = Image.open(input_path)
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Unable to open image."
        )

    # 6. Convert transparency safely for JPG/PDF
    if output_format in {"jpg", "jpeg", "pdf"}:
        image = image.convert("RGB")

    # 7. Generate unique output filename
    output_filename = (
        f"{input_path.stem}_"
        f"{uuid.uuid4().hex[:8]}."
        f"{output_format}"
    )

    output_path = CONVERTED_DIR / output_filename

    # 8. Determine Pillow format
    save_format = output_format.upper()

    if output_format in {"jpg", "jpeg"}:
        save_format = "JPEG"

    # 9. Save converted image
    try:
        image.save(output_path, save_format)
    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Image conversion failed."
        )
    finally:
        image.close()

    # 10. Return download URL
    return {
        "status": "success",
        "filename": output_filename,
        "download_url": f"/converted/{output_filename}"
    }

@app.post("/upload-convert")
def upload_convert_image(
    file: UploadFile = File(...),
    output_format: str = Form(...)
):
    output_format = output_format.lower()

    if output_format not in SUPPORTED_OUTPUTS:
        return {"error": "Unsupported output format"}

    original_suffix = Path(file.filename).suffix.lower()

    if original_suffix not in {".jpg", ".jpeg", ".png", ".webp", ".ico"}:
        return {"error": "Unsupported input image format"}

    safe_filename = f"{uuid.uuid4().hex}_{file.filename}"
    upload_path = UPLOAD_DIR / safe_filename

    with open(upload_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        image = Image.open(upload_path)

        if output_format in {"jpg", "jpeg", "pdf"}:
            image = image.convert("RGB")

        output_filename = f"{Path(file.filename).stem}_{uuid.uuid4().hex[:8]}.{output_format}"
        output_path = CONVERTED_DIR / output_filename

        save_format = output_format.upper()

        if output_format == "jpg":
            save_format = "JPEG"

        image.save(output_path, save_format)

    finally:
        if upload_path.exists():
            upload_path.unlink()

    return {
        "status": "success",
        "filename": output_filename,
        "download_url": f"/converted/{output_filename}"
    }

@app.post("/convert-online-image")
async def convert_online_image(
    request: ConvertOnlineImageRequest,
):
    output_format = request.output_format.lower()

    if output_format not in IMAGE_OUTPUT_FORMATS:
        raise HTTPException(
            status_code=400,
            detail="Unsupported output image format.",
        )

    temporary_path: Path | None = None

    try:
        temporary_path = await download_online_image(
            request.image_url
        )

        verify_image_file(temporary_path)

        output_path = convert_image_file(
            temporary_path,
            output_format,
        )

        return {
            "status": "success",
            "filename": output_path.name,
            "download_url": f"/converted/{output_path.name}",
        }

    finally:
        if temporary_path and temporary_path.exists():
            temporary_path.unlink()

@app.post("/upload-folder")
async def upload_folder(
    session_id: Annotated[str, Form()],
    files: Annotated[list[UploadFile], File()],
    relative_paths: Annotated[list[str], Form()],
):
    safe_session_id = validate_session_id(session_id)

    if len(files) != len(relative_paths):
        raise HTTPException(
            status_code=400,
            detail="Each uploaded file must include a relative path.",
        )

    if not files:
        raise HTTPException(
            status_code=400,
            detail="No files were uploaded.",
        )

    if len(files) > MAX_FILES:
        raise HTTPException(
            status_code=413,
            detail=f"A maximum of {MAX_FILES} images may be uploaded.",
        )

    session_directory = UPLOAD_ROOT / safe_session_id
    files_directory = session_directory / "files"
    index_path = session_directory / "images.json"

    if session_directory.exists():
        shutil.rmtree(session_directory)

    files_directory.mkdir(parents=True, exist_ok=True)

    total_size = 0
    saved_count = 0

    try:
        for uploaded_file, supplied_relative_path in zip(
            files,
            relative_paths,
        ):
            if uploaded_file.content_type not in ALLOWED_IMAGE_TYPES:
                continue

            safe_relative_path = sanitize_relative_path(
                supplied_relative_path
            )

            destination = files_directory / safe_relative_path
            destination.parent.mkdir(parents=True, exist_ok=True)

            file_size = 0

            with destination.open("wb") as output_file:
                while chunk := await uploaded_file.read(1024 * 1024):
                    file_size += len(chunk)
                    total_size += len(chunk)

                    if file_size > MAX_FILE_SIZE:
                        raise HTTPException(
                            status_code=413,
                            detail=(
                                f"{uploaded_file.filename} exceeds "
                                "the per-file size limit."
                            ),
                        )

                    if total_size > MAX_TOTAL_SIZE:
                        raise HTTPException(
                            status_code=413,
                            detail="The folder exceeds the total upload limit.",
                        )

                    output_file.write(chunk)

            saved_count += 1

        if saved_count == 0:
            raise HTTPException(
                status_code=400,
                detail="No supported image files were uploaded.",
            )

        indexed_records = build_image_index(
            image_directory=files_directory,
            output_file=index_path,
            preview_base_url=(
                f"/uploaded-images/{safe_session_id}"
            ),
        )

        return {
            "status": "success",
            "session_id": safe_session_id,
            "uploaded_count": saved_count,
            "indexed_count": len(indexed_records),
        }

    except Exception:
        if session_directory.exists():
            shutil.rmtree(session_directory)

        raise

    finally:
        for uploaded_file in files:
            await uploaded_file.close()

@app.delete("/uploaded-folder/{session_id}")
def delete_uploaded_folder(session_id: str):
    safe_session_id = validate_session_id(session_id)

    session_directory = (
        UPLOAD_ROOT
        / safe_session_id
    )

    if session_directory.exists():
        shutil.rmtree(session_directory)

    return {
        "status": "success",
        "removed": True,
    }

app.mount("/converted", StaticFiles(directory="static/converted"), name="converted")