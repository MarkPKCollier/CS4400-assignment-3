from flask import Flask
from flask import request
from flask import jsonify
import threading
import time
import json
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--port_num', type=int)
args = parser.parse_args()

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
            cur = g.db.execute('select locked from locks where file_id = (?)', (file_id, ))
            res = cur.fetchone()
            if res:
                if res[0] == 0:
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

@app.route("/", methods=['POST'])
def api():
    operation = request.form.get('operation')
    file_id = request.form.get('file_id')

    if not operation:
        return jsonify({
            'status': 'error',
            'error_message': 'You must specify an operation from (lock/unlock)'
        })

    if not file_id:
        return jsonify({
            'status': 'error',
            'error_message': 'You must specify a file_id'
        })
    
    if operation == 'lock':
        res = lock(file_id)
        if res:
            return jsonify({
                'status': 'success'
            })
        else:
            return jsonify({
                'status': 'error',
                'error_message': 'Timeout: failed to lock file: {0}'.format(file_id)
            })
    elif operation == 'unlock':
        unlock(file_id)
        return jsonify({
            'status': 'success'
        })

if __name__ == "__main__":
    app.run(port=port_num)

