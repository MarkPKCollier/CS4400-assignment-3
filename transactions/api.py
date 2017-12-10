from flask import Flask
from flask import request
from flask import jsonify
import threading
import time
import json
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

def broadcast_commit(transaction_id):
    # broadcast first to file servers, when they have completed, then send to lock service
    for ip in file_server_ips + [lock_service_ip]:
        r = requests.put(ip, data={
            'operation', 'commit_transaction',
            'transaction_id': transaction_id
        })

def broadcast_cancel(transaction_id):
    # broadcast first to file servers, when they have completed, then send to lock service
    for ip in file_server_ips + [lock_service_ip]:
        r = requests.put(ip, data={
            'operation', 'cancel_transaction',
            'transaction_id': transaction_id
        })


@app.route("/", methods=['POST'])
def api():
    operation = request.form.get('operation')

    if not operation:
        return jsonify({
            'status': 'error',
            'error_message': 'You must specify an operation from (start/commit/cancel)'
        })
    
    if operation == 'start_transaction':
        t_id = get_new_transaction_id()
        return jsonify({
            'status': 'success',
            'transaction_id': t_id
        })
    else:
        transaction_id = request.form.get('transaction_id')

        if not transaction_id:
            return jsonify({
                'status': 'error',
                'error_message': 'You must specify a transaction id'
            })

        if operation == 'commit_transaction':
            broadcast_commit(transaction_id)
            return jsonify({
                'status': 'success'
            })
        elif operation == 'cancel_transaction':
            broadcast_cancel(transaction_id)
            return jsonify({
                'status': 'success'
            })
        else:
            return jsonify({
                'status': 'error',
                'error_message': 'You must specify an operation from (start/commit/cancel), you specified: {0}'.format(operation)
            })

if __name__ == "__main__":
    app.run(port=port_num)

