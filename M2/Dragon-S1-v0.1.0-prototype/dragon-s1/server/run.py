import os
import uvicorn
from dotenv import load_dotenv
from pathlib import Path

# Load env from parent directory (since .env is in the root)
BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parent
load_dotenv(PROJECT_DIR / ".env")

if __name__ == "__main__":
    port_str = os.getenv("PORT", "3001")
    try:
        port = int(port_str)
    except ValueError:
        port = 3001
        
    print(f"Starting Dragon S1 Security Server on port {port}...")
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
