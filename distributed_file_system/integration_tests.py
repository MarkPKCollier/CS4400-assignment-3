from client import Client
import requests
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--directory_service_addr', type=str, required=True)
parser.add_argument('--locking_service_addr', type=str, required=True)
parser.add_argument('--security_service_addr', type=str, required=True)
parser.add_argument('--transaction_service_addr', type=str, required=True)
args = parser.parse_args()

directory_service_addr = args.directory_service_addr
locking_service_addr = args.locking_service_addr
security_service_addr = args.security_service_addr
transaction_service_addr = args.transaction_service_addr

password_1 = u'test1'
password_2 = u'test2'
password_3 = u'test3'

def create_user(pword):
    r = requests.post(security_service_addr, data={
            'operation': 'create_user',
            'admin_password': 'distributed systems',
            'password': pword,
            'access_level': 'a'
        })
    res = r.json()
    return res.get('user_id')

user_id_1 = create_user(password_1)
user_id_2 = create_user(password_2)
user_id_3 = create_user(password_3)

client1 = Client(user_id_1, password_1, directory_service_addr, locking_service_addr, security_service_addr, transaction_service_addr)
client2 = Client(user_id_2, password_2, directory_service_addr, locking_service_addr, security_service_addr, transaction_service_addr)
client3 = Client(user_id_3, password_3, directory_service_addr, locking_service_addr, security_service_addr, transaction_service_addr)

run_tests_cmds = '''
python distributed_file_system/api.py --port_num=5001 --host=127.0.0.1 --replication_service_addr=http://127.0.0.1:5004
python lock_service/api.py --port_num=5002 --host=127.0.0.1
python security_service/api.py --port_num=5003 --host=127.0.0.1
python replication/api.py --port_num=5004 --host=127.0.0.1 --num_copies_per_file=1 --file_server_addrs http://127.0.0.1:5001
python transactions/api.py --port_num=5005 --host=127.0.0.1 --lock_service_ip=http://127.0.0.1:5002 --file_server_addrs http://127.0.0.1:5001
python directory_service/api.py --port_num=5006 --host=127.0.0.1 --replication_service_addr=http://127.0.0.1:5004

python distributed_file_system/integration_tests.py \
--directory_service_addr=http://127.0.0.1:5006 \
--locking_service_addr=http://127.0.0.1:5002 \
--security_service_addr=http://127.0.0.1:5003 \
--transaction_service_addr=http://127.0.0.1:5005
'''

def test1():
    # single client open a file, write to it and read back contents
    fname = 'test1.txt'
    f = 'test1 file contents'

    client1.open(fname, 'w')
    client1.write(fname, f)
    res = client1.read(fname)
    client1.close(fname)

    assert res == f

    client1.open(fname, 'r')
    res = client1.read(fname)
    client1.close(fname)

    assert res == f

def test2():
    # client1 opens a file, write to it and read back contents, client 2 reads contents
    fname = 'test1.txt'
    f = 'test2 file contents'

    client1.open(fname, 'w')
    client1.write(fname, f)
    res = client1.read(fname)
    client1.close(fname)

    assert res == f

    client1.open(fname, 'r')
    res = client1.read(fname)
    client1.close(fname)

    assert res == f

    client2.open(fname, 'r')
    res = client2.read(fname)
    client2.close(fname)

    assert res == f

def test3():
    # client1 and client2 write to a file and client3 checks it sees the results
    fname = 'test1.txt'
    f = 'test3 file contents'
    f_plus = 'test3 tests appending'

    client1.open(fname, 'w')
    client1.write(fname, f)
    client1.close(fname)

    client3.open(fname, 'r')
    res = client3.read(fname)
    client3.close(fname)

    assert res == f

    client2.open(fname, 'w')
    res = client2.read(fname)
    client2.write(fname, res + f_plus)
    client2.close(fname)

    client3.open(fname, 'r')
    res = client3.read(fname)
    client3.close(fname)

    assert res == (f + f_plus)

def test4():
    # client1 and client2 attempt to simultaniously write to a file, client 2 can't lock the file and a timeout exception is raised
    fname = 'test1.txt'
    f = 'test3 file contents'
    f_ = 'test3 tests locking'

    client1.open(fname, 'w')
    client1.write(fname, f)

    exception = False
    try:
        client2.open(fname, 'w')
        client2.write(fname, f_)
        client2.close(fname)
    except:
        exception = True

    assert exception
    
    client1.close(fname)

    client1.open(fname, 'r')
    res = client1.read(fname)
    client1.close(fname)

    assert res == f


test1()
print 'Passed test 1'

test2()
print 'Passed test 2'

test3()
print 'Passed test 3'

test4()
print 'Passed test 4'




