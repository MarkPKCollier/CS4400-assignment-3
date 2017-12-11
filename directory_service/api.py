from flask import Flask
from flask import request
from flask import jsonify
from security_lib import encrypt_msg, decrypt_msg, get_session_key_decrypt_msg
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--host', type=str, required=True)
parser.add_argument('--port_num', type=int, required=True)
parser.add_argument('--replication_service_addr', type=str, required=True)
args = parser.parse_args()

host = args.host
port_num = args.port_num
replication_service_addr = args.replication_service_addr

DIRECTORY_SERVICE_SECRET_KEY = 'directory service key'

app = Flask(__name__)

def get_file_server(file_id, replication_service_key, encrytped_replication_service_key):
    msg = encrypt_msg({
        'file_id': file_id,
        'operation', 'get_server',
        'fs_session_key': replication_service_key
    }, replication_service_key)
    msg['encrypted_session_key'] = encrytped_replication_service_key

    r = requests.get(replication_service_addr, params=msg)

    res = decrypt_msg(r.json(), replication_service_key)

    if res.get('status') == 'success':
        return res.get('server')
    else:
        return None


@app.route("/", methods=['GET'])
def api():
    session_key, params = get_session_key_decrypt_msg(request.args, DIRECTORY_SERVICE_SECRET_KEY)

    file_name = params.get('file_name')
    replication_service_key = params.get('replication_service_key')
    encrytped_replication_service_key = params.get('encrytped_replication_service_key')

    if not file_name:
        return jsonify(encrypt_msg({
            'status': 'error',
            'error_message': 'You must specify a file_name'
        }, session_key))

    if not replication_service_key or not encrytped_replication_service_key:
        return jsonify(encrypt_msg({
            'status': 'error',
            'error_message': 'You must specify a replication service key'
        }, session_key))

    file_id = file_name.replace('/', '_')

    server = get_file_server(file_id)
    if server:
        return jsonify(encrypt_msg({
            'status': 'success',
            'server': server,
            'file_id': file_id
        }, session_key))
    else:
        return jsonify(encrypt_msg({
            'status': 'error',
            'error_message': 'Could not find a server'
        }, session_key))

if __name__ == "__main__":
    app.run(host=host, port=port_num)

