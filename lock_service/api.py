import sys
sys.path.insert(0, '../security_service')

from flask import Flask
from flask import request
from flask import jsonify
from security_lib import encrypt_msg, get_session_key_decrypt_msg
import threading
import time
import json
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

DATABASE = 'lock_service.db'
DEBUG = True
SECRET_KEY = 'development key'
USERNAME = 'admin'
PASSWORD = 'default'

LOCK_SERVICE_SECRET_KEY = 'lock service key'

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

look_pool_size = 50
lock_pool = {i: threading.RLock() for i in range(look_pool_size)}

def lock(file_id):
    while True:
        db_lock_id = hash(file_id) % look_pool_size
        db_lock = lock_pool[db_lock_id]
        db_lock.acquire()
        try:
            cur = g.db.execute('select locked, transaction_id from locks where file_id = (?)', (file_id, ))
            res = cur.fetchone()
            if res:
                if res[0] == 0 and res[1] is None:
                    return True
            else:
                g.db.execute('insert into locks (file_id, locked) values (?, ?)', (file_id, 1))
                g.db.commit()
                return True
        finally:
            db_lock.release()

        time.sleep(0.1)

def unlock(file_id):
    while True:
        db_lock_id = hash(file_id) % look_pool_size
        db_lock = lock_pool[db_lock_id]
        db_lock.acquire()
        try:
            g.db.execute('replace into locks (file_id, locked) values (?, ?)', (file_id, 0))
            g.db.commit()
            return True
        finally:
            db_lock.release()

        time.sleep(0.1)

def commit_transaction(transaction_id):
    g.db.execute('replace into locks (locked, transaction_id) values (?, ?) where transaction_id = (?)', (0, None, transaction_id))
    g.db.commit()

def cancel_transaction(transaction_id):
    commit_transaction(transaction_id)

@app.route("/", methods=['POST', 'PUT'])
def api():
    session_key, params = get_session_key_decrypt_msg(request.form, LOCK_SERVICE_SECRET_KEY)

    operation = params.get('operation')

    if not operation:
        return jsonify(encrypt_msg({
            'status': 'error',
            'error_message': 'You must specify an operation from (lock/unlock)'
        }, session_key))
    
    if request.method == 'POST':
        file_id = params.get('file_id')

        if not file_id:
            return jsonify(encrypt_msg({
                'status': 'error',
                'error_message': 'You must specify a file_id'
            }, session_key))

        if operation == 'lock':
            res = lock(file_id)
            if res:
                return jsonify(encrypt_msg({
                    'status': 'success'
                }, session_key))
            else:
                return jsonify(encrypt_msg({
                    'status': 'error',
                    'error_message': 'Timeout: failed to lock file: {0}'.format(file_id)
                }, session_key))
        elif operation == 'unlock':
            unlock(file_id)
            return jsonify(encrypt_msg({
                'status': 'success'
            }, session_key))

    elif request.method == 'PUT':
        transaction_id = params.get('transaction_id')
        if not transaction_id:
            return jsonify(encrypt_msg({
                'status': 'error',
                'error_message': 'You must specify a transaction id'
            }, session_key))

        if operation == 'commit_transaction':
            try:
                commit_transaction(transaction_id)
                return jsonify(encrypt_msg({
                    'status': 'success'
                }, session_key))
            except Exception as e:
                return jsonify({
                    'status': 'error',
                    'error_message': e
                })
        elif operation == 'cancel_transaction':
            try:
                cancel_transaction(transaction_id)
                return jsonify(encrypt_msg({
                    'status': 'success'
                }, session_key))
            except Exception as e:
                return jsonify(encrypt_msg({
                    'status': 'error',
                    'error_message': e
                }, session_key))
        else:
            return jsonify(encrypt_msg({
                'status': 'error',
                'error_message': 'The only operations allowed with the PUT method are (commit_transaction/cancel_transaction), you specified: {0}'.format(operation)
            }, session_key))

if __name__ == "__main__":
    app.run(host=host, port=port_num)

