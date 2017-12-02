import requests

class Client:
    def __init__(self, server_ip):
        self.server_ip = server_ip

    def open(self, file_id, mode):
        r = requests.put(self.server_ip, data={
            'operation', 'open',
            'file_id': file_id,
            'mode': mode
        })
        res = r.json()
        if res.get('status') == 'success':
            return file_id
        else:
            raise Exception(res.get('error_message'))

    def close(self, file_id):
        r = requests.put(self.server_ip, data={
            'operation', 'close',
            'file_id': file_id
        })
        res = r.json()
        if res.get('status') == 'success':
            return file_id
        else:
            raise Exception(res.get('error_message'))

    def read(self, file_id, num_bytes):
        r = requests.get(self.server_ip, params={
            'operation', 'read',
            'file_id': file_id,
            'num_bytes': num_bytes
        })
        res = r.json()
        if res.get('status') == 'success':
            return res.get('bytes')
        else:
            raise Exception(res.get('error_message'))

    def write(self, file_id, bytes):
        r = requests.post(self.server_ip, data={
            'operation', 'write',
            'file_id': file_id,
            'bytes': bytes
        })
        res = r.json()
        if res.get('status') == 'success':
            return file_id
        else:
            raise Exception(res.get('error_message'))

    def delete(self, file_id):
        r = requests.delete(self.server_ip, data={
            'operation', 'delete',
            'file_id': file_id
        })
        res = r.json()
        if res.get('status') == 'success':
            return file_id
        else:
            raise Exception(res.get('error_message'))

