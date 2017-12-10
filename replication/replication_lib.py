from random import randint

class ReplicationLib:
    def __init__(self, file_server_addrs, num_copies_per_file):
        self.file_server_addrs = file_server_addrs
        self.num_copies_per_file = num_copies_per_file

    def get_reference_file_server(self, file_id):
        reference_server_id = hash(file_id) % len(self.file_server_addrs)
        return reference_server_id, self.file_server_addrs[reference_server_id]

    def get_all_file_servers_with_copy(self, file_id):
        reference_server_id, _ = self.get_reference_file_server(file_id)

        res = []
        for shift in range(-(self.num_copies_per_file-1)/2, (self.num_copies_per_file-1)/2) + 1):
            fs_id = (reference_server_id + shift) % len(self.file_server_addrs)
            res.append(self.file_server_addrs[fs_id])
        return res

    def get_file_server(self, file_id, session_key=None):
        if session_key is None:
            # if the client hasn't got a session key then randomly assign them to any server who should handle their file
            fs_num = randint(self.num_copies_per_file-1)
        else:
            # if there is a session key then send the client back to the same server they have interacted with before
            fs_num = (hash(session_key) % self.num_copies_per_file)
        

        return self.get_all_file_servers_with_copy(file_id)[fs_num]
