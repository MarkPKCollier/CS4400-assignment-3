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

print 'Created user', user_id_1
print 'Created user', user_id_2
print 'Created user', user_id_3

client1 = Client(user_id_1, password_1, directory_service_addr, locking_service_addr, security_service_addr, transaction_service_addr)
client2 = Client(user_id_2, password_2, directory_service_addr, locking_service_addr, security_service_addr, transaction_service_addr)
client3 = Client(user_id_3, password_3, directory_service_addr, locking_service_addr, security_service_addr, transaction_service_addr)

run_tests_cmds = '''
python distributed_file_system/api.py --port_num=5001 --host=127.0.0.1 --replication_service_addr=http://127.0.0.1:5006
python distributed_file_system/api.py --port_num=5002 --host=127.0.0.1 --replication_service_addr=http://127.0.0.1:5006
python distributed_file_system/api.py --port_num=5003 --host=127.0.0.1 --replication_service_addr=http://127.0.0.1:5006
python lock_service/api.py --port_num=5004 --host=127.0.0.1
python security_service/api.py --port_num=5005 --host=127.0.0.1
python replication/api.py --port_num=5006 --host=127.0.0.1 --num_copies_per_file=2 --file_server_addrs http://127.0.0.1:5001 http://127.0.0.1:5002 http://127.0.0.1:5003
python transactions/api.py --port_num=5007 --host=127.0.0.1 --lock_service_ip=http://127.0.0.1:5004 --file_server_addrs http://127.0.0.1:5001 http://127.0.0.1:5002 http://127.0.0.1:5003
python directory_service/api.py --port_num=5007 --host=127.0.0.1 --replication_service_addr=http://127.0.0.1:5006

python distributed_file_system/integration_tests.py \
--directory_service_addr=http://127.0.0.1:5008 \
--locking_service_addr=http://127.0.0.1:5004 \
--security_service_addr=http://127.0.0.1:5005 \
--transaction_service_addr=http://127.0.0.1:5007
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
    fname = 'test2.txt'
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
    fname = 'test3.txt'
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
    fname = 'test4.txt'
    f = 'test4 file contents'
    f_ = 'test4 tests locking'

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


def test5():
    # client1 starts a transaction and write to a file, client2 reads the file while the transaction is ongoing, client1 commits, client2 reads
    fname = 'test5.txt'
    f = 'test5 file contents'
    f_ = 'test5 tests commiting transactions'

    client1.open(fname, 'w')
    try:
        client1.write(fname, f)
    finally:
        client1.close(fname)

    tid = client1.start_transaction()
    client1.open(fname, 'w')
    try:
        client1.write(fname, f_)

        client2.open(fname, 'r')
        try:
            res = client2.read(fname)

            assert res == f
        finally:
            client2.close(fname)
    finally:
        client1.close(fname)
    client1.commit_transaction()

    client2.open(fname, 'r')
    try:
        res = client2.read(fname)

        assert res == f_
    finally:
        client2.close(fname)

def test6():
    # like test5 only client commits transaction before closing file
    fname = 'test5.txt'
    f = 'test5 file contents'
    f_ = 'test5 tests commiting transactions'

    client1.open(fname, 'w')
    try:
        client1.write(fname, f)
    finally:
        client1.close(fname)

    tid = client1.start_transaction()
    client1.open(fname, 'w')
    try:
        client1.write(fname, f_)

        client2.open(fname, 'r')
        try:
            res = client2.read(fname)

            assert res == f
            try:
                client1.commit_transaction()
            except:
                exception = True

            assert exception
        finally:
            client2.close(fname)
    finally:
        client1.close(fname)
        client1.commit_transaction()

def test7():
    # client1 starts a transaction and write to a file, client2 reads the file while the transaction is ongoing, client1 cancels, client2 reads
    fname = 'test7.txt'
    f = 'test7 file contents'
    f_ = 'test7 tests cancelling transactions'

    client1.open(fname, 'w')
    try:
        client1.write(fname, f)
    finally:
        client1.close(fname)

    tid = client1.start_transaction()
    client1.open(fname, 'w')
    try:
        client1.write(fname, f_)

        client2.open(fname, 'r')
        try:
            res = client2.read(fname)

            assert res == f
        finally:
            client2.close(fname)
    finally:
        client1.close(fname)
    client1.cancel_transaction()

    client2.open(fname, 'r')
    try:
        res = client2.read(fname)

        assert res == f
    finally:
        client2.close(fname)

def test8():
    # like test7 only client cancels transaction before closing file
    fname = 'test8.txt'
    f = 'test8 file contents'
    f_ = 'test8 tests cancelling transactions'

    client1.open(fname, 'w')
    try:
        client1.write(fname, f)
    finally:
        client1.close(fname)

    tid = client1.start_transaction()
    client1.open(fname, 'w')
    try:
        client1.write(fname, f_)

        client2.open(fname, 'r')
        try:
            res = client2.read(fname)

            assert res == f
        finally:
            client2.close(fname)

        try:
            client1.cancel_transaction()
        except:
            exception = True

        assert exception
    finally:
        client1.close(fname)
        client1.cancel_transaction()


test1()
print 'Passed test 1'

test2()
print 'Passed test 2'

test3()
print 'Passed test 3'

test4()
print 'Passed test 4'

test5()
print 'Passed test 5'

test6()
print 'Passed test 6'

test7()
print 'Passed test 7'

test8()
print 'Passed test 8'




