from flask import Flask
from flask import request
from flask import jsonify
from security_lib import encrypt_msg, get_session_key_decrypt_msg
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--port_num', type=int)
args = parser.parse_args()

port_num = args.port_num

FS_SERVER_SECRET_KEY = 'file server key'
LOCK_SERVICE_SECRET_KEY = 'lock service key'
TRANSACTION_SERVICE_SECRET_KEY = 'transaction service key'
REPLICATION_SERVICE_SECRET_KEY = 'replication service key'
DIRECTORY_SERVICE_SECRET_KEY = 'directory service key'

app = Flask(__name__)

def find_server(file_id):
    pass

def get_low_load_server():
    pass

def create_file_on_server(file_id):
    server = get_low_load_server()

    return server

def find_or_create_file(file_id):
    server = find_server(file_id)
    if server is None:
        server = create_file_on_server(file_id)

    return server

@app.route("/", methods=['GET'])
def api():
    session_key, params = get_session_key_decrypt_msg(request.args, DIRECTORY_SERVICE_SECRET_KEY)

    file_name = params.get('file_name')

    if not file_name:
        return jsonify(encrypt_msg({
            'status': 'error',
            'error_message': 'You must specify a file_name'
        }, session_key))

    file_id = file_name.replace('/', '_')
    server = find_or_create_file(file_id)
    return jsonify(encrypt_msg({
        'status': 'success',
        'server': server,
        'file_id': file_id
    }, session_key))

if __name__ == "__main__":
    app.run(port=port_num)

