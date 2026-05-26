import base64
from flask import Flask, render_template, request, redirect, session, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from datetime import date, timedelta, datetime
from flask_login import UserMixin, LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
import os
from flask_session import Session
from flask_mail import Mail, Message
from flask_migrate import Migrate
import random
from dotenv import load_dotenv
from flask_wtf import CSRFProtect
from flask import jsonify
import uuid
import json

load_dotenv()

# Конфиги

app = Flask(__name__)  # Инициализация приложения
app.secret_key = os.getenv('SECRET_KEY')
manager = LoginManager(app)
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(
    days=31)  # Длительность сессии
app.config['SESSION_PERMANENT'] = True  # Сессия не исчезает после перезапуска
app.config['SESSION_TYPE'] = 'filesystem'  # Тип сессии
Session(app)  # Инициализация сессии
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///main.db'  # SQLAlchemy
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['AVATARS_FOLDER'] = 'static/avatars'
app.config['MAIL_SERVER'] = 'smtp.gmail.com'  # Сервер почты (Gmail)
app.config['MAIL_PORT'] = 587  # Порт почты (Gmail)
app.config['MAIL_USE_TLS'] = True  # Сертификаты безопасности
app.config['MAIL_USE_SSL'] = False  # Сертификаты безопасности
app.config['MAIL_USERNAME'] = 'nexusmcru@gmail.com'  # Имя почты
app.config['MAIL_PASSWORD'] = 'bugquvonzfttozus'  # Пароль приложения
# Чтобы не указывать отправителя
app.config['MAIL_DEFAULT_SENDER'] = 'nexusmcru@gmail.com'
db = SQLAlchemy(app)  # Инициализация дб
migrate = Migrate(app, db)
csrf = CSRFProtect(app)

# Инициализация почты

mail = Mail(app)

# Классы дб


class User(db.Model, UserMixin):  # Пользователи
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, unique=True)
    description = db.Column(
        db.Text, default="Пользователь поленился и не добавил инфу о себе :[")
    email = db.Column(db.Text, unique=True)
    edition = db.Column(db.String)
    hash_password = db.Column(db.String)
    avatar = db.Column(db.String)
    subscribers = db.Column(db.Integer, default=0)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    is_moderator = db.Column(db.Boolean, default=False)
    is_admin = db.Column(db.Boolean, default=False)
    is_checked = db.Column(db.Boolean, default=False)
    is_banned = db.Column(db.Boolean, default=False)
    exp = db.Column(db.Integer, default=0)
    level = db.Column(db.String, default='Новичок')
    clan = db.Column(db.Integer, nullable=True)
    friends = db.Column(db.JSON, nullable=True)
    banned_until = db.Column(db.DateTime, nullable=True)
    permanent_ban = db.Column(db.Boolean, nullable=True)
    ban_reason = db.Column(db.String(500), nullable=True)

    def __init__(self, username, email, hash_password, edition, is_moderator=None, is_admin=None, is_checked=None, is_banned=None, description=None):
        self.username = username
        self.description = description or "Пользователь поленился и не добавил инфу о себе :["
        self.email = email
        self.hash_password = hash_password
        self.edition = edition
        self.is_moderator = is_moderator or False
        self.is_admin = is_admin or False
        self.is_checked = is_checked or False
        self.is_banned = is_banned or False

    def __str__(self):
        return f"ID: {self.id}, Username: {self.username}, Email: {self.email}"


class Appeal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    moderator_id = db.Column(db.Integer, nullable=True)
    reason = db.Column(db.String)
    status = db.Column(db.String, default='active')
    time = db.Column(db.DateTime, default=datetime.utcnow)

    def __init__(self, user_id, reason, status, moderator_id=None):
        self.user_id = user_id
        self.reason = reason
        self.status = status
        self.moderator_id = moderator_id or False


class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    from_user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'))
    discuss_id = db.Column(db.Integer, db.ForeignKey(
        'discuss.id', name='fk_notification_discuss'))
    type = db.Column(db.String(50))
    message = db.Column(db.String(200))
    is_read = db.Column(db.Boolean, default=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    author = db.relationship('User', foreign_keys=[from_user_id], backref='notifications')

    def __init__(self, user_id, from_user_id, type, message, post_id=None, discuss_id=None):
        self.user_id = user_id
        self.from_user_id = from_user_id
        self.post_id = post_id or ''
        self.discuss_id = discuss_id or ''
        self.type = type
        self.message = message


class Email_cods(db.Model):  # Коды отправляемые на Email
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.Text)
    code = db.Column(db.String)
    is_activated = db.Column(db.Boolean, default=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)

    def __init__(self, email, code, is_activated):
        self.email = email
        self.code = code
        self.is_activated = is_activated

    def __str__(self):
        return f"ID: {self.id}, Username: {self.username}, Email: {self.email}"


class Comments(db.Model):  # Комментарии
    id = db.Column(db.Integer, primary_key=True)
    id_author = db.Column(db.Integer)
    id_post = db.Column(db.Integer)
    id_comment = db.Column(db.Integer)
    id_discuss = db.Column(db.Integer)
    comment = db.Column(db.Text)
    rating = db.Column(db.Integer, default=0)
    date = db.Column(db.DateTime, default=datetime.utcnow)

    def __init__(self, id_author, comment, id_comment=None, id_discuss=None, id_post=None):
        self.id_author = id_author
        self.id_post = id_post or ""
        self.id_discuss = id_discuss or ""
        self.id_comment = id_comment or ""
        self.comment = comment


