from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import sqlite3
from datetime import datetime
import uuid
import os

app = Flask(__name__, static_folder='dist', static_url_path='')
CORS(app)

def init_db():
    conn = sqlite3.connect('tasks.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS tasks
        (id TEXT PRIMARY KEY,
         title TEXT NOT NULL,
         description TEXT,
         completed BOOLEAN NOT NULL DEFAULT 0,
         created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP)
    ''')
    conn.commit()
    conn.close()

@app.route('/')
def serve():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/api/tasks', methods=['GET'])
def get_tasks():
    try:
        conn = sqlite3.connect('tasks.db')
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
        data = request.json
        task_id = str(uuid.uuid4())
        conn = sqlite3.connect('tasks.db')
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
        data = request.json
        conn = sqlite3.connect('tasks.db')
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
        conn = sqlite3.connect('tasks.db')
        c = conn.cursor()
        c.execute('DELETE FROM tasks WHERE id = ?', (task_id,))
        conn.commit()
        conn.close()
        return '', 204
    except Exception as e:
        print(f"Error deleting task: {str(e)}")
        return jsonify({'error': 'Failed to delete task'}), 500

if __name__ == '__main__':
    init_db()
    app.run(port=5000, debug=True)