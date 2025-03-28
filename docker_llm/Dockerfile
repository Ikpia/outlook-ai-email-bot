FROM python:3.10-slim

# Recommended: install system dependencies for torch & transformers
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy files
COPY requirements.txt requirements.txt
COPY app.py app.py

# Install Python dependencies
# torch MUST be installed via pip or it won't work
RUN pip install --no-cache-dir torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu \
    && pip install --no-cache-dir -r requirements.txt

# Expose Flask port
EXPOSE 7860

# Launch
CMD ["gunicorn", "-w", "2", "-b", "0.0.0.0:7860", "app:app"]
