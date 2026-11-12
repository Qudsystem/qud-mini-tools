from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np
from PIL import Image


def compress_to_webp(source: Path, destination: Path, max_size=(1280, 1280), quality: int = 78) -> None:
    with Image.open(source) as image:
        image = image.convert("RGB")
        image.thumbnail(max_size)
        image.save(destination, "WEBP", quality=quality, method=6)


def quality_metrics(path: Path) -> dict:
    image = cv2.imread(str(path))
    if image is None:
        return {"brightness": 0.0, "sharpness": 0.0, "acceptable": False}
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    brightness = float(np.mean(gray))
    sharpness = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    return {
        "brightness": round(brightness, 2),
        "sharpness": round(sharpness, 2),
        "acceptable": 35 <= brightness <= 225 and sharpness >= 18,
    }
