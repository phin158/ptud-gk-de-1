from flask import Flask, render_template, request, redirect, url_for, flash, session
from datetime import datetime
import json
import os
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)
app.secret_key = 'your_secret_key'

#file lưu trữ 
USERS_FILE = 'users.json'
POSTS_FILE = 'posts.json'

# Dữ liệu giả lập 
initial_users = [
    {"username": "admin", "password": "admin123", "role": "admin", "blocked": False, "block_reason": ""},
    {"username": "user1", "password": "user123", "role": "user", "blocked": False, "block_reason": ""},
    {"username": "user2", "password": "user123", "role": "user", "blocked": True, "block_reason": "Vi phạm quy định"},
    {"username": "user3", "password": "user123", "role": "user", "blocked": False, "block_reason": ""},
    {"username": "user4", "password": "user123", "role": "user", "blocked": False, "block_reason": ""}
]

#crawl dữ liệu từ DEV Community
def crawl_dev_posts():
    base_url = "https://dev.to/t/programming"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    posts = []
    page = 1
    post_id = 1

    while len(posts) < 110:  # Cần 110 bài viết
        url = f"{base_url}?page={page}"
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')

            # Tìm tất cả 
            articles = soup.find_all('div', class_='crayons-article__main')
            if not articles:
                print(f"Không tìm thấy bài viết nào trên trang {page}. Dừng crawl.")
                break

            for article in articles:
                # Lấy tiêu đề
                title_tag = article.find('h2', class_='crayons-article__title')
                title = title_tag.text.strip() if title_tag else f"Bài viết {post_id}"

                # Lấy nội dung tóm tắt
                content_tag = article.find('p', class_='crayons-article__summary')
                content = content_tag.text.strip() if content_tag else f"Nội dung bài viết {post_id}..."

                # Lấy tác giả
                author_tag = article.find('a', class_='crayons-article__author')
                author = author_tag.text.strip() if author_tag else f"user{(post_id % 4) + 1}"

                # Lấy ngày 
                date_tag = article.find('time')
                date = date_tag['datetime'][:10] if date_tag and 'datetime' in date_tag.attrs else f"2025-03-{post_id:02d}"

                post = {
                    "id": post_id,
                    "title": title,
                    "content": content[:200] + "..." if len(content) > 200 else content,
                    "author": author,
                    "date": date,
                    "task": "Đã đăng"
                }
                posts.append(post)
                post_id += 1

                if len(posts) >= 110:
                    break

            print(f"Đã crawl {len(posts)} bài viết từ DEV Community (trang {page})...")
            page += 1

        except Exception as e:
            print(f"Lỗi khi crawl dữ liệu từ DEV Community (trang {page}): {e}")
            break

    
    while len(posts) < 110:
        post_id = len(posts) + 1
        post = {
            "id": post_id,
            "title": f"Bài viết {post_id}",
            "content": f"Nội dung bài viết {post_id}...",
            "author": f"user{(post_id % 4) + 1}",
            "date": f"2025-03-{post_id:02d}",
            "task": "Đã đăng"
        }
        posts.append(post)

    print(f"Tổng cộng crawl được {len(posts)} bài viết.")
    return posts

# Crawl dữ liệu 
initial_posts = crawl_dev_posts()

# Hàm đọc 
def load_data(file_path, default_data):
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if not data or not isinstance(data, list):
                    print(f"File {file_path} rỗng hoặc không hợp lệ, sử dụng dữ liệu mặc định.")
                    return default_data
                return data
        except Exception as e:
            print(f"Lỗi khi đọc file {file_path}: {e}")
            return default_data
    return default_data

# Hàm ghi 
def save_data(data, file_path):
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        print(f"Lỗi khi ghi file {file_path}: {e}")

# Khởi tạo 
users = load_data(USERS_FILE, initial_users)
posts = load_data(POSTS_FILE, initial_posts)

# Phân trang
POSTS_PER_PAGE = 10

