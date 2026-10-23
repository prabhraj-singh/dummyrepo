FROM python:3.12-slim

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY server.py .

# Use environment variable for port, default to 8000 if not set
ENV PORT=8000

EXPOSE 8000

# Run the MCP server
CMD ["python", "server.py"]