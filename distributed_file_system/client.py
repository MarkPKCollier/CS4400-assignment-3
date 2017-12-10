import requests
from security_lib import encrypt_str, decrypt_str, encrypt_msg, decrypt_msg
from datetime import datetime

FS_SERVER_SECRET_KEY = 'file server key'
LOCK_SERVICE_SECRET_KEY = 'lock service key'
TRANSACTION_SERVICE_SECRET_KEY = 'transaction service key'
REPLICATION_SERVICE_SECRET_KEY = 'replication service key'
DIRECTORY_SERVICE_SECRET_KEY = 'directory service key'

class Client:
    def __init__(self, user_id, password, directory_service_ip, locking_service_ip, security_service_ip, transaction_service_ip):
        self.user_id = user_id
        self.password = password
        self.directory_service_ip = directory_service_ip
        self.locking_service_ip = locking_service_ip
        self.security_service_ip = security_service_ip
        self.transaction_service_ip = transaction_service_ip
        self.file_modes = {}
        self.file_positions = {}
        self.file_name_to_server_id = {}
        self.transaction_id = None
        self.session_keys = {}

    def get_new_session_key(self, service):
        r = requests.get(self.security_service_ip, params={
            'server_name': encrypt_str(service, self.password),
            'user_id': self.user_id
        })
        res = decrypt_msg(r.json(), self.password)
        try:
            if res.get('status') == 'success':
                return res.get('session_key'), res.get('fs_session_key'), res.get('timeout')
            else:
                raise Exception(res.get('error_message')) 
        except:
            raise Exception('Could not get a new session key')

    def get_session_key(self, service):
        tmp = self.session_keys.get(service)
        if not tmp or datetime.now() > tmp[2]:
            key, encrypted_key, timeout = self.get_new_session_key(service)
            self.session_keys[service] = (key, encrypted_key, timeout)
            return key, encrypted_key
        else:
            return tmp[0], tmp[1]

    def encrypt_msg(self, d, service):
        session_key, encrypted_session_key = self.get_session_key(service)
        msg = encrypt_msg(d, session_key)
        msg['encrypted_session_key'] = encrypted_session_key
        return msg

    def decrypt_msg(self, d, service):
        session_key, _ = self.get_session_key(service)
        return decrypt_msg(d, session_key)

    def get_file_server_details(self, file_name, lock=False):
        # get server, file_id from the directory service
        r = requests.get(self.directory_service_ip, params={
            'file_name': file_name
        })
        res = self.decrypt_msg(r.json(), 'directory service')
        if res.get('status') == 'success':
            server, file_id = res['server'], res['file_id']

            # request access from the security service
            # pass

            # if necessary request a lock from the locking service
            if lock:
                r = requests.post(self.locking_service_ip, data=self.encrypt_msg({
                    'operation': encrypt_str('lock', SERVER_SECRET_KEY),
                    'file_id': encrypt_str(file_id, SERVER_SECRET_KEY)
                }, 'lock service'))
                res = self.decrypt_msg(r.json(), 'lock service')
                if res.get('status') == 'success':
                    return server, file_id
                else:
                    raise Exception(res.get('error_message'))
            else:
                return server, file_id


        else:
            raise Exception(res.get('error_message'))


        return server, file_id

    def open(self, file_name, mode):
        server, file_id = self.get_file_server_details(file_name, lock=mode == 'write')

        r = requests.get(server, data=self.encrypt_msg({
            'operation', 'fetch',
            'file_id': file_id,
            'mode': mode,
            'transaction_id': self.transaction_id
        }, 'file server'))
        res = self.decrypt_msg(r.json(), 'file server')
        if res.get('status') == 'success':
            self.file_modes[file_name] = mode
            self.file_positions[file_name] = 0
            f = open(file_name.replace('/', '_'), 'wb')
            try:
                f.write(res.get('file_contents'))
            finally:
                f.close()
            return file_name
        else:
            raise Exception(res.get('error_message'))

    def close(self, file_name):
        if self.file_modes[file_name] == 'write':
            server, file_id = self.get_file_server_details(file_name)
            f = open(file_name.replace('/', '_'), 'rb')
            try:
                bytes = f.read()
            finally:
                f.close()
            r = requests.post(server, data=self.encrypt_msg({
                'operation', 'store',
                'file_id': file_id,
                'bytes': bytes,
                'transaction_id': self.transaction_id
            }, 'file server'))
            res = self.decrypt_msg(r.json(), 'file server')
            if res.get('status') == 'success':
                r = requests.post(self.locking_service_ip, data=self.encrypt_msg({
                    'operation', 'unlock',
                    'file_id': file_id,
                    'transaction_id': self.transaction_id
                }, 'lock service'))
                res = self.decrypt_msg(r.json(), 'lock service')
                if res.get('status') == 'success':
                    return file_name
                else:
                    raise Exception(res.get('error_message'))
            else:
                raise Exception(res.get('error_message'))
        else:
            return file_name

    def read(self, file_name, num_bytes=None):
        f = open(file_name.replace('/', '_'), 'rb')
        try:
            if num_bytes:
                f.seek(self.file_positions[file_name])
                res = f.read(num_bytes)
                self.file_positions[file_name] += num_bytes
            else:
                res = f.read()
        finally:
            f.close()
        return res

    def write(self, file_name, bytes):
        f = open(file_name.replace('/', '_'), 'wb')
        try:
            f.write(bytes)
        finally:
            f.close()
        return file_name

    def start_transaction(self):
        if not self.transaction_id is None:
            raise Exception('An existing transaction exitsts, close it first before starting a new one')

        r = requests.post(self.transaction_service_ip, data=self.encrypt_msg({
            'operation': 'start_transaction',
            'file_server_session_key': self.get_session_key('file server'),
            'lock_service_session_key': self.get_session_key('lock service')
        }, 'transaction service'))
        res = self.decrypt_msg(r.json(), 'transaction service')
        if res.get('status') == 'success':
            self.transaction_id = res.get('transaction_id')
            return self.transaction_id
        else:
            raise Exception(res.get('error_message'))

    def commit_transaction(self):
        r = requests.post(self.transaction_service_ip, data=self.encrypt_msg({
            'operation': 'commit_transaction',
            'transaction_id': self.transaction_id,
            'file_server_session_key': self.get_session_key('file server'),
            'lock_service_session_key': self.get_session_key('lock service')
        }, 'transaction service'))
        res = self.decrypt_msg(r.json(), 'transaction service')
        if res.get('status') == 'error':
            raise Exception(res.get('error_message'))
        self.transaction_id = None

    def cancel_transaction(self):
        r = requests.post(self.transaction_service_ip, data=self.encrypt_msg({
            'operation': 'cancel_transaction',
            'transaction_id': self.transaction_id,
            'file_server_session_key': self.get_session_key('file server'),
            'lock_service_session_key': self.get_session_key('lock service')
        }, 'transaction service'))
        res = self.decrypt_msg(r.json(), 'transaction service')
        if res.get('status') == 'error':
            raise Exception(res.get('error_message'))
        self.transaction_id = None

