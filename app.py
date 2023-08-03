from datetime import datetime

from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.ext.declarative import declarative_base

from enums import TaskStatus

Base = declarative_base()

app = Flask(__name__)
app.config.from_object("config.Config")
jwt = JWTManager(app)
db = SQLAlchemy(app)
CORS(app)


class Task(db.Model):
    __tablename__ = 'tasks'
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(100), nullable=False)
    complete = Column(Boolean, default=False)
    email = Column(String(100), nullable=False)
    text = Column(String(500))


class User(db.Model):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(100), nullable=False)
    password = Column(String(100), nullable=False)


@app.route('/tasks', methods=['POST'])
def create_task():
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    text = data.get('text')

    if username and email:
        new_task = Task(username=username, email=email, text=text)
        db.session.add(new_task)
        db.session.commit()
        return jsonify({'message': 'Task created successfully'}), 201
    else:
        return jsonify({'message': 'Title field is required'}), 400


@app.route('/tasks', methods=['GET'])
def get_tasks():
    complete = request.args.get('complete', TaskStatus.ALL)
    username = request.args.get('username', None)
    email = request.args.get('email', None)
    page = int(request.args.get('page', 1))
    per_page = 3

    filters = {}
    if complete == TaskStatus.COMPLETED:
        filters['complete'] = True
    elif complete == TaskStatus.IN_PROGRESS:
        filters['complete'] = False
    if username:
        filters['username'] = username
    if email:
        filters['email'] = email

    tasks_query = Task.query.filter_by(**filters)

    tasks = tasks_query.paginate(page=page, per_page=per_page, error_out=False)

    task_list = []
    for task in tasks.items:
        task_info = {
            'id': task.id,
            'username': task.username,
            'email': task.email,
            'text': task.text,
            'complete': task.complete
        }
        task_list.append(task_info)

    response = {
        'tasks': task_list,
        'total_pages': tasks.pages,
        'total_items': tasks.total,
        'current_page': tasks.page,
        'has_prev': tasks.has_prev,
        'has_next': tasks.has_next
    }

    return jsonify(response)


@app.route('/tasks/<int:task_id>', methods=['GET'])
def get_task(task_id):
    task = Task.query.get(task_id)
    if task:
        task_info = {
            'id': task.id,
            'username': task.username,
            'email': task.email,
            'text': task.text
        }
        return jsonify(task_info)
    else:
        return jsonify({'message': 'Task not found'}), 404


@app.route('/tasks/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    task = Task.query.get(task_id)
    if task:
        data = request.get_json()
        text_new = data.get('text')
        completed_new = bool(data.get('completed'))

        task.text = text_new if text_new else task.text
        task.complete = completed_new if completed_new else task.complete

        db.session.commit()
        return jsonify({'message': 'Task updated successfully'}), 200
    else:
        return jsonify({'message': 'Task not found'}), 404


@app.route('/tasks/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    task = Task.query.get(task_id)
    if task:
        db.session.delete(task)
        db.session.commit()
        return jsonify({'message': 'Task deleted successfully'}), 200
    else:
        return jsonify({'message': 'Task not found'}), 404


@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({"msg": "Missing username or password"}), 400

    user = User.query.filter_by(username=username).first()
    if not user or user.password != password:
        return jsonify({"msg": "Invalid credentials"}), 401

    access_token = create_access_token(identity=username)
    return jsonify({"access_token": access_token}), 200


# Protected route that requires valid access token
@app.route('/protected', methods=['GET'])
@jwt_required()
def protected():
    current_user = get_jwt_identity()
    return jsonify(logged_in_as=current_user), 200