class Likes(db.Model):  # Лайки
    id = db.Column(db.Integer, primary_key=True)
    id_author = db.Column(db.Integer, db.ForeignKey('user.id'))
    id_post = db.Column(db.Integer, db.ForeignKey('posts.id'))
    id_discuss = db.Column(db.Integer, db.ForeignKey(
        'discuss.id', name='fk_likes_discuss'))
    date = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (db.UniqueConstraint(
        'id_author', 'id_post', 'id_discuss', name='uq_likes_author_post_discuss'),)

    def __init__(self, id_author, id_post=None, id_discuss=None):
        self.id_author = id_author
        self.id_post = id_post
        self.id_discuss = id_discuss


class Dislikes(db.Model):  # Дизлайки
    id = db.Column(db.Integer, primary_key=True)
    id_author = db.Column(db.Integer, db.ForeignKey('user.id'))
    id_post = db.Column(db.Integer, db.ForeignKey('posts.id'))
    id_discuss = db.Column(db.Integer, db.ForeignKey(
        'discuss.id', name='fk_dislikes_discuss'))
    date = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (db.UniqueConstraint(
        'id_author', 'id_post', name='uq_dislikes_author_post'),)

    def __init__(self, id_author, id_post=None, id_discuss=None):
        self.id_author = id_author
        self.id_post = id_post or ''
        self.id_discuss = id_discuss or ''


