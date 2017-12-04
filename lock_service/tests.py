import requests
import threading
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--server_addr', type=str)
args = parser.parse_args()

server_addr = args.server_addr

def test1(num_threads, increments_per_thread):
    # each thread increments a shared variable using locks acquired from the lock server
    file_id = 'test1'
    global total
    total = 0

    def thread():
        global total
        for _ in range(increments_per_thread):
            r = requests.post(server_addr, data={
                'operation': 'lock',
                'file_id': file_id
            })
            res = r.json()
            if res['status'] == 'success':
                # print threading.current_thread()
                total += 1

            r = requests.post(server_addr, data={
                'operation': 'unlock',
                'file_id': file_id
            })
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

test1(1, 10)
test1(2, 10)
test1(4, 10)
test1(8, 10)

test1(1, 100)
test1(2, 100)
test1(4, 100)
test1(8, 100)
