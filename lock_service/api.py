from flask import Flask
from flask import request
from flask import jsonify

app = Flask(__name__)

def lock(file_id):
    pass

def unlock(file_id):
    pass

@app.route("/", methods=['POST'])
def api():
    operation = request.args.get('operation')
    file_id = request.args.get('file_id')

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
    app.run()

