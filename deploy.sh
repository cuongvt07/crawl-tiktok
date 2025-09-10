#!/bin/bash

# Script triển khai TiktokCrawler trên VPS
# Sử dụng: ./deploy.sh

# Kiểm tra Docker đã được cài đặt chưa
if ! [ -x "$(command -v docker)" ]; then
  echo 'Error: Docker không được cài đặt.' >&2
  echo 'Đang cài đặt Docker...'
  sudo apt update
  sudo apt install -y docker.io docker-compose-plugin
  sudo systemctl enable --now docker
fi

# Tạo thư mục downloads nếu chưa tồn tại
mkdir -p downloads
sudo chmod 777 downloads

# Dừng và xóa container cũ (nếu có)
docker compose down

# Xóa images cũ để tải phiên bản mới nhất
docker image prune -f

# Xây dựng và chạy container
docker compose up -d --build

# Kiểm tra trạng thái
echo "Đang kiểm tra trạng thái container..."
sleep 5
docker compose ps

echo "TiktokCrawler đã được triển khai thành công!"
echo "Bạn có thể truy cập tại: http://localhost:8080"
