import requests

class Client:
    def __init__(self, server_ip):
        self.server_ip = server_ip
        self.file_modes = {}
        self.file_positions = {}

    def open(self, file_id, mode):
        r = requests.get(self.server_ip, data={
            'operation', 'fetch',
            'file_id': file_id,
            'mode': mode
        })
        res = r.json()
        if res.get('status') == 'success':
            self.file_modes[file_id] = mode
            self.file_positions[file_id] = 0
            return file_id
        else:
            raise Exception(res.get('error_message'))

    def close(self, file_id):
        if self.file_modes[file_id] == 'read':
            r = requests.post(self.server_ip, data={
                'operation', 'store',
                'file_id': file_id
            })
            res = r.json()
            if res.get('status') == 'success':
                return file_id
            else:
                raise Exception(res.get('error_message'))
        else:
            return file_id

    def read(self, file_id, num_bytes=None):
        f = open(file_id, 'r')
        try:
            if num_bytes:
                f.seek(self.file_positions[file_id])
                res = f.read(num_bytes)
                self.file_positions[file_id] += num_bytes
            else:
                res = f.read()
        finally:
            f.close()
        return res

    def write(self, file_id, bytes):
        f = open(file_id, 'w')
        try:
            f.write(bytes)
        finally:
            f.close()
        return file_id

