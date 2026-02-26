from flask import Flask, render_template, redirect, url_for, request, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from config import Config
from models import db, User, Class, Student
from elsa import cli

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# 创建数据库表
with app.app_context():
    db.create_all()

# ---------- 页面路由 ----------
@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/register')
def register():
    return render_template('register.html')

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

# ---------- API 认证 ----------
@app.route('/api/register', methods=['POST'])
def api_register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    if not username or not password:
        return jsonify({'error': '用户名和密码不能为空'}), 400
    if User.query.filter_by(username=username).first():
        return jsonify({'error': '用户名已存在'}), 400
    hashed_pw = generate_password_hash(password)
    user = User(username=username, password=hashed_pw)
    db.session.add(user)
    db.session.commit()
    return jsonify({'message': '注册成功'}), 201

@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    user = User.query.filter_by(username=username).first()
    if user and check_password_hash(user.password, password):
        login_user(user)
        return jsonify({'message': '登录成功'})
    return jsonify({'error': '用户名或密码错误'}), 401

@app.route('/api/logout', methods=['POST'])
@login_required
def api_logout():
    logout_user()
    return jsonify({'message': '已退出'})

# ---------- 班级 API ----------
@app.route('/api/classes', methods=['GET'])
@login_required
def get_classes():
    classes = Class.query.filter_by(user_id=current_user.id).all()
    return jsonify([{'id': c.id, 'name': c.name} for c in classes])

@app.route('/api/classes', methods=['POST'])
@login_required
def add_class():
    data = request.get_json()
    name = data.get('name')
    if not name:
        return jsonify({'error': '班级名称不能为空'}), 400
    new_class = Class(name=name, user_id=current_user.id)
    db.session.add(new_class)
    db.session.commit()
    return jsonify({'id': new_class.id, 'name': new_class.name})

@app.route('/api/classes/<int:class_id>', methods=['PUT'])
@login_required
def edit_class(class_id):
    cls = Class.query.filter_by(id=class_id, user_id=current_user.id).first_or_404()
    data = request.get_json()
    name = data.get('name')
    if not name:
        return jsonify({'error': '班级名称不能为空'}), 400
    cls.name = name
    db.session.commit()
    return jsonify({'id': cls.id, 'name': cls.name})

@app.route('/api/classes/<int:class_id>', methods=['DELETE'])
@login_required
def delete_class(class_id):
    cls = Class.query.filter_by(id=class_id, user_id=current_user.id).first_or_404()
    db.session.delete(cls)
    db.session.commit()
    return jsonify({'message': '删除成功'})

# ---------- 学生 API ----------
@app.route('/api/classes/<int:class_id>/students', methods=['GET'])
@login_required
def get_students(class_id):
    cls = Class.query.filter_by(id=class_id, user_id=current_user.id).first_or_404()
    students = Student.query.filter_by(class_id=cls.id).all()
    return jsonify([{'id': s.id, 'name': s.name, 'age': s.age} for s in students])

@app.route('/api/classes/<int:class_id>/students', methods=['POST'])
@login_required
def add_student(class_id):
    cls = Class.query.filter_by(id=class_id, user_id=current_user.id).first_or_404()
    data = request.get_json()
    name = data.get('name')
    age = data.get('age')
    if not name or age is None:
        return jsonify({'error': '姓名和年龄不能为空'}), 400
    try:
        age = int(age)
    except:
        return jsonify({'error': '年龄必须为数字'}), 400
    student = Student(name=name, age=age, class_id=cls.id)
    db.session.add(student)
    db.session.commit()
    return jsonify({'id': student.id, 'name': student.name, 'age': student.age})

@app.route('/api/students/<int:student_id>', methods=['PUT'])
@login_required
def edit_student(student_id):
    student = Student.query.join(Class).filter(
        Student.id == student_id,
        Class.user_id == current_user.id
    ).first_or_404()
    data = request.get_json()
    name = data.get('name')
    age = data.get('age')
    if not name or age is None:
        return jsonify({'error': '姓名和年龄不能为空'}), 400
    try:
        age = int(age)
    except:
        return jsonify({'error': '年龄必须为数字'}), 400
    student.name = name
    student.age = age
    db.session.commit()
    return jsonify({'id': student.id, 'name': student.name, 'age': student.age})

@app.route('/api/students/<int:student_id>', methods=['DELETE'])
@login_required
def delete_student(student_id):
    student = Student.query.join(Class).filter(
        Student.id == student_id,
        Class.user_id == current_user.id
    ).first_or_404()
    db.session.delete(student)
    db.session.commit()
    return jsonify({'message': '删除成功'})


if __name__ == '__main__':
    # 这部分是留给 elsa 使用的
    # 当你在终端执行 python app.py serve 或 python app.py freeze 时，
    # elsa 的 cli() 函数会根据命令执行相应操作。
    cli(app, base_url='https://Lirui901.github.io/Lirui901.github.io')
