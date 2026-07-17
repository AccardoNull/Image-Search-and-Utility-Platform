import json
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from fastapi.staticfiles import StaticFiles
from algorithms.kmp import kmp_steps, kmp_contains
from fastapi.middleware.cors import CORSMiddleware
import subprocess
from fastapi.responses import FileResponse
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

load_dotenv()

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

class ConvertImageRequest(BaseModel):
    filename: str
    output_format: str

class ConvertOnlineImageRequest(BaseModel):
    image_url: str
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

@app.get("/preview/{filename}")
def preview_image(filename: str):
    file_path = Path("static/images") / filename

    return FileResponse(
        file_path,
        media_type="image/webp" if filename.lower().endswith(".webp") else None,
        filename=filename,
        content_disposition_type="inline"
    )

@app.get("/search")
def search_images(q: str):
    with open("data/images.json", "r", encoding="utf-8") as file:
        images = json.load(file)

    scored_results = []

    for image in images:
        score = score_image(image, q)

        if score > 0:
            image_with_score = image.copy()
            image_with_score["score"] = score
            scored_results.append(image_with_score)

    scored_results.sort(key=lambda item: item["score"], reverse=True)
    return {
        "query": q,
        "count": len(scored_results),
        "results": scored_results
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

@app.post("/open-file")
def open_file(request: OpenFileRequest):

    subprocess.run(
        ["explorer", f"/select,{request.filepath}"]
    )

    return {"status": "success"}

@app.post("/convert-image")
def convert_image(request: ConvertImageRequest):
    output_format = request.output_format.lower()

    if output_format not in SUPPORTED_OUTPUTS:
        return {"error": "Unsupported output format"}

    input_path = IMAGE_DIR / request.filename

    if not input_path.exists():
        return {"error": "File does not exist"}

    image = Image.open(input_path)

    # Convert transparency safely for JPG/PDF
    if output_format in {"jpg", "jpeg", "pdf"}:
        image = image.convert("RGB")

    output_filename = f"{input_path.stem}_{uuid.uuid4().hex[:8]}.{output_format}"
    output_path = CONVERTED_DIR / output_filename

    save_format = output_format.upper()

    if output_format == "jpg":
        save_format = "JPEG"

    image.save(output_path, save_format)

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

app.mount("/converted", StaticFiles(directory="static/converted"), name="converted")