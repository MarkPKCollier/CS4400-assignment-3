import requests
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--server_addr', type=str)
args = parser.parse_args()

server_addr = args.server_addr

def test1():
    # store and fetch contents
    f = 'testing\nthis\n out!'
    file_id = '123'

    r = requests.post(server_addr, data={
            'operation': 'store',
            'file_id': file_id,
            'bytes': f
        })
    res = r.json()
    assert res['status'] == 'success'

    r = requests.get(server_addr, params={
            'operation': 'fetch',
            'file_id': file_id
        })
    res = r.json()

    assert res['status'] == 'success'
    assert res['file_contents'] == f

def test2():
    # no bytes in store request
    file_id = '123'

    r = requests.post(server_addr, data={
            'operation': 'store',
            'file_id': file_id
        })
    res = r.json()
    assert res['status'] == 'error'

def test3():
    # illegal operation on POST
    f = 'testing\nthis\n out!'
    file_id = '123'

    r = requests.post(server_addr, data={
            'operation': 'fetch',
            'file_id': file_id,
            'bytes': f
        })
    res = r.json()
    assert res['status'] == 'error'

def test4():
    # illegal operation on GET
    file_id = '123'

    r = requests.get(server_addr, params={
            'operation': 'store',
            'file_id': file_id
        })
    res = r.json()

    assert res['status'] == 'error'

test1()
test2()
test3()
test4()


