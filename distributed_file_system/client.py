import os
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
security_service_dir = os.path.join(root_dir, 'security_service')
caching_dir = os.path.join(root_dir, 'caching')
import sys
sys.path.insert(0, security_service_dir)
sys.path.insert(0, caching_dir)

import requests
from security_lib import encrypt_str, decrypt_str, encrypt_msg, decrypt_msg, SessionsManager
from client_side_caching_lib import is_stale_file
from datetime import datetime

class Client:
    def __init__(self, user_id, password, directory_service_addr, locking_service_addr, security_service_addr, transaction_service_addr):
        self.user_id = user_id
        self.password = password
        self.directory_service_addr = directory_service_addr
        self.locking_service_addr = locking_service_addr
        self.security_service_addr = security_service_addr
        self.transaction_service_addr = transaction_service_addr
        self.file_modes = {}
        self.file_transactions = {}
        self.file_positions = {}
        self.file_name_to_server_id = {}
        self.transaction_id = None
        self.sessions_mgr = SessionsManager(user_id, password, security_service_addr)

    def get_file_server_details(self, file_name, lock=False):
        # get server, file_id from the directory service
        replication_service_session_key, encrypted_replication_service_session_key = self.sessions_mgr.get_session_key('replication service')

        r = requests.get(self.directory_service_addr, params=self.sessions_mgr.encrypt_msg({
            'file_name': file_name,
            'replication_service_key': replication_service_session_key,
            'encrytped_replication_service_key': encrypted_replication_service_session_key
        }, 'directory service'))
        res = self.sessions_mgr.decrypt_msg(r.json(), 'directory service')
        if res.get('status') == 'success':
            server, file_id = res['server'], res['file_id']

            # if necessary request a lock from the locking service
            if lock:
                r = requests.post(self.locking_service_addr, data=self.sessions_mgr.encrypt_msg({
                    'operation': 'lock',
                    'file_id': file_id
                }, 'lock service'))
                res = self.sessions_mgr.decrypt_msg(r.json(), 'lock service')
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
        assert mode in ['r', 'w']
        server, file_id = self.get_file_server_details(file_name, lock=mode == 'w')

        if is_stale_file(server, file_id, self.user_id, self.sessions_mgr):
            r = requests.get(server, params=self.sessions_mgr.encrypt_msg({
                'operation': 'fetch',
                'file_id': file_id,
                'mode': mode,
                'transaction_id': self.transaction_id
            }, 'file server'))
            res = self.sessions_mgr.decrypt_msg(r.json(), 'file server')
            if res.get('status') == 'success':
                self.file_modes[file_name] = mode
                self.file_transactions[file_name] = self.transaction_id
                self.file_positions[file_name] = 0
                f = open(str(self.user_id) + '_' + file_name.replace('/', '_'), 'wb')
                try:
                    f.write(res.get('file_contents'))
                finally:
                    f.close()
                return file_name
            elif 'does not exist' in res.get('error_message'):
                self.file_modes[file_name] = mode
                self.file_positions[file_name] = 0
                return file_name
            else:
                raise Exception(res.get('error_message'))
        else:
            return file_name

    def close(self, file_name):
        if self.file_modes[file_name] == 'w' and self.file_transactions.get(file_name) in [None, self.transaction_id]:
            self.file_modes[file_name] = None
            server, file_id = self.get_file_server_details(file_name)
            f = open(str(self.user_id) + '_' + file_name.replace('/', '_'), 'rb')
            try:
                bytes = f.read()
            finally:
                f.close()

            replication_service_session_key, encrypted_replication_service_session_key = self.sessions_mgr.get_session_key('replication service')
            r = requests.post(server, data=self.sessions_mgr.encrypt_msg({
                'operation': 'store',
                'file_id': file_id,
                'bytes': bytes,
                'transaction_id': self.transaction_id,
                'replication_service_session_key': replication_service_session_key,
                'encrypted_replication_service_session_key': encrypted_replication_service_session_key,
                'user_id': self.user_id
            }, 'file server'))
            res = self.sessions_mgr.decrypt_msg(r.json(), 'file server')
            if res.get('status') == 'success':
                r = requests.post(self.locking_service_addr, data=self.sessions_mgr.encrypt_msg({
                    'operation': 'unlock',
                    'file_id': file_id,
                    'transaction_id': self.transaction_id
                }, 'lock service'))
                res = self.sessions_mgr.decrypt_msg(r.json(), 'lock service')
                if res.get('status') == 'success':
                    return file_name
                else:
                    raise Exception(res.get('error_message'))
            else:
                raise Exception(res.get('error_message'))
        else:
            return file_name

    def read(self, file_name, num_bytes=None):
        f = open(str(self.user_id) + '_' + file_name.replace('/', '_'), 'rb')
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
        assert self.file_modes[file_name] == 'w'
        f = open(str(self.user_id) + '_' + file_name.replace('/', '_'), 'wb')
        try:
            f.write(bytes)
        finally:
            f.close()
        return file_name

    def start_transaction(self):
        if not self.transaction_id is None:
            raise Exception('An existing transaction exitsts, close it first before starting a new one')

        file_server_session_key, encrypted_file_server_session_key = self.sessions_mgr.get_session_key('file server')
        lock_service_session_key, encrytped_lock_service_session_key = self.sessions_mgr.get_session_key('lock service')

        r = requests.post(self.transaction_service_addr, data=self.sessions_mgr.encrypt_msg({
            'operation': 'start_transaction',
            'file_server_session_key': file_server_session_key,
            'encrypted_file_server_session_key': encrypted_file_server_session_key,
            'lock_service_session_key': lock_service_session_key,
            'encrypted_lock_service_session_key': encrytped_lock_service_session_key
        }, 'transaction service'))
        res = self.sessions_mgr.decrypt_msg(r.json(), 'transaction service')
        if res.get('status') == 'success':
            self.transaction_id = res.get('transaction_id')
            return self.transaction_id
        else:
            raise Exception(res.get('error_message'))

    def commit_transaction(self):
        if any(map(lambda m: m == 'w', self.file_modes.values())):
            raise Exception('You have files open for writing, close them before commiting a transaction')

        file_server_session_key, encrypted_file_server_session_key = self.sessions_mgr.get_session_key('file server')
        lock_service_session_key, encrytped_lock_service_session_key = self.sessions_mgr.get_session_key('lock service')

        replication_service_session_key, encrypted_replication_service_session_key = self.sessions_mgr.get_session_key('replication service')
        r = requests.post(self.transaction_service_addr, data=self.sessions_mgr.encrypt_msg({
            'operation': 'commit_transaction',
            'transaction_id': self.transaction_id,
            'file_server_session_key': file_server_session_key,
            'encrypted_file_server_session_key': encrypted_file_server_session_key,
            'lock_service_session_key': lock_service_session_key,
            'encrypted_lock_service_session_key': encrytped_lock_service_session_key,
            'replication_service_session_key': replication_service_session_key,
            'encrypted_replication_service_session_key': encrypted_replication_service_session_key,
            'user_id': self.user_id
        }, 'transaction service'))
        res = self.sessions_mgr.decrypt_msg(r.json(), 'transaction service')
        if res.get('status') == 'error':
            raise Exception(res.get('error_message'))
        self.transaction_id = None

    def cancel_transaction(self):
        if any(map(lambda m: m == 'w', self.file_modes.values())):
            raise Exception('You have files open for writing, close them before cancelling a transaction')

        file_server_session_key, encrypted_file_server_session_key = self.sessions_mgr.get_session_key('file server')
        lock_service_session_key, encrytped_lock_service_session_key = self.sessions_mgr.get_session_key('lock service')

        r = requests.post(self.transaction_service_addr, data=self.sessions_mgr.encrypt_msg({
            'operation': 'cancel_transaction',
            'transaction_id': self.transaction_id,
            'file_server_session_key': file_server_session_key,
            'encrypted_file_server_session_key': encrypted_file_server_session_key,
            'lock_service_session_key': lock_service_session_key,
            'encrypted_lock_service_session_key': encrytped_lock_service_session_key
        }, 'transaction service'))
        res = self.sessions_mgr.decrypt_msg(r.json(), 'transaction service')
        if res.get('status') == 'error':
            raise Exception(res.get('error_message'))
        self.transaction_id = None

