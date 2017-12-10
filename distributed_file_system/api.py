from flask import Flask
from flask import request
from flask import jsonify
import json
from security_lib import encrypt_msg, get_session_key_decrypt_msg
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--port_num', type=int)
parser.add_argument('--replication_service_addr', type=str)
args = parser.parse_args()

port_num = args.port_num
replication_service_addr = args.replication_service_addr

from flask import g
import os
import sqlite3
from contextlib import closing

DATABASE = 'file_system.db'
DEBUG = True
SECRET_KEY = 'development key'
USERNAME = 'admin'
PASSWORD = 'default'

FS_SERVER_SECRET_KEY = 'file server key'

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

def does_file_exist(file_id):
    return read_(file_id)

def is_stale_copy(file_id, user_id):
    cur = g.db.execute('select last_update_user_id from files where file_id = (?)', (file_id, ))
    res = cur.fetchone()
    if not res or not res[0] == user_id:
        return True
    else:
        return False

def read_(file_id):
    cur = g.db.execute('select file from files where file_id = (?)', (file_id, ))
    res = cur.fetchone()
    return res[0] if res else res

def get_file_servers(file_id, replication_service_key, encrytped_replication_service_key):
    msg = encrypt_msg({
        'file_id': file_id,
        'operation', 'get all servers with copies'
    }, replication_service_key)
    msg['encrypted_session_key'] = encrytped_replication_service_key

    r = requests.get(replication_service_addr, params=msg)

    res = decrypt_msg(r.json(), replication_service_key)

    if res.get('status') == 'success':
        return res.get('servers')
    else:
        return None

def broadcast_updated_file(file_id, bytes, user_id,
    session_key, encrypted_session_key,
    replication_service_session_key, encrypted_replication_service_session_key):
    
    servers_with_file_copies = get_file_servers(file_id, replication_service_session_key, encrypted_replication_service_session_key)

    for server in servers_with_file_copies:
        msg = encrypt_msg({
            'operation', 'store',
            'file_id': file_id,
            'bytes': bytes,
            'transaction_id': None,
            'replication_service_session_key': replication_service_session_key,
            'encrypted_replication_service_session_key': encrypted_replication_service_session_key
            'is_broadcast': True,
            'user_id': user_id
        }, session_key)
        msg['encrypted_session_key'] = encrypted_session_key

        r = requests.post(server, data=msg)

def write_(file_id, bytes, transaction_id, user_id,
    session_key, encrypted_session_key,
    replication_service_session_key, encrypted_replication_service_session_key, broadcast=False):
    if transaction_id is None:
        g.db.execute('replace into files (file_id, file, last_update_user_id) values (?, ?)', (file_id, bytes, user_id))
        g.db.commit()
        if broadcast:
            broadcast_updated_file(file_id, bytes, user_id, session_key, encrypted_session_key, replication_service_session_key, encrypted_replication_service_session_key)
    else:
        g.db.execute('replace into files (file_id, shadow_file) values (?, ?)', (file_id, bytes))
        g.db.commit()

def commit_transaction(transaction_id, user_id,
    session_key, encrypted_session_key,
    replication_service_session_key, encrypted_replication_service_session_key):
    cur = g.db.execute('select (file_id, shadow_file) from files where transaction_id = (?)', (transaction_id))
    for file_id, shadow_file in cur.fetchall():
        g.db.execute('replace into files (file_id, file, shadow_file, transaction_id) values (?, ?)', (file_id, shadow_file, None, None))
        g.db.commit()

        broadcast_updated_file(file_id, shadow_file, user_id, session_key, encrypted_session_key, replication_service_session_key, encrypted_replication_service_session_key)

def cancel_transaction(transaction_id):
    g.db.execute('replace into files (transaction_id, shadow_file) values (?, ?) where transaction_id = (?)', (None, None, transaction_id))
    g.db.commit()

@app.route("/", methods=['GET', 'POST', 'PUT'])
def api():
    if request.method == 'GET':
        params = request.args
    else:
        params = request.form

    session_key, params = get_session_key_decrypt_msg(params, FS_SERVER_SECRET_KEY)

    operation = params.get('operation')
    file_id = params.get('file_id')
    
    if request.method == 'POST':
        if operation == 'store':
            bytes = params.get('bytes')
            transaction_id = params.get('transaction_id')
            if bytes:
                replication_service_session_key = params.get('replication_service_session_key')
                encrypted_replication_service_session_key = params.get('encrypted_replication_service_session_key')

                if not replication_service_session_key or not encrypted_replication_service_session_key:
                    return jsonify(encrypt_msg({
                        'status': 'error',
                        'error_message': 'You must specify a replication service session key'
                    }, session_key))

                try:
                    is_broadcast = params.get('is_broadcast')
                    user_id = params.get('user_id')
                    write_(file_id, bytes, user_id, transaction_id, session_key, params.get('encrypted_session_key'), replication_service_session_key, encrypted_replication_service_session_key, broadcast=(is_broadcast is None or not is_broadcast))
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
                    'error_message': 'You must provide bytes to write to the file'
                }, session_key))
        else:
            return jsonify(encrypt_msg({
                'status': 'error',
                'error_message': 'The only operation allowed with the POST method is store, you specified: {0}'.format(operation)
            }, session_key))
    elif request.method == 'GET':
        if operation == 'fetch':
            if not does_file_exist(file_id):
                return jsonify(encrypt_msg({
                    'status': 'error',
                    'error_message': 'File ID: {0} does not exist'.format(file_id)
                }, session_key))

            else:
                try:
                    res = read_(file_id)
                    return jsonify(encrypt_msg({
                        'status': 'success',
                        'file_contents': res
                    }, session_key))
                except Exception as e:
                    return jsonify(encrypt_msg({
                        'status': 'error',
                        'error_message': e
                    }, session_key))
        elif operation == 'poll':
            user_id = params.get('user_id')
            return jsonify(encrypt_msg({
                'status': 'success',
                'is_stale_copy': is_stale_copy(file_id, user_id)
            }, session_key))

        else:
            return jsonify(encrypt_msg({
                'status': 'error',
                'error_message': 'The only operations allowed with the GET method are (fetch/poll), you specified: {0}'.format(operation)
            }, session_key))

    elif request.method == 'PUT':
        transaction_id = params.get('transaction_id')
        if not transaction_id:
            return jsonify(encrypt_msg({
                'status': 'error',
                'error_message': 'You must specify a transaction id'
            }, session_key))

        if operation == 'commit_transaction':
            replication_service_session_key = params.get('replication_service_session_key')
            encrypted_replication_service_session_key = params.get('encrypted_replication_service_session_key')

            if not replication_service_session_key or not encrypted_replication_service_session_key:
                return jsonify(encrypt_msg({
                    'status': 'error',
                    'error_message': 'You must specify a replication service session key'
                }, session_key))

            try:
                user_id = params.get('user_id')
                commit_transaction(transaction_id, user_id, session_key, params.get('encrypted_session_key'), replication_service_session_key, encrypted_replication_service_session_key)
                return jsonify(encrypt_msg({
                    'status': 'success'
                }, session_key))
            except Exception as e:
                return jsonify(encrypt_msg({
                    'status': 'error',
                    'error_message': e
                }, session_key))
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
    app.run(port=port_num)

