# transactions invlove the file server, the lock service and the transasction service
# unit testing the transaction service in isolation is difficult
# I opt for a half way point of interacting with the API directly while also interacting with the file server and lock service

import requests
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--file_server_addr', type=str, required=True)
parser.add_argument('--security_service_addr', type=str, required=True)
parser.add_argument('--transaction_service_addr', type=str, required=True)
args = parser.parse_args()

security_service_addr = args.security_service_addr
file_server_addr = args.file_server_addr
transaction_service_addr = args.transaction_service_addr

user_password_1 = u'test'

r = requests.post(security_service_addr, data={
        'operation': 'create_user',
        'admin_password': 'distributed systems',
        'password': user_password_1,
        'access_level': 'a'
    })
res = r.json()

user_id_1 = res.get('user_id')

user_password_2 = u'testing'

r = requests.post(security_service_addr, data={
        'operation': 'create_user',
        'admin_password': 'distributed systems',
        'password': user_password_2,
        'access_level': 'a'
    })
res = r.json()

user_id_2 = res.get('user_id')



import os
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
security_service_dir = os.path.join(root_dir, 'security_service')
import sys
sys.path.insert(0, security_service_dir)
from security_lib import SessionsManager

session_mgr_1 = SessionsManager(user_id_1, user_password_1, security_service_addr)
session_mgr_2 = SessionsManager(user_id_2, user_password_2, security_service_addr)
replication_service_key_1, encrypted_replication_service_key_1 = session_mgr_1.get_session_key('replication service')
file_server_key_2, encrypted_file_server_key_2 = session_mgr_2.get_session_key('file server')
lock_service_key_2, encrypted_lock_service_key_2 = session_mgr_2.get_session_key('lock service')
replication_service_key_2, encrypted_replication_service_key_2 = session_mgr_2.get_session_key('replication service')

def test1():
    '''
    commands to run in different shells from project root directory:
    python distributed_file_system/api.py --port_num=5001 --host=127.0.0.1 --replication_service_addr=http://127.0.0.1:5004
    python lock_service/api.py --port_num=5002 --host=127.0.0.1
    python security_service/api.py --port_num=5003 --host=127.0.0.1
    python replication/api.py --port_num=5004 --host=127.0.0.1 --num_copies_per_file=1 --file_server_addrs http://127.0.0.1:5001
    python transactions/api.py --port_num=5005 --host=127.0.0.1 --lock_service_ip=http://127.0.0.1:5002 --file_server_addrs http://127.0.0.1:5001
    python transactions/tests.py --file_server_addr=http://127.0.0.1:5001 --security_service_addr=http://127.0.0.1:5003 --transaction_service_addr=http://127.0.0.1:5005
    '''

    # user 1 should create two files
    # user 2 should start a transaction and make edits to the files
    # user 1 should read the contents of the files and verify they are the same as when created
    # user 2 should commit the transaction
    # both users should verify that they get an updated version of the file

    # store and fetch contents
    f1 = 'testing\nthis\n out!'
    f1_ = 'testing\nthis\n out! adding something'
    file_id_1 = '124'

    f2 = 'transactions'
    f2_ = 'transactions rule'
    file_id_2 = '808'

    r = requests.post(file_server_addr, data=session_mgr_1.encrypt_msg({
            'operation': 'store',
            'file_id': file_id_1,
            'bytes': f1,
            'replication_service_session_key': replication_service_key_1,
            'encrypted_replication_service_session_key': encrypted_replication_service_key_1
        }, 'file server'))
    res = session_mgr_1.decrypt_msg(r.json(), 'file server')

    assert res['status'] == 'success'

    r = requests.post(file_server_addr, data=session_mgr_1.encrypt_msg({
            'operation': 'store',
            'file_id': file_id_2,
            'bytes': f2,
            'replication_service_session_key': replication_service_key_1,
            'encrypted_replication_service_session_key': encrypted_replication_service_key_1
        }, 'file server'))
    res = session_mgr_1.decrypt_msg(r.json(), 'file server')

    assert res['status'] == 'success'

    r = requests.post(transaction_service_addr, data=session_mgr_2.encrypt_msg({
            'operation': 'start_transaction',
            'file_server_session_key': file_server_key_2,
            'encrypted_file_server_session_key': encrypted_file_server_key_2,
            'lock_service_session_key': lock_service_key_2,
            'encrypted_lock_service_session_key': encrypted_lock_service_key_2
        }, 'transaction service'))
    res = session_mgr_2.decrypt_msg(r.json(), 'transaction service')

    assert res['status'] == 'success'

    transaction_id = res['transaction_id']

    r = requests.post(file_server_addr, data=session_mgr_2.encrypt_msg({
            'operation': 'store',
            'file_id': file_id_1,
            'bytes': f1_,
            'replication_service_session_key': replication_service_key_2,
            'encrypted_replication_service_session_key': encrypted_replication_service_key_2,
            'transaction_id': transaction_id
        }, 'file server'))
    res = session_mgr_2.decrypt_msg(r.json(), 'file server')

    assert res['status'] == 'success'

    r = requests.post(file_server_addr, data=session_mgr_2.encrypt_msg({
            'operation': 'store',
            'file_id': file_id_2,
            'bytes': f2_,
            'replication_service_session_key': replication_service_key_2,
            'encrypted_replication_service_session_key': encrypted_replication_service_key_2,
            'transaction_id': transaction_id
        }, 'file server'))
    res = session_mgr_2.decrypt_msg(r.json(), 'file server')

    assert res['status'] == 'success'

    r = requests.get(file_server_addr, params=session_mgr_1.encrypt_msg({
            'operation': 'fetch',
            'file_id': file_id_1
        }, 'file server'))
    res = session_mgr_1.decrypt_msg(r.json(), 'file server')

    assert res['status'] == 'success'
    assert res['file_contents'] == f1

    r = requests.get(file_server_addr, params=session_mgr_1.encrypt_msg({
            'operation': 'fetch',
            'file_id': file_id_2
        }, 'file server'))
    res = session_mgr_1.decrypt_msg(r.json(), 'file server')

    assert res['status'] == 'success'
    assert res['file_contents'] == f2

    r = requests.post(transaction_service_addr, data=session_mgr_2.encrypt_msg({
            'operation': 'commit_transaction',
            'transaction_id': transaction_id,
            'file_server_session_key': file_server_key_2,
            'encrypted_file_server_session_key': encrypted_file_server_key_2,
            'lock_service_session_key': lock_service_key_2,
            'encrypted_lock_service_session_key': encrypted_lock_service_key_2,
            'replication_service_session_key': replication_service_key_2,
            'encrypted_replication_service_session_key': encrypted_replication_service_key_2
        }, 'transaction service'))
    res = session_mgr_2.decrypt_msg(r.json(), 'transaction service')

    assert res['status'] == 'success'

    r = requests.get(file_server_addr, params=session_mgr_1.encrypt_msg({
            'operation': 'fetch',
            'file_id': file_id_1
        }, 'file server'))
    res = session_mgr_1.decrypt_msg(r.json(), 'file server')

    assert res['status'] == 'success'
    assert res['file_contents'] == f1_

    r = requests.get(file_server_addr, params=session_mgr_1.encrypt_msg({
            'operation': 'fetch',
            'file_id': file_id_2
        }, 'file server'))
    res = session_mgr_1.decrypt_msg(r.json(), 'file server')

    assert res['status'] == 'success'
    assert res['file_contents'] == f2_



test1()
print 'Passed test 1'


