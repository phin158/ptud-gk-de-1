from flask import Flask, render_template, request, redirect, url_for, flash, session
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os
from flask_migrate import Migrate

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Cấu hình database SQLite
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'app.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Khởi tạo database và migrate
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# -----------------------
# Định nghĩa các Model
# -----------------------
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), default='user')  # 'user' hoặc 'admin'
    blocked = db.Column(db.Boolean, default=False)
    block_reason = db.Column(db.String(200), default='')
    posts = db.relationship('Post', backref='user', lazy=True, cascade="all, delete-orphan")

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=True)
    image_url = db.Column(db.String(255), nullable=True)
    author = db.Column(db.String(50), nullable=False)  # lưu username của tác giả
    date = db.Column(db.String(20), nullable=False)
    task = db.Column(db.String(50), nullable=False)    # trạng thái bài viết: "Chờ duyệt", "Đã đăng"
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=True)


class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    # Nếu cần mô tả category, thêm cột description
    # Mối quan hệ 1-n với Post
    posts = db.relationship('Post', backref='category', lazy=True)

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    date = db.Column(db.String(20), nullable=False)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)

    # Khai báo relationship
    user = db.relationship('User', backref='comments')
    post = db.relationship('Post', backref='comments')



# -----------------------
# Helpers
# -----------------------
def current_user():
    """Trả về đối tượng User của người dùng đang đăng nhập, hoặc None nếu chưa đăng nhập."""
    if 'user_id' in session:
        return User.query.get(session['user_id'])
    return None

# **QUAN TRỌNG**: Dùng context_processor để hàm current_user() sẵn sàng trong tất cả template
@app.context_processor
def inject_current_user():
    return dict(current_user=current_user)

@app.context_processor
def inject_categories():
    return dict(all_categories=Category.query.all())

# -----------------------
# Routes
# -----------------------

# Trang đăng ký
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        role = request.form.get('role', 'viewer')  # Lấy role từ form, mặc định viewer

        if not username or not password:
            flash("Vui lòng nhập đầy đủ thông tin!", "danger")
            return redirect(url_for('register'))
        
        if password != confirm_password:
            flash("Mật khẩu và xác nhận mật khẩu không khớp!", "danger")
            return redirect(url_for('register'))

        if User.query.filter_by(username=username).first():
            flash("Tên đăng nhập đã tồn tại!", "danger")
            return redirect(url_for('register'))

        hashed_pw = generate_password_hash(password)
        new_user = User(
            username=username,
            password=hashed_pw,
            role=role,  # gán role
            blocked=False,
            block_reason=""
        )
        db.session.add(new_user)
        db.session.commit()

        flash("Đăng ký thành công! Vui lòng đăng nhập.", "success")
        return redirect(url_for('login'))
    
    return render_template('register.html')


# Đăng nhập
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            if user.blocked:
                flash(f"Tài khoản của bạn đã bị khóa! Lý do: {user.block_reason}", "danger")
                return redirect(url_for('login'))

            session['user_id'] = user.id
            flash("Đăng nhập thành công!", "success")
            return redirect(url_for('index'))
        else:
            flash("Sai tên đăng nhập hoặc mật khẩu!", "danger")
            return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/category/<int:cat_id>')
def show_category(cat_id):
    category = Category.query.get_or_404(cat_id)
    posts = Post.query.filter_by(category_id=cat_id, task="Đã đăng").order_by(Post.id.desc()).all()

    # Có thể dùng chung template index.html, hoặc template riêng
    return render_template('index.html', posts=posts, page=1, total_pages=1, category_name=category.name)

@app.route('/admin/categories', methods=['GET', 'POST'])
def admin_categories():
    user = current_user()
    if not user or user.role != 'admin':
        flash("Bạn không có quyền truy cập!", "danger")
        return redirect(url_for('index'))

    if request.method == 'POST':
        new_cat_name = request.form.get('cat_name')
        if new_cat_name:
            cat = Category(name=new_cat_name)
            db.session.add(cat)
            db.session.commit()
            flash("Đã thêm danh mục!", "success")
        return redirect(url_for('admin_categories'))

    cats = Category.query.all()
    return render_template('admin_categories.html', cats=cats)


@app.route('/admin/edit_role/<username>', methods=['GET', 'POST'])
def edit_role(username):
    user = current_user()
    if not user or user.role != 'admin':
        flash("Bạn không có quyền truy cập!", "danger")
        return redirect(url_for('index'))

    target_user = User.query.filter_by(username=username).first()
    if not target_user:
        flash("Người dùng không tồn tại!", "danger")
        return redirect(url_for('admin_users'))

    if request.method == 'POST':
        new_role = request.form.get('role')
        if new_role not in ['viewer', 'collaborator', 'editor', 'admin']:
            flash("Role không hợp lệ!", "danger")
            return redirect(url_for('edit_role', username=username))

        target_user.role = new_role
        db.session.commit()
        flash(f"Đã cập nhật role cho user {username} thành {new_role}!", "success")
        return redirect(url_for('admin_users'))

    # GET => hiển thị form sửa role
    return render_template('edit_role.html', target_user=target_user)

