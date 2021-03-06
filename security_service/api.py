from flask import Flask
from flask import request
from flask import jsonify
import base64
from cryptography.fernet import Fernet
from datetime import datetime, timedelta
from security_lib import encrypt_str, decrypt_str, encrypt_msg, decrypt_msg, password_to_key
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--host', type=str, required=True)
parser.add_argument('--port_num', type=int, required=True)
args = parser.parse_args()

host = args.host
port_num = args.port_num

from flask import g
import os
import sqlite3
from contextlib import closing

DATABASE = 'clients.db'
DEBUG = True
SECRET_KEY = 'development key'
USERNAME = 'admin'
PASSWORD = 'default'

ADMIN_PASSWORD = 'distributed systems'

FS_SERVER_SECRET_KEY = 'file server key'
LOCK_SERVICE_SECRET_KEY = 'lock service key'
TRANSACTION_SERVICE_SECRET_KEY = 'transaction service key'
REPLICATION_SERVICE_SECRET_KEY = 'replication service key'
DIRECTORY_SERVICE_SECRET_KEY = 'directory service key'

token_maps = {
    'file server': FS_SERVER_SECRET_KEY,
    'lock service': LOCK_SERVICE_SECRET_KEY,
    'transaction service': TRANSACTION_SERVICE_SECRET_KEY,
    'replication service': REPLICATION_SERVICE_SECRET_KEY,
    'directory service': DIRECTORY_SERVICE_SECRET_KEY
}

app = Flask(__name__)
app.config.from_object(__name__)

def connect_db():
    return sqlite3.connect(app.config['DATABASE'])

def init_db():
    with closing(connect_db()) as db:
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()

init_db()

@app.before_request
def before_request():
    g.db = connect_db()

@app.teardown_request
def teardown_request(exception):
    db = getattr(g, 'db', None)
    if db is not None:
        db.close()

def get_user_password(user_id):
    cur = g.db.execute('select password from clients where id = (?)', (user_id, ))
    res = cur.fetchone()
    try:
        return res[0]
    except:
        return None

def gen_key():
    fernet_key = Fernet.generate_key()
    return fernet_key

@app.route("/", methods=['GET', 'POST'])
def api():
    if request.method == 'GET':
        params = request.args
    else:
        params = request.form

    if request.method == 'GET':
        user_id = params.get('user_id')
        user_password = get_user_password(user_id)
        if user_password is None:
            return jsonify({
                'status': 'error',
                'error_message': 'We do not have a password for that user'
            })

        encrypted_server_name = params.get('server_name')
        server_name = decrypt_str(encrypted_server_name, password_to_key(user_password))

        if server_name in token_maps:
            new_session_key = gen_key()
            timeout = datetime.now() + timedelta(hours=8)

            return jsonify(encrypt_msg({
                'status': 'success',
                'fs_session_key': encrypt_str(new_session_key, token_maps[server_name]),
                'session_key': new_session_key,
                'timeout': timeout
            }, user_password))
        else:
            return jsonify(encrypt_msg({
                'status': 'error',
                'error_message': 'Busted you failed authentication - better luck next time'
            }, user_password))
    elif request.method == 'POST':
        operation = params.get('operation')
        if operation == 'create_user':
            if params.get('admin_password') != ADMIN_PASSWORD:
                return jsonify({
                    'status': 'error',
                    'error_message': 'You have provided administrative authentication'
                })

            password = params.get('password')
            access_level = params.get('access_level')

            cur = g.db.execute('insert into clients (password, access_level) values (?, ?)', (password, access_level))
            g.db.commit()
            return jsonify({
                    'status': 'success',
                    'user_id': cur.lastrowid
                })

if __name__ == "__main__":
    app.run(host=host, port=port_num)

