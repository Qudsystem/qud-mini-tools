from pathlib import Path
from typing import Optional

from PIL import Image


def compress_image(source: Path, destination: Optional[Path] = None) -> Path:
    destination = destination or source.with_suffix(".webp")
    with Image.open(source) as image:
        image = image.convert("RGB")
        image.thumbnail((1280, 1280))
        image.save(destination, "WEBP", quality=78, method=6)
    return destination
