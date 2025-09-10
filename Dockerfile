FROM python:3.10-slim

# Cài đặt các phụ thuộc hệ thống
RUN apt-get update && apt-get install -y \
    ffmpeg \
    wget \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Tạo user không phải root
RUN groupadd -r tiktokcrawler && useradd -r -g tiktokcrawler tiktokcrawler

# Thư mục làm việc
WORKDIR /app

# Copy requirements và cài đặt
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir flask gunicorn

# Copy code
COPY setup_web.py .
COPY src/ ./src/
COPY pyproject.toml .
COPY web/ ./web/

# Cài đặt package (editable mode)
RUN pip install -e .

# Tạo thư mục dữ liệu và gán quyền
RUN mkdir -p /app/downloads /app/user_downloads \
    && chown -R tiktokcrawler:tiktokcrawler /app

# Chuyển sang user non-root
USER tiktokcrawler

# Expose port 5000 (chạy cố định 5000 thôi, không cần 8080 nữa)
EXPOSE 5000

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/ || exit 1

# Chạy web bằng Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "--timeout", "120", "web.app:app"]
