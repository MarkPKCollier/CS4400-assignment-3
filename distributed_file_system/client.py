import requests

class Client:
    def __init__(self, server_ip):
        self.server_ip = server_ip

    def open(self, file_id, mode):
        r = requests.get(self.server_ip, params={
            'file_id': file_id,
            'mode': mode
        })
        res = r.json()
        if res.get('status') == 'success':
            return file_id
        else:
            raise Exception(res.get('error_message'))

    def close(self, file_id):
        pass

    def read(self, file_id, num_bytes):
        pass

    def write(self, file_id, bytes):
        pass