# Sử dụng Python làm image gốc
FROM python:3.9

# Đặt thư mục làm việc trong container
WORKDIR /app

# Sao chép toàn bộ mã nguồn vào container
COPY . .

# Cài đặt các dependencies từ requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Chạy ứng dụng Flask
CMD ["python", "app.py"]
