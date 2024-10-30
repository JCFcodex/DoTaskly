from flask import Flask, request, jsonify, send_from_directory, make_response
from flask_cors import CORS
from datetime import datetime
import sqlite3
import uuid
import os

app = Flask(__name__, static_folder='dist', static_url_path='')
CORS(app, supports_credentials=True)

def get_or_create_user_id():
    user_id = request.cookies.get('user_id')
    if not user_id:
        user_id = str(uuid.uuid4())
    return user_id

def get_user_db_path(user_id):
    # Create user_databases directory if it doesn't exist
    if not os.path.exists('user_databases'):
        os.makedirs('user_databases')
    return f'user_databases/tasks_{user_id}.db'

def init_user_db(user_id):
    db_path = get_user_db_path(user_id)
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS tasks
        (id TEXT PRIMARY KEY,
         title TEXT NOT NULL,
         description TEXT,
         completed BOOLEAN NOT NULL DEFAULT 0,
         created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP)
    ''')
    
    # Check if this is a new database (no tasks exist)
    c.execute('SELECT COUNT(*) FROM tasks')
    count = c.fetchone()[0]
    
    if count == 0:
        # Create welcome task
        welcome_task = {
            'id': str(uuid.uuid4()),
            'title': 'Welcome to DoTaskly!',
            'description': "This is your first task. Tap the + button below to add new tasks and start organizing your day with DoTaskly. You can edit, complete, or delete tasks as needed!",
            'completed': False
        }
        c.execute(
            'INSERT INTO tasks (id, title, description, completed) VALUES (?, ?, ?, ?)',
            (welcome_task['id'], welcome_task['title'], welcome_task['description'], welcome_task['completed'])
        )
    
    conn.commit()
    conn.close()

@app.route('/')
def serve():
    response = make_response(send_from_directory(app.static_folder, 'index.html'))
    user_id = get_or_create_user_id()
    # Set cookie that never expires
    response.set_cookie('user_id', user_id, max_age=315360000, httponly=True, samesite='Strict')
    init_user_db(user_id)
    return response

@app.route('/api/tasks', methods=['GET'])
def get_tasks():
    try:
        user_id = get_or_create_user_id()
        conn = sqlite3.connect(get_user_db_path(user_id))
        c = conn.cursor()
        c.execute('SELECT * FROM tasks ORDER BY created_at DESC')
        tasks = []
        for row in c.fetchall():
            tasks.append({
                'id': row[0],
                'title': row[1],
                'description': row[2],
                'completed': bool(row[3]),
                'createdAt': row[4]
            })
        conn.close()
        return jsonify(tasks)
    except Exception as e:
        print(f"Error fetching tasks: {str(e)}")
        return jsonify({'error': 'Failed to fetch tasks'}), 500

@app.route('/api/tasks', methods=['POST'])
def create_task():
    try:
        user_id = get_or_create_user_id()
        data = request.json
        task_id = str(uuid.uuid4())
        conn = sqlite3.connect(get_user_db_path(user_id))
        c = conn.cursor()
        c.execute(
            'INSERT INTO tasks (id, title, description, completed) VALUES (?, ?, ?, ?)',
            (task_id, data['title'], data.get('description'), False)
        )
        conn.commit()
        
        c.execute('SELECT * FROM tasks WHERE id = ?', (task_id,))
        row = c.fetchone()
        task = {
            'id': row[0],
            'title': row[1],
            'description': row[2],
            'completed': bool(row[3]),
            'createdAt': row[4]
        }
        conn.close()
        return jsonify(task), 201
    except Exception as e:
        print(f"Error creating task: {str(e)}")
        return jsonify({'error': 'Failed to create task'}), 500

@app.route('/api/tasks/<task_id>', methods=['PATCH'])
def update_task(task_id):
    try:
        user_id = get_or_create_user_id()
        data = request.json
        conn = sqlite3.connect(get_user_db_path(user_id))
        c = conn.cursor()
        
        if 'completed' in data:
            c.execute(
                'UPDATE tasks SET completed = ? WHERE id = ?',
                (data['completed'], task_id)
            )
        elif 'title' in data:
            c.execute(
                'UPDATE tasks SET title = ?, description = ? WHERE id = ?',
                (data['title'], data.get('description'), task_id)
            )
            
        conn.commit()
        
        c.execute('SELECT * FROM tasks WHERE id = ?', (task_id,))
        row = c.fetchone()
        task = {
            'id': row[0],
            'title': row[1],
            'description': row[2],
            'completed': bool(row[3]),
            'createdAt': row[4]
        }
        conn.close()
        return jsonify(task)
    except Exception as e:
        print(f"Error updating task: {str(e)}")
        return jsonify({'error': 'Failed to update task'}), 500

@app.route('/api/tasks/<task_id>', methods=['DELETE'])
def delete_task(task_id):
    try:
        user_id = get_or_create_user_id()
        conn = sqlite3.connect(get_user_db_path(user_id))
        c = conn.cursor()
        c.execute('DELETE FROM tasks WHERE id = ?', (task_id,))
        conn.commit()
        conn.close()
        return '', 204
    except Exception as e:
        print(f"Error deleting task: {str(e)}")
        return jsonify({'error': 'Failed to delete task'}), 500

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)