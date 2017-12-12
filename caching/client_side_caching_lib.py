import requests

# caching is provided accross the system as opposed to as a separate module
# thus the caching module has little code
# nonetheless here I provide methods to aid in client side caching

def is_stale_file(file_server_addr, file_id, user_id, sessions_mgr):
    r = requests.get(file_server_addr, params=sessions_mgr.encrypt_msg({
            'operation': 'poll',
            'file_id': file_id,
            'user_id': user_id
            }, 'file server'))
    res = sessions_mgr.decrypt_msg(r.json(), 'file server')

    return res.get('is_stale_copy')