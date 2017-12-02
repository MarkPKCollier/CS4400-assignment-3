from flask import Flask
from flask import request
from flask import jsonify
from subprocess import check_output
import time
from git import Repo

app = Flask(__name__)

def does_file_exist(file_id):
    pass

def open_(file_id, mode):
    pass

def close_(file_id):
    pass

def read_(file_id, num_bytes):
    pass

def write_(file_id, bytes):
    pass

def delete_(file_id):
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
                try:
                    open_(file_id, mode)
                    return jsonify({
                        'status': 'success'
                    })
                except Exception as e:
                    return jsonify({
                        'status': 'error',
                        'error_message': e
                    })
        elif operation == 'close':
            if not does_file_exist(file_id):
                return jsonify({
                    'status': 'error',
                    'error_message': 'File ID: {0} does not exist'.format(file_id)
                })
            else:
                try:
                    close_(file_id)
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
                'error_message': 'The only operations allowed with the PUT method are open, close, you specified: {0}'.format(operation)
            })
    elif request.method == 'GET':
        if operation == 'read':
            if not does_file_exist(file_id):
                return jsonify({
                    'status': 'error',
                    'error_message': 'File ID: {0} does not exist'.format(file_id)
                })

            else:
                num_bytes = request.args.get('num_bytes')
                if not num_bytes:
                    return jsonify({
                        'status': 'error',
                        'error_message': 'You called the read operation, but did not specify num_bytes'
                    })
                else:
                    try:
                        read_(file_id, num_bytes)
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
                'error_message': 'The only operation allowed with the GET method is read, you specified: {0}'.format(operation)
            })
    elif request.method == 'DELETE':
        if operation == 'delete':
            if not does_file_exist(file_id):
                return jsonify({
                    'status': 'error',
                    'error_message': 'File ID: {0} does not exist'.format(file_id)
                })
            else:
                try:
                    delete_(file_id)
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
                'error_message': 'The only operation allowed with the DELETE method is delete, you specified: {0}'.format(operation)
            })

if __name__ == "__main__":
    app.run()

