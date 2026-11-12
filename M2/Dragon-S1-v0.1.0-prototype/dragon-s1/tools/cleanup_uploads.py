import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "server"))
from services.storage import cleanup_old_uploads
print(f"Removed {cleanup_old_uploads()} expired image(s).")
