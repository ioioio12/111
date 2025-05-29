import os
import psycopg2
from flask import Flask, request, jsonify, render_template, redirect, url_for
from flask_cors import CORS
from flasgger import Swagger, swag_from
from flask_jwt_extended import (
    JWTManager, create_access_token, create_refresh_token,
    jwt_required, get_jwt_identity
)
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'super-secret-key')
jwt = JWTManager(app)
swagger = Swagger(app)

DB_CONFIG = {
    "dbname": "db1",
    "user": "postgres",
    "password": "123",
    "host": "localhost",
    "port": "5432"
}

def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)

def create_table():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        DROP TABLE IF EXISTS users;
        CREATE TABLE users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(100) UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        );
    """)
    conn.commit()
    cur.close()
    conn.close()

create_table()

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE username = %s", (username,))
    if cur.fetchone():
        return jsonify({"error": "Username already exists"}), 400

    password_hash = generate_password_hash(password)
    cur.execute("INSERT INTO users (username, password_hash) VALUES (%s, %s)", (username, password_hash))
    conn.commit()
    cur.close()
    conn.close()

    return jsonify({"message": "User registered successfully"}), 201

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, username, password_hash FROM users WHERE username = %s", (username,))
    user = cur.fetchone()
    cur.close()
    conn.close()

    if not user or not check_password_hash(user[2], password):
        return jsonify({"error": "Invalid username or password"}), 401

    access_token = create_access_token(identity=username)
    refresh_token = create_refresh_token(identity=username)
    return jsonify(access_token=access_token, refresh_token=refresh_token), 200

@app.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    identity = get_jwt_identity()
    access_token = create_access_token(identity=identity)
    return jsonify(access_token=access_token), 200

@app.route('/protected', methods=['GET'])
@jwt_required()
def protected():
    current_user = get_jwt_identity()
    return jsonify(logged_in_as=current_user), 200

# API

@app.route("/users", methods=["GET"])
@swag_from({
    'responses': {
        200: {
            'description': 'List of users',
            'examples': {
                'application/json': [{"id": 1, "username": "john"}]
            }
        }
    }
})
def get_users():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, username FROM users")
    users = [{"id": row[0], "username": row[1]} for row in cur.fetchall()]
    cur.close()
    conn.close()
    return jsonify(users)

@app.route("/users/<int:user_id>", methods=["DELETE"])
def delete_user(user_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM users WHERE id = %s", (user_id,))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"message": "User deleted"}), 200

@app.route("/users/<int:user_id>", methods=["PUT"])
def update_user(user_id):
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"error": "Both username and password are required"}), 400

    password_hash = generate_password_hash(password)
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("UPDATE users SET username = %s, password_hash = %s WHERE id = %s",
                (username, password_hash, user_id))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"message": "User updated"}), 200


@app.route('/')
def home():
    return render_template('home.html')


@app.route('/register', methods=['GET'])
def register_form():
    return render_template('register.html')


@app.route('/login', methods=['GET'])
def login_form():
    return render_template('login.html')


@app.route('/register_html', methods=['POST'])
def register_html():
    username = request.form['username']
    password = request.form['password']

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE username = %s", (username,))
    if cur.fetchone():
        cur.close()
        conn.close()
        return "Username already exists", 400

    password_hash = generate_password_hash(password)
    cur.execute("INSERT INTO users (username, password_hash) VALUES (%s, %s)",
                (username, password_hash))
    conn.commit()
    cur.close()
    conn.close()

    return redirect(url_for('login_form'))


@app.route('/login_html', methods=['POST'])
def login_html():
    username = request.form['username']
    password = request.form['password']

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, username, password_hash FROM users WHERE username = %s", (username,))
    user = cur.fetchone()
    cur.close()
    conn.close()

    if not user or not check_password_hash(user[2], password):
        return "Invalid username or password", 401

    return redirect(url_for('protected'))


@app.route('/users_view')
def users_view():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, username FROM users")
    users = [{"id": row[0], "username": row[1]} for row in cur.fetchall()]
    cur.close()
    conn.close()
    return render_template('users.html', users=users)


@app.route('/delete_user/<int:user_id>', methods=['POST'])
def delete_user_form(user_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM users WHERE id = %s", (user_id,))
    conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for('users_view'))


if __name__ == "__main__":
    app.run(debug=True)
