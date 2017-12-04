from flask import Flask
from flask import request
from flask import jsonify
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

DATABASE = 'file_system.db'
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

def does_file_exist(file_id):
    return read_(file_id)

def read_(file_id):
    cur = g.db.execute('select file from files where file_id = (?)', (file_id, ))
    res = cur.fetchone()
    return res[0] if res else res

def write_(file_id, bytes):
    g.db.execute('replace into files (file_id, file) values (?, ?)', (file_id, bytes))
    g.db.commit()

@app.route("/", methods=['GET', 'POST'])
def api():
    if request.method == 'GET':
        params = request.args
    else:
        params = request.form

    operation = params.get('operation')
    file_id = params.get('file_id')
    
    if request.method == 'POST':
        if operation == 'store':
            bytes = params.get('bytes')
            if bytes:
                try:
                    write_(file_id, bytes)
                    return jsonify({
                        'status': 'success'
                    })
                except Exception as e:
                    return jsonify({
                        'status': 'error',
                        'error_message': e
                    })
            else:
                return jsonify({
                    'status': 'error',
                    'error_message': 'You must provide bytes to write to the file'
                })
        else:
            return jsonify({
                'status': 'error',
                'error_message': 'The only operation allowed with the POST method is store, you specified: {0}'.format(operation)
            })
    elif request.method == 'GET':
        if operation == 'fetch':
            if not does_file_exist(file_id):
                return jsonify({
                    'status': 'error',
                    'error_message': 'File ID: {0} does not exist'.format(file_id)
                })

            else:
                try:
                    res = read_(file_id)
                    return jsonify({
                        'status': 'success',
                        'file_contents': res
                    })
                except Exception as e:
                    return jsonify({
                        'status': 'error',
                        'error_message': e
                    })
        else:
            return jsonify({
                'status': 'error',
                'error_message': 'The only operation allowed with the GET method is fetch, you specified: {0}'.format(operation)
            })

if __name__ == "__main__":
    app.run(port=port_num)