@app.route('/edit_post/<int:post_id>', methods=['GET', 'POST'])
def edit_post(post_id):
    user = current_user()
    if not user:
        flash("Vui lòng đăng nhập!", "danger")
        return redirect(url_for('login'))

    post = Post.query.get_or_404(post_id)
    # Chỉ owner + collaborator + editor + admin => cho sửa
    if post.user_id != user.id:
        flash("Bạn không có quyền sửa bài này!", "danger")
        return redirect(url_for('index'))

    if user.role == 'viewer':
        flash("Viewer không có quyền sửa bài!", "danger")
        return redirect(url_for('index'))

    # collaborator, editor, admin => ok
    if request.method == 'POST':
        new_title = request.form.get('title')
        new_content = request.form.get('content')
        post.title = new_title
        post.content = new_content
        db.session.commit()
        flash("Đã sửa bài viết!", "success")
        return redirect(url_for('my_posts'))

    return render_template('edit_post.html', post=post)


# Đăng xuất
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash("Đăng xuất thành công!", "success")
    return redirect(url_for('login'))

# Trang chủ: hiển thị bài viết đã được duyệt (Đã đăng)
@app.route('/')
@app.route('/page/<int:page>')
def index(page=1):
    POSTS_PER_PAGE = 10
    # Lấy tất cả bài viết "Đã đăng"
    published_posts = Post.query.filter_by(task="Đã đăng").order_by(Post.id.desc()).all()

    total_posts = len(published_posts)
    total_pages = (total_posts // POSTS_PER_PAGE) + (1 if total_posts % POSTS_PER_PAGE else 0)

    # Nếu chưa có bài viết nào, tránh vòng lặp redirect
    if total_pages == 0:
        total_pages = 1

    if page < 1 or page > total_pages:
        flash('Trang không tồn tại!', 'danger')
        return redirect(url_for('index', page=1))

    start = (page - 1) * POSTS_PER_PAGE
    end = start + POSTS_PER_PAGE
    paginated_posts = published_posts[start:end]

    # Truyền posts, page, total_pages vào template
    return render_template('index.html', posts=paginated_posts, page=page, total_pages=total_pages)

# Trang chi tiết bài viết
@app.route('/post/<int:post_id>')
@app.route('/post/<int:post_id>', methods=['GET', 'POST'])
def post_detail(post_id):
    post = Post.query.get_or_404(post_id)
    if post.task != "Đã đăng":
        flash("Bài viết chưa được duyệt hoặc không tồn tại!", "danger")
        return redirect(url_for('index'))

    if request.method == 'POST':
        user = current_user()
        if not user:
            flash("Vui lòng đăng nhập để bình luận!", "danger")
            return redirect(url_for('login'))

        comment_content = request.form.get('comment')
        new_comment = Comment(
            content=comment_content,
            date=datetime.now().strftime("%Y-%m-%d %H:%M"),
            user_id=user.id,
            post_id=post.id
        )
        db.session.add(new_comment)
        db.session.commit()
        flash("Đã thêm bình luận!", "success")
        return redirect(url_for('post_detail', post_id=post.id))

    comments = Comment.query.filter_by(post_id=post.id).order_by(Comment.id.desc()).all()
    return render_template('post.html', post=post, comments=comments)


# Tạo bài viết mới (user thường)
@app.route('/create', methods=['GET', 'POST'])
def create_post():
    user = current_user()
    if not user:
        flash("Vui lòng đăng nhập để tạo bài viết!", "danger")
        return redirect(url_for('login'))

    # Nếu user.role == 'viewer' => không cho tạo (nếu bạn đang phân quyền)
    if user.role == 'viewer':
        flash("Tài khoản Viewer chỉ được xem bài, không được tạo!", "danger")
        return redirect(url_for('index'))

    # Lấy danh sách Category từ DB
    categories = Category.query.all()

    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        cat_id = request.form.get('category_id')  # Lấy giá trị từ form

        random_id = datetime.now().timestamp()
        new_post = Post(
            title=title,
            content=content,
            image_url=f"https://picsum.photos/300/200?random={random_id}",
            author=user.username,
            date=datetime.now().strftime("%Y-%m-%d"),
            task="Chờ duyệt",  # Bài viết mới cần admin duyệt
            user_id=user.id,
            category_id=cat_id  # GÁN DANH MỤC
        )
        db.session.add(new_post)
        db.session.commit()

        flash("Bài viết đã được gửi để duyệt!", "success")
        return redirect(url_for('index'))

    # Lần đầu GET => hiển thị form, kèm theo danh sách category
    return render_template('create_post.html', categories=categories)


# Trang quản lý bài viết của user (xem, xóa bài viết của chính mình)
@app.route('/my_posts', methods=['GET', 'POST'])
def my_posts():
    user = current_user()
    if not user:
        flash("Vui lòng đăng nhập để quản lý bài viết!", "danger")
        return redirect(url_for('login'))
    
    # Nếu user là viewer => không cho sửa/xóa
    # Nếu user là collaborator => cho sửa, KHÔNG xóa
    # Nếu user là editor => cho sửa, xóa
    if request.method == 'POST':
        if user.role == 'viewer':
            flash("Viewer không có quyền xóa bài!", "danger")
            return redirect(url_for('my_posts'))
        if user.role == 'collaborator':
            flash("Collaborator không có quyền xóa bài!", "danger")
            return redirect(url_for('my_posts'))
        
        # Chỉ editor (hoặc admin) mới đến được đây
        post_ids = request.form.getlist('post_ids')
        post_ids = [int(pid) for pid in post_ids]
        posts_to_delete = Post.query.filter(Post.id.in_(post_ids), Post.user_id == user.id).all()
        for post in posts_to_delete:
            db.session.delete(post)
        db.session.commit()
        flash("Đã xóa các bài viết được chọn!", "success")
        return redirect(url_for('my_posts'))

    user_posts = Post.query.filter_by(user_id=user.id).order_by(Post.id.desc()).all()
    return render_template('my_posts.html', posts=user_posts)


# Trang quản trị (Admin): Quản lý bài viết (Admin duyệt hoặc xóa bài viết)
@app.route('/admin')
def admin_panel():
    user = current_user()
    if not user or user.role != "admin":
        flash("Bạn không có quyền truy cập trang này!", "danger")
        return redirect(url_for('index'))

    all_posts = Post.query.order_by(Post.id.desc()).all()
    return render_template('admin.html', posts=all_posts)

# Trang quản lý user (Admin): Hiển thị danh sách user
@app.route('/admin/users')
def admin_users():
    user = current_user()
    if not user or user.role != "admin":
        flash("Bạn không có quyền truy cập trang này!", "danger")
        return redirect(url_for('index'))

    all_users = User.query.all()
    return render_template('admin_users.html', users=all_users)

# Duyệt hoặc xóa bài viết (Admin)
@app.route('/admin/update/<int:post_id>/<action>')
def update_post(post_id, action):
    user = current_user()
    if not user or user.role != "admin":
        flash("Bạn không có quyền thực hiện hành động này!", "danger")
        return redirect(url_for('index'))

    post = Post.query.get(post_id)
    if post:
        if action == 'approve':
            post.task = "Đã đăng"
            flash("Bài viết đã được duyệt!", "success")
        elif action == 'delete':
            db.session.delete(post)
            flash("Bài viết đã được xóa!", "success")
        db.session.commit()

    return redirect(url_for('admin_panel'))

# Reset mật khẩu (Admin) – đặt lại mật khẩu cho user
@app.route('/admin/reset_password/<username>')
def reset_password(username):
    user = current_user()
    if not user or user.role != "admin":
        flash("Bạn không có quyền thực hiện hành động này!", "danger")
        return redirect(url_for('index'))

    target_user = User.query.filter_by(username=username).first()
    if target_user:
        target_user.password = generate_password_hash("newpassword123")
        db.session.commit()
        flash(f"Mật khẩu của {username} đã được reset thành 'newpassword123'!", "success")
    else:
        flash("Người dùng không tồn tại!", "danger")
    return redirect(url_for('admin_users'))

# Khóa hoặc mở khóa user (Admin)
@app.route('/admin/block_user/<username>/<action>')
def block_user(username, action):
    user = current_user()
    if not user or user.role != "admin":
        flash("Bạn không có quyền thực hiện hành động này!", "danger")
        return redirect(url_for('index'))

    target_user = User.query.filter_by(username=username).first()
    if target_user:
        if action == "block":
            target_user.blocked = True
            target_user.block_reason = request.args.get('reason', 'Không có lý do')
            flash(f"Người dùng {username} đã bị khóa!", "success")
        elif action == "unblock":
            target_user.blocked = False
            target_user.block_reason = ""
            flash(f"Người dùng {username} đã được mở khóa!", "success")
        db.session.commit()
    else:
        flash("Người dùng không tồn tại!", "danger")

    return redirect(url_for('admin_users'))

# -----------------------
# Khởi tạo database và admin mặc định
# -----------------------
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        # Nếu chưa có admin mặc định, thêm admin với mật khẩu 'admin'
        if not User.query.filter_by(username="admin").first():
            admin_user = User(
                username="admin",
                password=generate_password_hash("admin"),
                role="admin",
                blocked=False,
                block_reason=""
            )
            db.session.add(admin_user)
            db.session.commit()
        
        if Category.query.count() == 0:
            cat1 = Category(name="Chuyện vui")
            cat2 = Category(name="Chuyện buồn")
            db.session.add_all([cat1, cat2])
            db.session.commit()
    app.run(debug=True, host="0.0.0.0", port=5000)
