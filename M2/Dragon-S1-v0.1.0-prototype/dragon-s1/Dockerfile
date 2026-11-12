FROM python:3.11-slim

# Install system dependencies needed for some Python packages like psycopg2 and opencv
RUN apt-get update && apt-get install -y libpq-dev gcc libgl1-mesa-glx libglib2.0-0 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY server/requirements.txt ./server/requirements.txt
RUN pip install --no-cache-dir -r server/requirements.txt

COPY . .

WORKDIR /app/server
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
