import json
from pathlib import Path
from typing import Any

SUPPORTED_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
    ".gif",
    ".bmp",
    ".tif",
    ".tiff",
    ".ico",
}


def build_image_index(
    image_directory: Path,
    output_file: Path,
    preview_base_url: str,
) -> list[dict[str, Any]]:
    image_directory = image_directory.resolve()
    records: list[dict[str, Any]] = []

    for file_path in image_directory.rglob("*"):
        if not file_path.is_file():
            continue

        extension = file_path.suffix.lower()

        if extension not in SUPPORTED_EXTENSIONS:
            continue

        relative_path = file_path.relative_to(image_directory).as_posix()

        record = {
            "id": len(records) + 1,
            "filename": file_path.name,
            "relative_path": relative_path,
            "filepath": relative_path,
            "extension": extension.lstrip("."),
            "size": file_path.stat().st_size,
            "url": f"{preview_base_url}/{relative_path}",
            "description": file_path.stem.replace("_", " ").replace("-", " "),
            "tags": create_tags(file_path),
        }

        records.append(record)

    output_file.parent.mkdir(parents=True, exist_ok=True)

    with output_file.open("w", encoding="utf-8") as file:
        json.dump(records, file, indent=2, ensure_ascii=False)

    return records


def create_tags(relative_path: str) -> list[str]:
    path = Path(relative_path)

    return sorted(set(
        path.stem
        .replace("_", " ")
        .replace("-", " ")
        .lower()
        .split()
    ))

if __name__ == "__main__":
    build_image_index(
        image_directory=Path("static/images"),
        output_file=Path("data/images.json"),
        preview_base_url="/images",
    )