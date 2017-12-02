from flask import Flask
from flask import request
from flask import jsonify

app = Flask(__name__)

def map_dir(file_id):
    pass

@app.route("/", methods=['GET'])
def api():
    file_id = request.args.get('file_id')

    if not file_id:
        return jsonify({
            'status': 'error',
            'error_message': 'You must specify a file_id'
        })
    
    server, file_id = map_dir(file_id)
    return jsonify({
        'status': 'success',
        'server': server,
        'file_id': file_id
    })

if __name__ == "__main__":
    app.run()

