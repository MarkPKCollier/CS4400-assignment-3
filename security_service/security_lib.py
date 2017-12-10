import base64
from cryptography.fernet import Fernet

def encrypt_str(s, key):
    cipher_suite = Fernet(key)
    s_ = base64.b64encode(s)
    return cipher_suite.encrypt(s_)

def decrypt_str(s, key):
    cipher_suite = Fernet(key)
    s_ = base64.b64decode(s)
    return cipher_suite.decrypt(s_)

def encrypt_msg(d, key, ignore_keys=[]):
    return {k: encrypt_str(v, key) for k, v in d.iteritems()}

def decrypt_msg(d, key, ignore_keys=[]):
    return {k: decrypt_str(v, key) if k not in ignore_keys else k: v for k, v in d.iteritems()}

def get_session_key_decrypt_msg(d, service_key):
    session_key = decrypt_str(d.get('encrypted_session_key'), service_key)
    return session_key, decrypt_msg(d, session_key, ignore_keys=['encrypted_session_key'])


class SessionsManager:
    def __init__(self, user_id, password, security_service_ip):
        self.user_id = user_id
        self.password = password
        self.security_service_ip = security_service_ip
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

