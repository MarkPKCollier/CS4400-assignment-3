# CS4400-assignment-3

Plan:

- Specify client/server API
- Implement locking service
- Implement directory service
- Implement security service
- Implement replication service
- Implement in memory client side caching
- Implement a client side application that demonstrates usage of the file system
- Implement transactions

Distributed file system with:

- Distributed Transparent File Access
- Security Service
- Directory Service
- Replication
- Caching
- Transactions
- Lock Service

## Implementation details

Each service is implemented as a separate module exposing a RESTful API.

I use Python with the Flask library to implement each component and its lightwight API.

### Distributed Transparent File Access

I implement a AFS style distributed file system. In particular I implement [AFS v2](http://pages.cs.wisc.edu/~remzi/OSTEP/dist-afs.pdf).

The server offers fetch and store operations and promises to notify clients to changes in the file state via callbacks. This means the server maintains some state on each fetch request, but empirically this was found necessary to scale AFS.

The server exposes a RESTful API that the client communicates with. The client is a Python library that can be imported into another Python program and provides transparent access to the distributed file system. A user of this library would see little difference to using the standard Python I/O library.

Transparently to the library user, each client maintains a lightweight HTTP server which accepts callbacks from the server and invalidates the local cache accordingly.

When a file is opened the client caches it locally and subsequent read and write operations are made locally. When the file is closed, any changes are pushed to the server.

I implement a flat file system, so the mechanisms specified in AFS v2 for reducing server load via caching directory traversals are unnecessary.

---

*The client side API is:*

open(file_name, mode)

close(file_name)

read(file_name, num_bytes) -> num_bytes is optional, if unspecified the whole file is read

write(file_name, bytes)

---

*The server side API is:*


fetch(file_id, mode)

store(file_id, bytes)

---

### Security Service

Implementation of the Kerberos protocol.

### Directory Service

I use a flat file system - in effect offering a single directory. This is similar to other popular distributed file systems such as Amazon Cloud Storage and Google Cloud Storage.

### Replication

File are replicated across different server nodes with consistency maintained by an implementation of the Gossip protocol.

### Caching

As per the AFS specification, clients cache files locally. On each client side open operation, a fetch call is made to the file server. The results of this call are stored to disk locally.

Additionally I implement in memory file caching on the client side.

### Transactions

A simple transaction service enables the user to batch queries into atomic units.

### Lock Service

A read-many, write-one style locking service is provided.

A client locks a file whenever they open a file in write mode. The client calls a RESTful lock service in order to lock/unlock a particular file id.

In order to ensure the lock service scales to a large distributed system we maintain a database containing the lock status of each file id. Thus I don't maintain locks for each file in memory, allowing the number of locks to scale to the limits of the database (disk space) rather than memory.

The lock service locks the database (using a reentrant lock from the [Python threading library](https://docs.python.org/2/library/threading.html)). It then applies the lock/unlock operation to the database for that file id.

In order to enable parallel handling of lock/unlock requests, I maintain a thread pool in memory. Each file id is hashed to an integer and this integer is used to find that file's reentrant lock.

if *pool_size = number of threads in thread pool*
and *num_files = number of file ids in the distributed system*

Then the memory requirements of the lock service is O(*pool_size*) and the disk space requirements are O(*num_files*). But we can service up to *pool_size* parallel lock/unlock requests.