class Views(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'))
    discuss_id = db.Column(db.Integer, db.ForeignKey('discuss.id'))
    user_id = db.Column(db.Integer, nullable=True)
    session_id = db.Column(db.String, nullable=True)
    viewed_at = db.Column(db.DateTime, default=datetime.utcnow)


class Posts(db.Model):  # Посты
    id = db.Column(db.Integer, primary_key=True)
    id_author = db.Column(db.Integer)
    title = db.Column(db.String)
    text = db.Column(db.Text)
    rating = db.Column(db.Integer, default=0)
    views = db.Column(db.Integer, default=0)
    deny_reason = db.Column(db.String, nullable=True)
    status = db.Column(db.Integer, default='on_moderating')
    categories = db.Column(db.JSON, default=[])
    type = db.Column(db.String)
    thumbnail = db.Column(db.String, nullable=True)
    images_names = db.Column(db.JSON, default=[])
    video_link = db.Column(db.String, nullable=True)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    is_news = db.Column(db.Boolean, default=False)
    official = db.Column(db.Boolean, default=False)
    file = db.Column(db.String, nullable=True)

    def __init__(self, id_author, title, text, views, status, type, images_names, is_news, video_link, thumbnail, file):
        self.id_author = id_author
        self.title = title
        self.text = text
        self.views = views
        self.status = status
        self.type = type
        self.images_name = images_names
        self.thumbnail = thumbnail
        self.video_link = video_link
        self.is_news = is_news or False
        self.file = file


class Discuss(db.Model):  # Посты
    id = db.Column(db.Integer, primary_key=True)
    id_author = db.Column(db.Integer)
    title = db.Column(db.String)
    text = db.Column(db.Text)
    rating = db.Column(db.Integer, default=0)
    views = db.Column(db.Integer, default=0)
    deny_reason = db.Column(db.String, nullable=True)
    status = db.Column(db.Integer, default='on_moderating')
    categories = db.Column(db.JSON, default=[])
    date = db.Column(db.DateTime, default=datetime.utcnow)

    def __init__(self, id_author, title, text, views, status, categories):
        self.id_author = id_author
        self.title = title
        self.text = text
        self.views = views
        self.status = status
        self.categories = categories

class Clans(db.Model):  # Кланы
    id = db.Column(db.Integer, primary_key=True)
    id_author = db.Column(db.Integer)
    name = db.Column(db.String)
    members = db.Column(db.JSON, nullable=False, default=[])
    description = db.Column(db.Text)
    rating = db.Column(db.Integer, default=0)
    views = db.Column(db.Integer, default=0)
    categories = db.Column(db.JSON, default=[])
    date = db.Column(db.DateTime, default=datetime.utcnow)

    def __init__(self, id_author, name, views, description, categories):
        self.id_author = id_author
        self.name = name
        self.description = description
        self.views = views
        self.categories = categories

# Для проверки файлов
ALLOWED_EXTENSIONS_IMAGES = {'png', 'jpg', 'jpeg', 'gif', 'webp'}  # Расширения файлов
ALLOWED_EXTENSIONS_ARCHIVES = {'zip', 'rar', '7z'}
MAX_FILE_SIZE = 16 * 1024 * 1024  # Размер файлов 16MB

def allowed_file(filename, allowed_set):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_set


def time_ago(date):
    now = datetime.utcnow()
    diff = now - date

    total_seconds = int(diff.total_seconds())

    if total_seconds < 60:
        return f"{total_seconds} секунд назад"
    elif total_seconds < 3600:
        minutes = total_seconds // 60
        return f"{minutes} минут назад"
    elif total_seconds < 86400:
        hours = total_seconds // 3600
        return f"{hours} часов назад"
    elif total_seconds < 2592000:
        days = total_seconds // 86400
        return f"{days} дней назад"
    else:
        return date.strftime("%d.%m.%Y")


def generate_code():
    return ''.join([str(random.randint(0, 9)) for _ in range(6)])

def file_upload(file, allowed_set):
    if not file or not file.filename:
        return None, 'Файл не выбран'

    if not allowed_file(file.filename, allowed_set):
        extensions_str = ", ".join(sorted(allowed_set))
        return None, f"Недопустимый формат файла! Разрешены: {extensions_str}"

    file.seek(0, 2)  # Перемещаемся в конец файла
    file_size = file.tell()
    file.seek(0)  # Возвращаемся в начало

    if file_size > MAX_FILE_SIZE:
        return None, f"Файл слишком большой! Максимум {MAX_FILE_SIZE // 1024 // 1024}MB"

    filename = secure_filename(file.filename)
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

    # Проверка на дубликаты имен
    if os.path.exists(file_path):
        name, ext = os.path.splitext(filename)
        counter = 1
        while os.path.exists(file_path):
            filename = f"{name}_{counter}{ext}"
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            counter += 1
    
    file.save(file_path)
    return filename, None

def multiple_file_upload(files):
    import os
    uploaded_files=[]
    errors=[]

    for file in files:
        if not file or not file.filename:
            continue
        
        if not allowed_file(file.filename, ALLOWED_EXTENSIONS_IMAGES):
            errors.append(f"{file.filename}: Недопустимый формат файла!")
            continue
        
        file.seek(0, 2)
        file_size = file.tell()
        file.seek(0)

        if file_size > MAX_FILE_SIZE:
            errors.append(f"{file.filename}: Слишком большой файл!")
            continue
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

        if os.path.exists(file_path):
            name, ext = os.path.splitext(filename)
            counter = 1
            while os.path.exists(file_path):
                filename = f"{name}_{counter}{ext}"
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                counter += 1
        
        file.save(file_path)
        uploaded_files.append(filename)

    return uploaded_files, errors


@app.route('/notifications', methods=['POST', 'GET'])
def notifications():
    user = current_user
    id = user.id
    notifications = Notification.query.filter_by(user_id=id).limit(3).all()
    if notifications:
        return render_template('notifications.html', notifications=notifications)
    return render_template('notifications.html')


@app.route('/mark_notice', methods=['POST'])
def mark_notice():
    if not current_user.is_authenticated:
        return jsonify({'success': False, 'message': 'Не авторизован'}), 401

    try:
        Notification.query.filter_by(
            user_id=current_user.id, is_read=False).update({'is_read': True})
        db.session.commit()

        return jsonify({'success': True, 'message': 'Прочитано'})

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/send_email/<verifyType>', methods=['POST'])
def send_email(verifyType):
    if request.method == 'POST':

        # Получение данных из формы для их сохранения
        email = request.form.get('email', '')
        username = request.form.get('username', '')
        password = request.form.get('password', '')
        edition = request.form.get('version', 'java')

        if not email:  # Если нет почты
            print("Почта не введена!")
            flash('Введите email', 'danger')
            return redirect(url_for('register' if verifyType == 'register' else 'login'))

        # Для логина проверяем существование пользователя
        if verifyType == 'login':
            user = User.query.filter_by(email=email).first()
            if user is None:
                flash('Такого пользователя не существует', 'danger')
                return redirect("/login")

        # Для регистрации проверяем, не занят ли email
        elif verifyType == 'register':
            user = User.query.filter_by(email=email).first()
            if user:
                flash('Этот email уже зарегистрирован', 'danger')
                return redirect("/register")

        # Добавление данных в сессию
        session["email"] = email
        session["username"] = username
        session["password"] = password
        session["edition"] = edition

        # Удаляем старые коды для этого email
        old_codes = Email_cods.query.filter_by(email=email).all()
        for old_code in old_codes:
            db.session.delete(old_code)

        # Генерация нового кода
        code = generate_code()

        new_code = Email_cods(email, code, False)
        db.session.add(new_code)
        db.session.commit()

        code_verify = Email_cods.query.filter_by(
            email=email, is_activated=True).first()

        if verifyType == 'login':
            if check_password_hash(user.hash_password, password):
                return 'Пароль введен верно.', 204
            else:
                flash('Неверный пароль!')
                return redirect(url_for('login'))

        if code_verify:
            db.session.delete(code_verify)
            db.session.commit()
        else:
            db.session.add(new_code)  # Добавление кода в бд
            db.session.commit()  # Подтверждение

        if verifyType == 'login':
            user = User.query.filter_by(email=email).first()
            username = user.username if user else "пользователь"
            msg = Message(
                subject="Nexus MC: Код подтверждения",
                recipients=[email],
                body=f'''Привет, {username}.
        Мы получили запрос на вход в ваш аккаунт
        Подтвердите свою Электронную почту введя код снизу в поле ввода.
        {code}'''
            )  # Шаблон для Email
        elif verifyType == 'register':
            msg = Message(
                subject="Nexus MC: Код подтверждения",
                recipients=[email],
                body=f'''Привет, {username}.
        Вы регистрируетесь на Nexus MC!
        Подтвердите свою Электронную почту введя код снизу в поле ввода.
        {code}''')  # Шаблон для Email

        mail.send(msg)  # Отправление Email

        return '', 204


@manager.user_loader
def load_user(user_id):
    return db.session.get(User, user_id)


@app.context_processor
def inject_helpers():
    return dict(time_ago=time_ago)


@app.context_processor
def inject_user():
    user = current_user

    if user.is_authenticated:
        if user.is_banned:
            logout_user()
            return {}

        notifications = Notification.query.filter_by(
            user_id=user.id,
            is_read=False
        ).order_by(Notification.date.desc()).limit(3).all()

        for notice in notifications:
            notice.author = User.query.get(notice.from_user_id)

        return {
            'user': user,
            'notifications': notifications,
            'notifications_count': len(notifications)
        }

    return {}


@app.route('/')
def index():
    posts = Posts.query.order_by(Posts.views.desc()).all()
    comments_len = 0
    if posts:
        for post in posts:
            comment = Comments.query.filter_by(id_post=post.id).all()
            post.author = User.query.get(post.id_author)
            post.comments_len = len(comment)

            if current_user.is_authenticated:
                like = Likes.query.filter_by(
                    id_author=current_user.id, id_post=post.id).first()
                post.liked = like is not None
            else:
                post.liked = False
    return render_template("index.html", posts=posts)

@app.route('/news')
def news():
    posts = Posts.query.order_by(Posts.views.desc()).all()
    comments_len = 0
    if posts:
        for post in posts:
            comment = Comments.query.filter_by(id_post=post.id).all()
            post.author = User.query.get(post.id_author)
            post.comments_len = len(comment)

            if current_user.is_authenticated:
                like = Likes.query.filter_by(
                    id_author=current_user.id, id_post=post.id).first()
                post.liked = like is not None
            else:
                post.liked = False
    return render_template("news_nexus.html", posts=posts)

@app.route('/moderate/<moderateType>')
def moderate(moderateType):
    if current_user.is_moderator:
        posts = Posts.query.filter_by(status='on_moderating').all()
        discusses = Discuss.query.filter_by(status='on_moderating').all()

        for post in posts:
            post.author = User.query.get(post.id_author)

        for discuss in discusses:
            discuss.author = User.query.get(discuss.id_author)

        return render_template("moderate_posts.html", posts=posts, discusses=discusses, moderateType=moderateType)

    else:
        return redirect(url_for('index'))


@app.route('/news_nexus')
def news_nexus():
    return render_template("news_nexus.html")


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == "GET":
        # Проверяем, есть ли email в сессии
        email = session.get("email", "")
        return render_template("register.html", email=email)

    # Проверяем, что все необходимые данные есть в сессии
    username = session.get("username")
    email = session.get("email")
    password = session.get("password")
    edition = session.get("edition")

    # Если каких-то данных нет, перенаправляем на регистрацию
    if not all([username, email, password, edition]):
        flash("Пожалуйста, заполните форму регистрации сначала", 'danger')
        return redirect(url_for('register'))

    print(email, username)

    # Получение проверочного кода из формы в модальном окне
    verify_code = request.form.get('verify_code')

    user = User.query.filter_by(username=username, email=email).first()

    if user:
        flash('Почта или имя пользователя уже используется!', 'danger')
        return redirect("/register")

    elif len(username) < 4:
        flash("Зачем в коде лазишь?!", 'danger')
        return redirect(url_for('register'))

    else:
        code_entry = Email_cods.query.filter_by(email=email).first()
        print(code_entry.code, verify_code)

        if code_entry:
            code = code_entry.code
        else:
            flash('Код не найден или уже активирован!', 'danger')
            return redirect("/register")

        if code == verify_code:
            hash_pwd = generate_password_hash(password)
            new_user = User(username, email, hash_pwd, edition)
            db.session.add(new_user)
            db.session.commit()
            user = db.session.get(User, new_user.id)
            login_user(user)
            session.permanent = True
            code_entry.is_activated = True
            db.session.commit()
            flash("Регистрация прошла успешно!", 'success')
            return redirect("/")

        else:
            flash("Неверный код!", 'danger')
            return redirect("/register")


@app.route('/login', methods=['GET', 'POST'])
def login():

    # Берем данные из сессии
    username = session.get("username")
    email = session.get("email")
    password = session.get("password")
    edition = session.get("edition")

    # Получение проверочного кода из формы в модальном окне
    verify_code = request.form.get('verify_code')

    if request.method == "GET":

        if current_user.is_authenticated:  # Проверка на авторизацию
            flash("Вы уже авторизованы", 'warning')
            return redirect("/")

        return render_template("login.html", email=email, password=password)

    if not email or not password:
        flash('Пожалуйста, введите email и пароль', 'danger')
        return redirect("/login")

    user = User.query.filter_by(email=email).first()

    if user is None:
        print("Пользователь не найден!")
        flash('Такого пользователя не существует', 'danger')
        return redirect("/login")
    else:
        code_entry = Email_cods.query.filter_by(email=email).first()
        print(code_entry.code, verify_code)

        if code_entry:
            code = code_entry.code
        else:
            flash('Код не найден или уже активирован!', 'danger')
            return redirect("/login")
    if code == verify_code:
        login_user(user)
        session.permanent = True
        code_entry.is_activated = True
        db.session.commit()
        flash("Успешный вход!", 'success')
        return redirect("/")

    else:
        flash("Неверный код!", 'danger')
        return redirect("/login")

    flash("Неверный логин или пароль!", 'danger')
    return render_template("login.html", email=email, password=password)


@app.route('/forgot_password')
def forgot_password():
    return render_template('forgot_password.html')


@app.route('/logout')
def logout():
    logout_user()
    return redirect("/")


@app.route('/user/<int:id>', methods=['GET', 'POST'])
def user(id):

    avatar = request.files.get('avatar')
    user = User.query.filter_by(id=id).first()
    if user.friends:
        if current_user.id in user.friends:
            user.is_friend = True
        else: 
            user.is_friend = False
    else:
        pass
    status = "Пользователь"
    if user:
        friends_users = User.query.filter(User.id.in_(user.friends)).all()
        if user.is_moderator:
            status = "Модератор"
        elif user.is_checked:
            status = "Проверенный"
        elif user.username == "Whyiok" or user.username == "Nexus":
            status = "Админ"
    else:
        flash('Пользователь не найден!', 'danger')
        return redirect(url_for('index'))

    posts = Posts.query.order_by(Posts.views.desc()).all()
    comments_len = 0
    if posts:
        for post in posts:
            comment = Comments.query.filter_by(id_post=post.id).all()
            post.author = User.query.get(post.id_author)
            comments_len = len(comment)

    return render_template("account.html", user=user, status=status, posts=posts, comments_len=comments_len, friends_users=friends_users)

@app.route('/add_friend/<int:id>', methods=['GET', 'POST'])
def add_friend(id):
    user = User.query.get(id)

    user_friends = list(user.friends) if user.friends else []
    current_user_friends = list(current_user.friends) if current_user.friends else []

    if current_user.id not in user_friends:
        user_friends.append(current_user.id)
    
    if user.id not in current_user_friends:
        current_user_friends.append(current_user.id)
    
    user.friends = user_friends
    current_user.friends = current_user_friends

    db.session.commit()
    return redirect(url_for('user', id=id))


@app.route('/update_user', methods=['GET', 'POST'])
def update_user():
    if request.method == 'POST':
        avatar = request.files.get('avatar')
        email = request.form.get('email')
        old_pass = request.form.get('old_pass')
        new_pass = request.form.get('new_pass')
        new_pass_repeat = request.form.get('new_pass_repeat')
        user = current_user
        updated = False
        id = current_user.id

        if email and email != '' and email != user.email:
            user.email = email
            updated = True
            flash('Email обновлен!', 'success')

        if old_pass and new_pass and new_pass_repeat:
            if check_password_hash(user.hash_password, old_pass):
                if new_pass == new_pass_repeat:
                    user.hash_password = generate_password_hash(new_pass)
                    updated = True
                    flash("Пароль сменён!", 'success')
                else:
                    flash("Пароли не совпадают!", 'danger')
            else:
                flash("Старый пароль неверный!", 'danger')

        if avatar and avatar.filename:

            if not allowed_file(avatar.filename, ALLOWED_EXTENSIONS_IMAGES):
                flash(
                    "Недопустимый формат файла! Разрешены: gif, png, jpg, jpeg", 'danger')
                return redirect(url_for('user', id=id))

            # Проверка размера файла
            avatar.seek(0, os.SEEK_END)
            file_size = avatar.tell()
            avatar.seek(0)  # Вернуть указатель в начало

            if file_size > MAX_FILE_SIZE:
                flash(
                    f"Файл слишком большой! Максимум {MAX_FILE_SIZE // 1024 // 1024}MB", 'danger')
                return redirect(url_for('user', id=id))

            filename = secure_filename(avatar.filename)
            filepath = os.path.join(app.config['AVATARS_FOLDER'], filename)

            avatar.save(filepath)
            flash("Аватар добавлен!", "success")
            user.avatar = filename
            updated = True

        if updated:
            db.session.commit()

    return redirect(url_for('user', id=id))


@app.route('/del_account', methods=['GET', 'POST'])
def del_account():

    db.session.delete(current_user)
    db.session.commit()
    flash("Аккаунт удален!", 'success')
    return redirect("/")


@app.route('/comment/<contentType>/<int:id>', methods=['GET', 'POST'])
def comment(contentType, id):
    if current_user.is_authenticated:
        if request.method == 'POST':
            if contentType == 'post':
                text = request.form.get('text')
                post_id = request.form.get('post_id')
                post = Posts.query.get(post_id)
                if len(text) > 500:
                    flash("Недопустимый запрос.", 'danger')
                    return redirect(url_for("index"))
                new_notice = Notification(user_id=post.id_author, from_user_id=current_user.id,
                                          post_id=post.id, type="reply", message="прокомментировал ваш пост!")
                new_comment = Comments(
                    id_author=current_user.id, id_post=post_id, comment=text)
                db.session.add(new_notice)
                db.session.add(new_comment)
                db.session.commit()
                flash("Комментарий добавлен!", 'success')
                return redirect(url_for('post', id=id))

            elif contentType == 'discuss':
                text = request.form.get('text')
                discuss_id = request.form.get('discuss_id')
                discuss = Discuss.query.get(discuss_id)
                if len(text) > 500:
                    flash("Недопустимый запрос.", 'danger')
                    return redirect(url_for('forum'))
                new_notice = Notification(user_id=discuss.id_author, from_user_id=current_user.id,
                                          discuss_id=discuss.id, type="reply", message="ответил на вашу дискуссию!")
                new_comment = Comments(
                    id_author=current_user.id, id_discuss=discuss_id, comment=text)
                db.session.add(new_notice)
                db.session.add(new_comment)
                db.session.commit()
                flash("Ответ добавлен!", 'success')
                return redirect(url_for('discuss', id=id))
            else:
                flash("Пост или Дискуссия не найдены!", 'danger')
                return redirect(url_for('index'))
    else:
        flash("Пожалуйста, войдите в аккаунт!", 'danger')
        return redirect(url_for('login'))


@app.route('/forum', methods=['GET', 'POST'])
def forum():
    page = request.args.get('page', 1, type=int)
    per_page = 25
    pagination = Discuss.query.order_by(Discuss.id.desc()).paginate(
        page=page,
        per_page=per_page,
        error_out=False
    )
    discusses = pagination.items
    comments_len = 0
    if len(discusses) != 0:
        for discuss in discusses:
            discuss.author = User.query.get(discuss.id_author)
            comment = Comments.query.filter_by(id_discuss=discuss.id).all()

            if comment or len(comment) != 0:
                comments_len = len(comment)

            if current_user.is_authenticated:
                discuss.liked = Likes.query.filter_by(
                    id_author=current_user.id,
                    id_discuss=discuss.id
                ).first() is not None
            else:
                discuss.liked = False

    return render_template("forum.html", discusses=discusses, pagination=pagination, comments_len=comments_len)


@app.route('/add_post/<post_type>', methods=['GET', 'POST'])
def add_post(post_type):
    if not current_user.is_authenticated:
        flash("Войдите в аккаунт!", 'danger')
        return redirect(url_for('login'))
    if not current_user.is_authenticated:
        flash("Войдите в аккаунт!", 'danger')
        return redirect(url_for('login'))
        
    if current_user.is_banned:
        flash('Вы забанены!', 'danger')
        return redirect(url_for('index'))

    true_types = ['article', 'server_java', 'server_bedrock', 'texture_pack', 'news', 'mod']

    if post_type not in true_types:
        flash("Недопустимый тип поста.", 'danger')
        return redirect(url_for('index'))

    if request.method == 'POST':
        thumbnail = request.files.get('thumbnail')
        title = request.form.get('title')
        text = request.form.get('text')
        categories = request.form.get('categories')
        file = request.files.get('file')
        images = request.files.getlist('images[]')
        video_link = request.form.get('video_link')
        id_author = current_user.id
        is_news = True
        views = 0

        images_names = []
        thumbnail_filename = None
        file_filename = None

        if not title or not text:
            flash("Недопустимый запрос.", 'danger')
            return redirect(url_for('edit', editType=editType, id=id))

        if current_user.is_banned:
            flash('Вы забанены!', 'success')
            return redirect(url_for('index'))
        
        uploaded_files, errors = multiple_file_upload(images)
        if errors:
            for error in errors:
                flash(error, 'danger')
                print(f"Ошибка: {error}")

        images_names = uploaded_files

        if uploaded_files:
            flash(f"Загружено {len(uploaded_files)}", 'success')
            print(f"Загружены: {', '.join(uploaded_files)}")
        
        if thumbnail and thumbnail.filename:
            filename, error = file_upload(thumbnail, ALLOWED_EXTENSIONS_IMAGES)
            if error:
                flash(error, 'danger')
                return redirect(url_for('add_post', post_type=post_type))
            thumbnail_filename = filename
            flash("Картинка добавлена!", "success")

        if file and file.filename:
            filename, error = file_upload(file, ALLOWED_EXTENSIONS_ARCHIVES)
            if error:
                flash(error, 'danger')
                return redirect(url_for('add_post', post_type=post_type))
            file_filename = filename
            flash("Файл добавлен!", "success")
        print(file_filename)
        try:
            from sqlalchemy.orm.attributes import flag_modified
            import json


            new_post = Posts(
                id_author=id_author,
                title=title,
                text=text,
                views=views,
                status='on_moderating',
                type=post_type,
                thumbnail=thumbnail_filename,
                video_link=video_link,
                is_news=is_news,
                images_names=[],
                file=file_filename
            )

            new_post.images_names = images_names
            flag_modified(new_post, 'images_names')

            db.session.add(new_post)
            db.session.commit()
            
            flash("Пост успешно добавлен!", 'success')
            return redirect(url_for('index'))

        except Exception as e:
            print(f"Ошибка: {e}")
            db.session.rollback()
            flash(f"Ошибка: {str(e)}", 'danger')
            return redirect(url_for('add_post', post_type=post_type))

    return render_template("add_post.html", post_type=post_type)

import re

@app.template_filter('youtube_embed')
def youtube_embed_filter(url):
    if not url:
        return ''
    # Регулярное выражение для поиска ID видео в разных типах ссылок YouTube
    reg = r'(https?://)?(www\.)?(youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)([^?&\s]+)'
    match = re.search(reg, url)
    if match:
        video_id = match.group(4)
        return f"https://www.youtube.com/embed/{video_id}"
    return url


@app.route('/accept/<contentType>/<int:id>', methods=['GET', 'POST'])
def accept(contentType, id):
    if contentType == 'post':
        post = Posts.query.filter_by(id=id).first()
        post.status = 'moderated'
        db.session.commit()
        new_notice = Notification(user_id=post.id_author, from_user_id=current_user.id,
                                  post_id=post.id, type="post_accepted", message="Ваш пост был принят!")
        db.session.add(new_notice)
        db.session.commit()
        flash('Пост успешно одобрен!', 'success')
        return redirect(url_for('moderate', moderateType='posts'))
    elif contentType == 'discuss':
        discuss = Discuss.query.filter_by(id=id).first()
        discuss.status = 'moderated'
        db.session.commit()
        new_notice = Notification(user_id=discuss.id_author, from_user_id=current_user.id,
                                  discuss_id=discuss.id, type="discuss_accepted", message="Ваша дискуссия была принята!")
        db.session.add(new_notice)
        db.session.commit()
        flash('Дискуссия успешно одобрена!', 'success')
        return redirect(url_for('moderate', moderateType='discusses'))
    else:
        flash('Неизвестный тип контента.', 'danger')
        return redirect(url_for('index'))



@app.route('/deny/<contentType>/<int:id>', methods=['GET', 'POST'])
def deny(contentType, id):
    if contentType == 'post':
        post = Posts.query.filter_by(id=id).first()
        deny_reason = 'Пост не подходит под наши критерии.'
        post.deny_reason = deny_reason
        post.status = 'denied'
        db.session.commit()
        new_notice = Notification(user_id=post.id_author, from_user_id=current_user.id,
                                  post_id=post.id, type="discuss_denied", message="Ваш пост был отклонен.")
        db.session.add(new_notice)
        db.session.commit()
        flash('Пост успешно отклонен.', 'success')
        return redirect(url_for('moderate', moderateType='posts'))
    elif contentType == 'discuss':
        discuss = Discuss.query.filter_by(id=id).first()
        discuss.status = 'denied'
        deny_reason = 'Дискуссия не подходит под наши критерии.'
        discuss.deny_reason = deny_reason
        db.session.commit()
        new_notice = Notification(user_id=discuss.id_author, from_user_id=current_user.id,
                                  discuss_id=discuss.id, type="post_denied", message="Ваша дискуссия была отклонена.")
        db.session.add(new_notice)
        db.session.commit()
        flash('Дискуссия успешно отклонена.', 'success')
        return redirect(url_for('moderate', moderateType='discusses'))
    else:
        flash('Неизвестный тип контента.', 'danger')
        return redirect(url_for('index'))
    return redirect(url_for('moderate_posts'))


@app.route('/add_discuss', methods=['GET', 'POST'])
def add_discuss():
    if current_user.is_authenticated:
        if request.method == 'POST':

            title = request.form.get('title')
            text = request.form.get('text')
            id_author = current_user.id
            views = 0
            categories = request.form.getlist('categories')

            if title == '' or text == '':
                flash("Недопустимый запрос.", 'danger')
                return redirect(url_for('add_discuss'))

            else:
                if current_user.is_banned:
                    flash('Вы забанены!', 'success')
                    redirect(url_for('index'))
                else:
                    try:
                        db.session.add(Discuss(
                            id_author=id_author, title=title, text=text, views=views, status='on_moderating', categories=categories))
                        db.session.commit()
                        flash("Дискуссия успешно добавлена! Ждите одобрения модерацией.", 'success')
                        return redirect(url_for('forum'))

                    except Exception as e:
                        flash(
                            f"Не удалось добавить дискуссию! Ошибка: {e}", 'danger')
                        db.session.rollback()

        return render_template("add_discuss.html")

    else:
        flash("Войдите в аккаунт!", 'danger')
        return redirect(url_for('login'))


@app.route('/discuss/<int:id>', methods=['GET', 'POST'])
def discuss(id):
    discuss = db.session.get(Discuss, id)
    comments = Comments.query.filter_by(id_discuss=id).all()

    if comments:
        for comment in comments:
            comment.author = User.query.get(comment.id_author)
    user_a = db.session.get(User, discuss.id_author)
    liked = False
    disliked = False

    if not discuss:
        return redirect(url_for('forum'))

    if current_user.is_authenticated:
        viewer_id = current_user.id

        view = Views.query.filter_by(
            discuss_id=id,
            user_id=viewer_id
        ).first()

        discuss.liked = Likes.query.filter_by(
            id_author=current_user.id,
            id_discuss=id
        ).first() is not None
    else:
        if 'session_id' not in session:
            session['session_id'] = str(uuid.uuid4())
        viewer_id = session['session_id']
        view = Views.query.filter_by(
            discuss_id=id,
            user_id=viewer_id
        ).first()
    if not view:
        new_view = Views(
            discuss_id=id,
            user_id=current_user.id if current_user.is_authenticated else None,
            session_id=None if current_user.is_authenticated else viewer_id
        )
        db.session.add(new_view)
        discuss.views += 1
        db.session.commit()

    return render_template("discuss.html", discuss=discuss, user_a=user_a, comments=comments)


@app.route('/post/<int:id>', methods=['GET', 'POST'])
def post(id):
    post = db.session.get(Posts, id)
    comments = Comments.query.filter_by(id_post=id).all()

    if comments:
        for comment in comments:
            comment.author = User.query.get(comment.id_author)
    user_a = db.session.get(User, post.id_author)
    liked = False
    disliked = False

    if not post:
        return redirect(url_for('index'))

    if current_user.is_authenticated:
        viewer_id = current_user.id

        view = Views.query.filter_by(
            post_id=id,
            user_id=viewer_id
        ).first()

        if current_user.is_authenticated:
            like = Likes.query.filter_by(
                id_author=current_user.id, id_post=post.id).first()
            post.liked = like is not None
        else:
            post.liked = False

    else:
        if 'session_id' not in session:
            session['session_id'] = str(uuid.uuid4())
        viewer_id = session['session_id']
        view = Views.query.filter_by(
            post_id=id,
            user_id=viewer_id
        ).first()
    if not view:
        new_view = Views(
            post_id=id,
            user_id=current_user.id if current_user.is_authenticated else None,
            session_id=None if current_user.is_authenticated else viewer_id
        )
        db.session.add(new_view)
        post.views += 1
        db.session.commit()

    return render_template("post.html", post=post, liked=liked, disliked=disliked, user_a=user_a, comments=comments)


@app.route('/delete/<contentType>/<int:id>', methods=['GET', 'POST'])
def delete(contentType, id):
    if request.method == 'POST':
        if contentType == 'post':
            word = 'Удалить'
            word_input = request.form.get('word')
            if word_input == word:
                post = db.session.get(Posts, id)
                if not post:
                    return redirect(url_for('forum'))

                if current_user.id != post.id_author and not current_user.is_moderator:
                    flash("Вы не можете удалять чужие посты!", 'danger')
                    return redirect(url_for('index'))

                # если есть таблица лайков
                Likes.query.filter_by(id_post=id).delete()
                # если есть таблица комментариев
                Comments.query.filter_by(id_post=id).delete()

                db.session.delete(post)
                db.session.commit()
                flash('Пост успешно удален.', 'success')
                return redirect(url_for('index'))
            else:
                flash('Неверное слово!', 'warning')
                return redirect(url_for('post', id=id))
        elif contentType == 'discuss':
            word = 'Удалить'
            word_input = request.form.get('word')
            if word_input == word:
                discuss = db.session.get(Discuss, id)
                if not discuss:
                    return redirect(url_for('forum'))

                if current_user.id != discuss.id_author and not current_user.is_moderator:
                    flash("Вы не можете удалять чужие дискуссии!", 'danger')
                    return redirect(url_for('forum'))

                # если есть таблица лайков
                Likes.query.filter_by(id_discuss=id).delete()
                # если есть таблица комментариев
                Comments.query.filter_by(id_discuss=id).delete()

                db.session.delete(discuss)
                db.session.commit()
                flash('Дискуссия успешно удалена.', 'success')
                return redirect(url_for('forum'))
            else:
                flash('Неверное слово!', 'warning')
                return redirect(url_for('discuss', id=id))


@app.route('/like/<contentType>/<int:id>', methods=['GET', 'POST'])
def like(contentType, id):
    if current_user.is_authenticated:
        if contentType == 'discuss':
            discuss = Discuss.query.filter_by(id=id).first()
            like = Likes.query.filter_by(
                id_author=current_user.id, id_discuss=id).first()
            if like:
                db.session.delete(like)
                discuss.rating -= 1
                db.session.commit()
                return jsonify({
                    "rating": discuss.rating,
                    "liked": False
                })
            else:
                new_like = Likes(id_author=current_user.id, id_discuss=id)
                new_notice = Notification(user_id=discuss.id_author, from_user_id=current_user.id,
                                          discuss_id=discuss.id, type="discuss_liked", message="понравилась ваша ветка!")
                discuss.rating += 1
                db.session.add(new_like)
                db.session.add(new_notice)
                db.session.commit()
                return jsonify({
                    "rating": discuss.rating,
                    "liked": True
                })
        elif contentType == 'post':
            post = Posts.query.filter_by(id=id).first()
            like = Likes.query.filter_by(
                id_author=current_user.id, id_post=id).first()
            if like:
                db.session.delete(like)
                post.rating -= 1
                db.session.commit()
                return jsonify({
                    "rating": post.rating,
                    "liked": False
                })
            else:
                new_like = Likes(id_author=current_user.id, id_post=id)
                new_notice = Notification(user_id=post.id_author, from_user_id=current_user.id,
                                          post_id=post.id, type="post_liked", message="понравился ваш пост!")
                post.rating += 1
                db.session.add(new_like)
                db.session.add(new_notice)
                db.session.commit()
                return jsonify({
                    "rating": post.rating,
                    "liked": True
                })
        else:
            flash('Нету такого поста или дискуссии!', 'danger')
            return redirect(url_for('forum'))

    else:
        flash("Авторизируйтесь!", 'danger')
        return redirect('/login')


@app.route('/report/<contentType>/<int:id>', methods=['GET', 'POST'])
def report(contentType, id):
    if current_user.is_authenticated:
        post = db.session.get(Posts, id)
        discuss = db.session.get(Discuss, id)
        moderators = User.query.filter_by(is_moderator=True).all()
        print(f"{len(moderators)} модераторов найдено")
        if contentType == 'post':
            for moderator in moderators:
                new_notice = Notification(user_id=moderator.id, from_user_id=current_user.id,
                                          post_id=post.id, message="отправил жалобу на пост!", type="post_report")
                db.session.add(new_notice)
            db.session.commit()
            flash('Спасибо за помощь!', 'success')
            return redirect(url_for('forum'))

        elif contentType == 'discuss':
            for moderator in moderators:
                new_notice = Notification(user_id=moderator.id, from_user_id=current_user.id,
                                          discuss_id=discuss.id, message="отправил жалобу на ветку!", type="discuss_report")
                db.session.add(new_notice)
            db.session.commit()
            flash('Спасибо за помощь!', 'success')
            return redirect(url_for('forum'))

        else:
            flash('Неизвестный тип жалобы!', 'danger')
            return redirect(url_for('forum'))

    else:
        flash("Авторизируйтесь!", 'danger')
        return redirect('/login')


@app.route('/edit/<editType>/<int:id>', methods=['GET', 'POST'])
def edit(editType, id):
    if not current_user.is_authenticated:
        flash("Войдите в аккаунт!", 'danger')
        return redirect(url_for('login'))
    post = None
    discuss = None
    
    if editType == 'post':
        post = Posts.query.get(id)
        if not post:
            flash('Пост не найден!', 'danger')
            return redirect(url_for('index'))
        if post.id_author != current_user.id and not current_user.is_moderator:
            flash("У вас нет прав для редактирования этого поста!", 'danger')
            return redirect(url_for('index'))

    elif editType == 'discuss':
        discuss = Discuss.query.get(id)
        if not discuss:
            flash('Дискуссия не найдена!', 'danger')
            return redirect(url_for('forum'))
        if discuss.id_author != current_user.id and not current_user.is_moderator:
            flash("У вас нет прав для редактирования этой дискуссии!", 'danger')
            return redirect(url_for('forum'))
    else:
        flash('Недопустимый вид редактирования!', 'danger')
        return redirect(url_for('index'))

    if request.method == 'POST':
        if editType == 'post':
            title = request.form.get('title')
            text = request.form.get('text')
            thumbnail = request.files.get('thumbnail')
            post = Posts.query.get(id)
            categories = request.form.getlist('categories')

        elif editType == 'discuss':
            title = request.form.get('title')
            text = request.form.get('text')
            discuss = Discuss.query.get(id)
            categories = request.form.getlist('categories')

        if not title or not text:
            flash("Недопустимый запрос.", 'danger')
            return redirect(url_for('edit', editType=editType, id=id))
        else:
            try:
                if editType == 'post':
                    thumbnail_filename = None
                    if thumbnail and thumbnail.filename:
                        filename, error = file_upload(thumbnail, ALLOWED_EXTENSIONS_IMAGES)
                        if error:
                            flash(error, 'danger')
                            return redirect(url_for('add_post', post_type=post_type))
                        thumbnail_filename = filename
                        flash("Картинка добавлена!", "success")
                    post = Posts.query.filter_by(id=id).first()
                    discuss = None
                    post.status = 'on_moderating'
                    post.title = title
                    post.text = text
                    post.thumbnail = thumbnail_filename
                    post.categories = categories
                    db.session.commit()
                    flash("Пост успешно изменен! Ожидайте одобрения модерацией.", 'success')
                    return redirect(url_for('index'))
                elif editType == 'discuss':
                    discuss = Discuss.query.filter_by(id=id).first()
                    discuss.status = 'on_moderating'
                    post = None
                    discuss.title = title
                    discuss.text = text
                    discuss.categories = categories
                    db.session.commit()
                    flash("Дискуссия успешно изменена! Ожидайте одобрения модерацией.", 'success')
                    return redirect(url_for('index'))
            except Exception as e:
                print(f"Не удалось изменить пост или дискуссю! Ошибка: {e}")
                db.session.rollback()
    return render_template("edit.html", post=post, discuss=discuss, editType=editType, id=id)


@app.route('/ban_user/<int:id>', methods=['GET', 'POST'])
def ban_user(id):
    user = User.query.filter_by(id=id).first()
    user.is_banned = True
    db.session.commit()
    return redirect(url_for('user', id=id))


@app.route('/unban_user/<int:id>', methods=['GET', 'POST'])
def unban_user(id):
    user = User.query.filter_by(id=id).first()
    user.is_banned = False
    db.session.commit()
    return redirect(url_for('user', id=id))


with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True, port=5000)
