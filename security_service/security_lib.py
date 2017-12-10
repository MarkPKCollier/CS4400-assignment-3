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

