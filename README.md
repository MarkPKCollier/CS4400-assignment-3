# CS4400-assignment-3

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

The server offers open and close operations and promises to notify clients to changes in the file state via callbacks. This means the server maintains some state on each open request, but empirically this was found necessary to scale AFS.

Each client maintains a lightweight HTTP server which accepts callbacks and invalidates the local cache accordingly.

When a file is opened the client caches it locally and subsequent read and write operations are made locally. When the file is closed, these changes are pushed to the server.

I implement a flat file system, so the mechanisms specified in AFS v2 for reducing server load via caching directory traversals are unnecessary.

The client side API is

---

open(file_id, mode)

close(file_id)

read(file_id, num_bytes) -> num_bytes is optional, if unspecified the whole file is read

write(file_id, bytes)

The server side API is

---

fetch(file_id, mode)

store(file_id, bytes)

### Security Service

Implementation of the Kerberos protocol.

### Directory Service

I use a flat file system - in effect offering a single directory. This is similar to other popular distributed file systems such as Amazon Cloud Storage and Google Cloud Storage.

### Replication

File are replicated across different server nodes with consistency maintained by an implementation of the Gossip protocol.

### Caching

Parts of files are cached in memory on the client side.

### Transactions

A simple transaction service enables the user to batch queries into atomic units.

### Lock Service

A read-many, write-one style locking service is provided.