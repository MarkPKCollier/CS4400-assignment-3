from flask import Flask
from flask import request
from flask import jsonify

app = Flask(__name__)

def create_file(file_id):
    pass

def does_file_exist(file_id):
    pass

def read_(file_id, mode):
    pass

def write_(file_id, bytes):
    pass

@app.route("/", methods=['GET', 'POST'])
def api():
    operation = request.args.get('operation')
    file_id = request.args.get('file_id')
    
    if request.method == 'POST':
        if operation == 'store':
            if not does_file_exist(file_id):
                create_file(file_id)
            bytes = request.args.get('bytes')
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
                mode = request.args.get('mode')
                if mode:
                    try:
                        res = read_(file_id, mode)
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
                        'error_message': 'You must specify a mode in which to fetch the file'
                    })
        else:
            return jsonify({
                'status': 'error',
                'error_message': 'The only operation allowed with the GET method is fetch, you specified: {0}'.format(operation)
            })

if __name__ == "__main__":
    app.run()

