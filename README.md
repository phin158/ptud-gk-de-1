# Phát triển ứng dụng

##  Thông tin cá nhân  
- **Họ tên**: Nguyễn Thanh Tường Vy  
- **Mã sinh viên**: 22708841

---

## 📌 Mô tả project  
Project giữa kỳ của em là một ứng dụng web xây dựng bằng **Flask**.  
Ứng dụng hỗ trợ các chức năng chính sau:

### 🚀 Chức năng chính  
- **Blog**: Cho phép người dùng viết bài, chỉnh sửa, xóa bài viết.  
- **Hệ thống bình luận**: Người dùng có thể bình luận dưới mỗi bài viết.  

## 🔑 Phân quyền người dùng  

Hệ thống hỗ trợ 3 loại quyền người dùng chính:

| Vai trò         | Xem | Chỉnh sửa | Xóa |  
|---------------|:--:|:---------:|:--:|  
| **Viewer**       | ✅ | ❌ | ❌ |  
| **Collaborator** | ✅ | ✅ | ❌ |  
| **Editor**       | ✅ | ✅ | ✅ |  

- **Quản trị viên**: Quản lý tất cả bài viết và người dùng.  
- **Hệ thống đăng nhập/đăng ký**: Xác thực bằng **Flask-Login**.  
- **Quản lý danh mục**: Phân loại bài viết theo danh mục.  
- **Giao diện thân thiện**: Xây dựng với **Jinja2 + Bootstrap**.    


---

## Hướng dẫn cài đặt 🔧

### **1️⃣ Yêu cầu hệ thống**  
Trước khi chạy project, hãy đảm bảo bạn đã cài đặt:  
- Python 3.x  
- Flask (`pip install flask`)  
- Git (để clone repo)  

### **2️⃣ Cài đặt & chạy ứng dụng**
**Bước 1: Clone repo từ GitHub**  
```bash
git clone https://github.com/phin158/ptud-gk-de-1/.git
cd flask-tiny-app
```
**Bước 2: Tạo môi trường ảo và cài đặt dependencies**  
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```
**Bước 3: Chạy ứng dụng**
```bash
python app.py
```
