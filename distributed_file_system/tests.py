import requests
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--file_server_addr', type=str, required=True)
parser.add_argument('--security_service_addr', type=str, required=True)
args = parser.parse_args()

security_service_addr = args.security_service_addr
file_server_addr = args.file_server_addr

user_password = u'test'

r = requests.post(security_service_addr, data={
        'operation': 'create_user',
        'admin_password': 'distributed systems',
        'password': user_password,
        'access_level': 'a'
    })
res = r.json()

user_id = res.get('user_id')

import os
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
security_service_dir = os.path.join(root_dir, 'security_service')
import sys
sys.path.insert(0, security_service_dir)
from security_lib import SessionsManager

session_mgr = SessionsManager(user_id, user_password, security_service_addr)
replication_service_key, encrytped_replication_service_key = session_mgr.get_session_key('replication service')

def test1():
    # store and fetch contents
    f = 'testing\nthis\n out!'
    file_id = '123'

    r = requests.post(file_server_addr, data=session_mgr.encrypt_msg({
            'operation': 'store',
            'file_id': file_id,
            'bytes': f,
            'replication_service_session_key': replication_service_key,
            'encrypted_replication_service_session_key': encrytped_replication_service_key
        }, 'file server'))
    res = session_mgr.decrypt_msg(r.json(), 'file server')

    assert res['status'] == 'success'

    r = requests.get(file_server_addr, params=session_mgr.encrypt_msg({
            'operation': 'fetch',
            'file_id': file_id
        }, 'file server'))
    res = session_mgr.decrypt_msg(r.json(), 'file server')

    assert res['status'] == 'success'
    assert res['file_contents'] == f

def test2():
    # no bytes in store request
    file_id = '123'

    r = requests.post(file_server_addr, data=session_mgr.encrypt_msg({
            'operation': 'store',
            'file_id': file_id,
            'replication_service_session_key': replication_service_key,
            'encrypted_replication_service_session_key': encrytped_replication_service_key
        }, 'file server'))
    res = session_mgr.decrypt_msg(r.json(), 'file server')
    assert res['status'] == 'error'

def test3():
    # illegal operation on POST
    f = 'testing\nthis\n out!'
    file_id = '123'

    r = requests.post(file_server_addr, data=session_mgr.encrypt_msg({
            'operation': 'fetch',
            'file_id': file_id,
            'bytes': f
        }, 'file server'))
    res = session_mgr.decrypt_msg(r.json(), 'file server')

    assert res['status'] == 'error'

def test4():
    # illegal operation on GET
    file_id = '123'

    r = requests.get(file_server_addr, params=session_mgr.encrypt_msg({
            'operation': 'store',
            'file_id': file_id,
            'replication_service_session_key': replication_service_key,
            'encrypted_replication_service_session_key': encrytped_replication_service_key
        }, 'file server'))
    res = session_mgr.decrypt_msg(r.json(), 'file server')

    assert res['status'] == 'error'

test1()
print 'Passed test 1'
test2()
print 'Passed test 2'
test3()
print 'Passed test 3'
test4()
print 'Passed test 4'


