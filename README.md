# CS4400-assignment-3

Simple distributed file system with:

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

A NFS style distributed file system.

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