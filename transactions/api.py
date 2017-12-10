from flask import Flask
from flask import request
from flask import jsonify
from security_lib import encrypt_msg, get_session_key_decrypt_msg
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--port_num', type=int)
parser.add_argument('--file_server_ips', nargs='+')
parser.add_argument('--lock_service_ip', type=str)
args = parser.parse_args()

port_num = args.port_num
file_server_ips = args.file_server_ips
lock_service_ip = args.lock_service_ip

from flask import g
import os
import sqlite3
from contextlib import closing

DATABASE = 'transaction_service.db'
DEBUG = True
SECRET_KEY = 'development key'
USERNAME = 'admin'
PASSWORD = 'default'

TRANSACTION_SERVICE_SECRET_KEY = 'transaction service key'

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

def get_new_transaction_id():
    cur = g.db.execute('insert into transactions')
    g.db.commit()
    return '_transaction_{0}'.format(cur.lastrowid)

def broadcast_operation(operation, transaction_id,
        file_server_session_key, encrypted_file_server_session_key,
        lock_service_session_key, encrypted_file_server_session_key):
    # broadcast first to file servers, when they have completed, then send to lock service
    for ip in file_server_ips:
        msg = encrypt_msg({
            'operation', operation,
            'transaction_id': transaction_id
        }, file_server_session_key)
        msg['encrypted_session_key'] = file_server_session_key
        r = requests.put(ip, data=msg)

    msg = encrypt_msg({
        'operation', operation,
        'transaction_id': transaction_id
    }, lock_service_session_key)
    msg['encrypted_session_key'] = encrytped_lock_service_session_key

    r = requests.put(lock_service_ip, data=msg)

def broadcast_commit(transaction_id,
        file_server_session_key, encrypted_file_server_session_key,
        lock_service_session_key, encrypted_file_server_session_key):
    broadcast_operation('commit_transaction', transaction_id,
        file_server_session_key, encrypted_file_server_session_key,
        lock_service_session_key, encrypted_file_server_session_key)

def broadcast_cancel(transaction_id,
        file_server_session_key, encrypted_file_server_session_key,
        lock_service_session_key, encrypted_file_server_session_key):
    broadcast_operation('cancel_transaction', transaction_id,
        file_server_session_key, encrypted_file_server_session_key,
        lock_service_session_key, encrypted_file_server_session_key)


@app.route("/", methods=['POST'])
def api():
    session_key, params = get_session_key_decrypt_msg(request.form, TRANSACTION_SERVICE_SECRET_KEY)

    operation = params.get('operation')

    file_server_session_key = params.get('file_server_session_key')
    encrypted_file_server_session_key = params.get('encrypted_file_server_session_key')
    lock_service_session_key = params.get('lock_service_session_key')
    encrytped_lock_service_session_key = params.get('encrytped_lock_service_session_key')

    if not operation:
        return jsonify(encrypt_msg({
            'status': 'error',
            'error_message': 'You must specify an operation from (start/commit/cancel)'
        }, session_key))
    if not file_server_session_key or not encrypted_file_server_session_key:
        return jsonify(encrypt_msg({
            'status': 'error',
            'error_message': 'You must specify a file server session key'
        }, session_key))
    if not lock_service_session_key or not encrytped_lock_service_session_key:
        return jsonify(encrypt_msg({
            'status': 'error',
            'error_message': 'You must specify a lock service session key'
        }, session_key))
    
    if operation == 'start_transaction':
        t_id = get_new_transaction_id()
        return jsonify(encrypt_msg({
            'status': 'success',
            'transaction_id': t_id
        }, session_key))
    else:
        transaction_id = params.get('transaction_id')

        if not transaction_id:
            return jsonify(encrypt_msg({
                'status': 'error',
                'error_message': 'You must specify a transaction id'
            }, session_key))

        if operation == 'commit_transaction':
            broadcast_commit(transaction_id,
                file_server_session_key, encrypted_file_server_session_key,
                lock_service_session_key, encrypted_file_server_session_key)
            return jsonify(encrypt_msg({
                'status': 'success'
            }, session_key))
        elif operation == 'cancel_transaction':
            broadcast_cancel(transaction_id,
                file_server_session_key, encrypted_file_server_session_key,
                lock_service_session_key, encrypted_file_server_session_key)
            return jsonify(encrypt_msg({
                'status': 'success'
            }, session_key))
        else:
            return jsonify(encrypt_msg({
                'status': 'error',
                'error_message': 'You must specify an operation from (start/commit/cancel), you specified: {0}'.format(operation)
            }, session_key))

if __name__ == "__main__":
    app.run(port=port_num)

