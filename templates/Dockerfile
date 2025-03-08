# Sử dụng image Python chính thức
FROM python:3.10

# Đặt thư mục làm việc trong container
WORKDIR /app

# Sao chép toàn bộ project vào container
COPY . /app

# Cài đặt các dependencies từ requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Mở cổng 5000 cho ứng dụng Flask
EXPOSE 5000

# Chạy ứng dụng Flask
CMD ["python", "app.py"]
