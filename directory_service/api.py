from flask import Flask
from flask import request
from flask import jsonify

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
    file_name = request.args.get('file_name')

    if not file_name:
        return jsonify({
            'status': 'error',
            'error_message': 'You must specify a file_name'
        })

    file_id = file_name.replace('/', '_')
    server = find_or_create_file(file_id)
    return jsonify({
        'status': 'success',
        'server': server,
        'file_id': file_id
    })

if __name__ == "__main__":
    app.run()