# Trang đăng ký
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if any(user['username'] == username for user in users):
            flash('Tên đăng nhập đã tồn tại!', 'danger')
            return redirect(url_for('register'))
        
        new_user = {
            "username": username,
            "password": password,
            "role": "user",
            "blocked": False,
            "block_reason": ""
        }
        users.append(new_user)
        save_data(users, USERS_FILE)
        flash('Đăng ký thành công! Vui lòng đăng nhập.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

# đăng nhập
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = next((user for user in users if user['username'] == username and user['password'] == password), None)
        if user:
            if user['blocked']:
                flash(f'Tài khoản của bạn đã bị khóa! Lý do: {user["block_reason"]}', 'danger')
                return redirect(url_for('login'))
            session['user'] = user
            flash('Đăng nhập thành công!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Tên đăng nhập hoặc mật khẩu không đúng!', 'danger')
    return render_template('login.html')

# Đăng xuất
@app.route('/logout')
def logout():
    session.pop('user', None)
    flash('Đăng xuất thành công!', 'success')
    return redirect(url_for('login'))

# Trang chủ
@app.route('/')
@app.route('/page/<int:page>')
def index(page=1):
    published_posts = [post for post in posts if post['task'] == "Đã đăng"]
    total_posts = len(published_posts)
    total_pages = (total_posts // POSTS_PER_PAGE) + (1 if total_posts % POSTS_PER_PAGE else 0)
    
    # Debug
    print(f"Debug: Tổng số bài viết 'Đã đăng': {total_posts}, Tổng số trang: {total_pages}")

    if page < 1 or page > total_pages:
        flash('Trang không tồn tại!', 'danger')
        return redirect(url_for('index', page=1))
    
    start = (page - 1) * POSTS_PER_PAGE
    end = start + POSTS_PER_PAGE
    paginated_posts = published_posts[start:end]
    
    # Debug
    print(f"Debug: Hiển thị bài viết trên trang {page}: {[post['id'] for post in paginated_posts]}")

    return render_template('index.html', posts=paginated_posts, page=page, total_pages=total_pages)

# Trang chi tiết bài viết
@app.route('/post/<int:post_id>')
def post(post_id):
    post = next((post for post in posts if post['id'] == post_id), None)
    if post and post['task'] == "Đã đăng":
        return render_template('post.html', post=post)
    flash('Bài viết không tồn tại hoặc chưa được duyệt!', 'danger')
    return redirect(url_for('index'))

# Tạo bài viết mới
@app.route('/create', methods=['GET', 'POST'])
def create_post():
    if 'user' not in session:
        flash('Vui lòng đăng nhập để tạo bài viết!', 'danger')
        return redirect(url_for('login'))
    
    if session['user']['blocked']:
        flash(f'Tài khoản của bạn đã bị khóa! Lý do: {session["user"]["block_reason"]}', 'danger')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        new_post = {
            "id": len(posts) + 1,
            "title": title,
            "content": content,
            "author": session['user']['username'],
            "date": datetime.now().strftime("%Y-%m-%d"),
            "task": "Chờ duyệt"
        }
        posts.append(new_post)
        save_data(posts, POSTS_FILE)
        flash('Bài viết đã được gửi để duyệt!', 'success')
        return redirect(url_for('index'))
    
    return render_template('create_post.html')

# Trang quản lý bài viết của user
@app.route('/my_posts', methods=['GET', 'POST'])
def my_posts():
    if 'user' not in session:
        flash('Vui lòng đăng nhập để quản lý bài viết!', 'danger')
        return redirect(url_for('login'))
    
    if session['user']['blocked']:
        flash(f'Tài khoản của bạn đã bị khóa! Lý do: {session["user"]["block_reason"]}', 'danger')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        post_ids = request.form.getlist('post_ids')
        post_ids = [int(pid) for pid in post_ids]
        
        global posts
        posts = [post for post in posts if post['id'] not in post_ids or post['author'] != session['user']['username']]
        save_data(posts, POSTS_FILE)
        flash('Đã xóa các bài viết được chọn!', 'success')
        return redirect(url_for('my_posts'))
    
    user_posts = [post for post in posts if post['author'] == session['user']['username']]
    return render_template('my_posts.html', posts=user_posts)

# Trang quản trị (quản lý bài viết)
@app.route('/admin')
def admin():
    if 'user' not in session or session['user']['role'] != 'admin':
        flash('Bạn không có quyền truy cập trang này!', 'danger')
        return redirect(url_for('index'))
    
    return render_template('admin.html', posts=posts)

# Trang quản lý user
@app.route('/admin/users')
def admin_users():
    if 'user' not in session or session['user']['role'] != 'admin':
        flash('Bạn không có quyền truy cập trang này!', 'danger')
        return redirect(url_for('index'))
    
    return render_template('admin_users.html', users=users)

# Duyệt hoặc xóa bài viết (admin)
@app.route('/admin/update/<int:post_id>/<action>')
def update_post(post_id, action):
    if 'user' not in session or session['user']['role'] != 'admin':
        flash('Bạn không có quyền thực hiện hành động này!', 'danger')
        return redirect(url_for('index'))
    
    post = next((post for post in posts if post['id'] == post_id), None)
    if post:
        if action == 'approve':
            post['task'] = 'Đã đăng'
            flash('Bài viết đã được duyệt!', 'success')
        elif action == 'delete':
            posts.remove(post)
            flash('Bài viết đã được xóa!', 'success')
        save_data(posts, POSTS_FILE)
    
    return redirect(url_for('admin'))

# Reset mật khẩu (admin)
@app.route('/admin/reset_password/<username>')
def reset_password(username):
    if 'user' not in session or session['user']['role'] != 'admin':
        flash('Bạn không có quyền thực hiện hành động này!', 'danger')
        return redirect(url_for('index'))
    
    user = next((user for user in users if user['username'] == username), None)
    if user:
        user['password'] = 'newpassword123'
        flash(f'Mật khẩu của {username} đã được reset thành "newpassword123"!', 'success')
        save_data(users, USERS_FILE)
    else:
        flash('Người dùng không tồn tại!', 'danger')
    return redirect(url_for('admin_users'))

# Khóa hoặc mở khóa user (admin)
@app.route('/admin/block_user/<username>/<action>')
def block_user(username, action):
    if 'user' not in session or session['user']['role'] != 'admin':
        flash('Bạn không có quyền thực hiện hành động này!', 'danger')
        return redirect(url_for('index'))
    
    user = next((user for user in users if user['username'] == username), None)
    if user:
        if action == 'block':
            user['blocked'] = True
            user['block_reason'] = request.args.get('reason', 'Không có lý do')
            flash(f'Người dùng {username} đã bị khóa!', 'success')
        elif action == 'unblock':
            user['blocked'] = False
            user['block_reason'] = ""
            flash(f'Người dùng {username} đã được mở khóa!', 'success')
        save_data(users, USERS_FILE)
    else:
        flash('Người dùng không tồn tại!', 'danger')
    return redirect(url_for('admin_users'))

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=5000)
