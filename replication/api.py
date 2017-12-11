import sys
sys.path.insert(0, '../security_service')

from flask import Flask
from flask import request
from flask import jsonify
from security_lib import encrypt_msg, get_session_key_decrypt_msg
from replication_lib import ReplicationLib
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--host', type=str, required=True)
parser.add_argument('--port_num', type=int, required=True)
parser.add_argument('--num_copies_per_file', type=int, required=True)
parser.add_argument('--file_server_addrs', nargs='+', required=True)
args = parser.parse_args()

host = args.host
port_num = args.port_num
num_copies_per_file = args.num_copies_per_file
file_server_addrs = args.file_server_addrs

REPLICATION_SERVICE_SECRET_KEY = 'replication service key'

app = Flask(__name__)

r_lib = ReplicationLib(file_server_addrs, num_copies_per_file)

@app.route("/", methods=['GET'])
def api():
    session_key, params = get_session_key_decrypt_msg(request.args, REPLICATION_SERVICE_SECRET_KEY)

    file_id = params.get('file_id')
    operation = params.get('operation')
    fs_session_key = params.get('fs_session_key')

    if operation == 'get all servers with copies':
        file_servers = r_lib.get_all_file_servers_with_copy(file_id)
        return jsonify(encrypt_msg({
            'status': 'success',
            'servers': file_servers
            }, session_key))
    elif operation == 'get server':
        file_server = r_lib.get_file_server(file_id, session_key=fs_session_key)
        return jsonify(encrypt_msg({
            'status': 'success',
            'server': file_server
            }, session_key))

if __name__ == "__main__":
    app.run(host=host, port=port_num)

