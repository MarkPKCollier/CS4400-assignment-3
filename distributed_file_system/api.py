from flask import Flask
from flask import request
from flask import jsonify
from subprocess import check_output
import time
from git import Repo

app = Flask(__name__)

# open {r, w}, close, read, write

def does_file_exist(file_id):
    pass

@app.route("/", methods=['GET', 'POST', 'PUT', 'DELETE'])
def api():
    operation = request.args.get('operation')
    file_id = request.args.get('file_id')
    
    if request.method == 'POST':
        if operation == 'write':
            if not does_file_exist(file_id):
                return jsonify({
                    'status': 'error',
                    'error_message': 'File ID: {0} does not exist'.format(file_id)
                })
        else:
            return jsonify({
                'status': 'error',
                'error_message': 'The only operation allowed with the POST method is write, you specified: {0}'.format(operation)
            })
    elif request.method == 'PUT':
        if operation == 'open':
            mode = request.args.get('mode')
            if not mode:
                return jsonify({
                    'status': 'error',
                    'error_message': 'You called the open operation, but did not specify a mode'
                })
            else:
                if mode == 'read':
                    if not does_file_exist(file_id):
                        return jsonify({
                            'status': 'error',
                            'error_message': 'File ID: {0} does not exist'.format(file_id)
                        })
                    else:
                        pass
                elif mode == 'write':
                    pass
        elif operation == 'close':
            if not does_file_exist(file_id):
                return jsonify({
                    'status': 'error',
                    'error_message': 'File ID: {0} does not exist'.format(file_id)
                })
        else:
            return jsonify({
                'status': 'error',
                'error_message': 'The only operations allowed with the PUT method are open, close, you specified: {0}'.format(operation)
            })
    elif request.method == 'GET':
        if operation == 'read':
            if not does_file_exist(file_id):
                return jsonify({
                    'status': 'error',
                    'error_message': 'File ID: {0} does not exist'.format(file_id)
                })

            num_bytes = request.args.get('num_bytes')
            if not num_bytes:
                return jsonify({
                    'status': 'error',
                    'error_message': 'You called the read operation, but did not specify num_bytes'
                })
        else:
            return jsonify({
                'status': 'error',
                'error_message': 'The only operation allowed with the GET method is read, you specified: {0}'.format(operation)
            })
    elif request.method == 'DELETE':
        if operation == 'delete':
            if not does_file_exist(file_id):
                return jsonify({
                    'status': 'error',
                    'error_message': 'File ID: {0} does not exist'.format(file_id)
                })

if __name__ == "__main__":
    app.run()

