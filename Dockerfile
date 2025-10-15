FROM --platform=linux/amd64 python:3.11-slim

WORKDIR /app

# Install uv for faster package installation
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy requirements file
COPY requirements.txt .

# Install dependencies using uv (much faster than pip)
RUN uv pip install --system -r requirements.txt

# Copy application code
COPY . .

CMD ["python", "main.py"]