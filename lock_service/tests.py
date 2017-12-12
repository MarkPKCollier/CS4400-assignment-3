import requests
import threading
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--security_service_addr', type=str, required=True)
parser.add_argument('--lock_service_addr', type=str, required=True)
args = parser.parse_args()

security_service_addr = args.security_service_addr
lock_service_addr = args.lock_service_addr

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

def test1(num_threads, increments_per_thread):
    # each thread increments a shared variable using locks acquired from the lock server
    file_id = 'test1'
    global total
    total = 0

    def thread():
        global total
        for _ in range(increments_per_thread):
            r = requests.post(lock_service_addr, data=session_mgr.encrypt_msg({
                'operation': 'lock',
                'file_id': file_id
            }, 'lock service'))
            res = session_mgr.decrypt_msg(r.json(), 'lock service')
            if res['status'] == 'success':
                total += 1

            r = requests.post(lock_service_addr, data=session_mgr.encrypt_msg({
                'operation': 'unlock',
                'file_id': file_id
            }, 'lock service'))
            res = session_mgr.decrypt_msg(r.json(), 'lock service')
            assert res['status'] == 'success'

    threads = []
    for i in range(num_threads):
        t = threading.Thread(target=thread)
        threads.append(t)
        t.start()

    for i in range(num_threads):
        threads[i].join()

    print total, num_threads * increments_per_thread
    assert total == num_threads * increments_per_thread

def test2():
    # test lock service requires a operation
    file_id = 'test2'

    r = requests.post(lock_service_addr, data=session_mgr.encrypt_msg({
                'file_id': file_id
            }, 'lock service'))
    res = session_mgr.decrypt_msg(r.json(), 'lock service')
    assert res['status'] == 'error'

def test3():
    # test lock service requires a file_id
    r = requests.post(lock_service_addr, data=session_mgr.encrypt_msg({
                'operation': 'lock'
            }, 'lock service'))
    res = session_mgr.decrypt_msg(r.json(), 'lock service')
    assert res['status'] == 'error'

    r = requests.post(lock_service_addr, data=session_mgr.encrypt_msg({
                'operation': 'unlock'
            }, 'lock service'))
    res = session_mgr.decrypt_msg(r.json(), 'lock service')
    assert res['status'] == 'error'


test1(1, 10)
test1(2, 10)
test1(4, 10)
test1(8, 10)

test1(1, 100)
test1(2, 100)
test1(4, 100)
test1(8, 100)

test2()
test3()
