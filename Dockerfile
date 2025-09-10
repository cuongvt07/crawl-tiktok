FROM python:3.10-slim

# Cài đặt các phụ thuộc hệ thống
RUN apt-get update && apt-get install -y \
    ffmpeg \
    wget \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Tạo người dùng không phải root để tăng bảo mật
RUN groupadd -r tiktokcrawler && useradd -r -g tiktokcrawler tiktokcrawler

# Thư mục làm việc trong container
WORKDIR /app

# Sao chép requirements trước để tận dụng cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir flask gunicorn

# Sao chép code
COPY setup_web.py .
COPY src/ ./src/
COPY pyproject.toml .
COPY web/ ./web/

# Cài đặt package
RUN pip install -e .

# Tạo thư mục downloads và thiết lập quyền
RUN mkdir -p /app/downloads && \
    mkdir -p /app/user_downloads && \
    chown -R tiktokcrawler:tiktokcrawler /app

# Chuyển sang user không phải root
USER tiktokcrawler

# Expose port cho web interface
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/ || exit 1

# Khởi chạy web interface với Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "web.app:app"]
RUN pip install -e .

# Chuyển sang người dùng không phải root
USER tiktokcrawler

# Port để chạy Flask
EXPOSE 8080

# Chạy ứng dụng web với gunicorn cho môi trường production
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "4", "--timeout", "120", "web.app:app"]
