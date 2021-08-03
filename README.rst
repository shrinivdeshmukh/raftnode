========
raftnode
========


.. image:: https://img.shields.io/pypi/v/raftnode.svg
        :target: https://pypi.python.org/pypi/raftnode

.. image:: https://readthedocs.org/projects/raftnode/badge/?version=latest
        :target: https://raftnode.readthedocs.io/en/latest/?version=latest
        :alt: Documentation Status




RAFT consensus algorithm implementation

* Free software: MIT license
* Documentation: https://raftnode.readthedocs.io.

Overview
--------
`raftnode` is a fault tolerant distributed metastore based on RAFT consensus algorithm. It supports storing data in-memory
and storing data in rocksdb_ database

.. _rocksdb: https://rocksdb.org/

It let's you save the state of your application. Like configurations, web application sessions, or any kind of data you want to cache for faster retrieval. In a way, it's like distributed python dictionary.

**Few core features are:**

* **High availability:** data can be read, even in case of node failures (thanks to the RAFT consensus)

* **Replication:** every data is replicated across machines

* **Stateful-ness:** raftnode maintains a log which is basically sequence of commands as they come in. For example: the cluster gets 2 data insert operations, they will be logged in the exact sequence of their arrival, across the cluster

* **Namespaces:** you can have different isolated categories(namespaces) to store different types of information/configurations. For example: for user sessions, you can have a namespace say 'sessions' that will hold just the session data And another namespace 'configuration' that will hold configurations like database address, microservice address, etc

* **Consistency:** (thanks to RAFT consensus) I've tried to maintain data Consistency. In case of leader node failure, data insertions are halted until new leader node is elected (the time is few ms)

* **Bring-your-own-client:** using raftnode, you can start the distributed cluster. To interact with it, you have the ability to write your own client using nodejs or scala or python or any language of your choice. There's no language binding here.

* **Scaling:** the nodes in the cluster can be added or removed at will.

**When use distributed key value stores?**

Whenever your application needs lots of small continuous reads and writes. For example: ecommerce cart items, product recommendations, microservice address, database configurations , etc.

raftnode is similar to redis or etcd. raftnode also lets you write your own client instead of using redis or etcd libraries.

Here are few links for further reference:

* https://redislabs.com/nosql/key-value-databases/

* https://hazelcast.com/glossary/key-value-store/

* https://www.kdnuggets.com/2021/04/nosql-explained-understanding-key-value-databases.html

**What is the library's future potential?**

Currently, it let's you insert/update key-values, but not delete. It does not have support for snapshots or scheduled backup to some external storage like s3 (I'm not sure of its required). So a few updates in the near future are:

* Add snapshot-ing

* (May be) add probabilistic data structures like hyperloglog and bloom filters

* An authentication mechanism to verify the identity of the nodes

Installation
------------

By default, raftnode stores the data in memory. To install the vanilla version, follow these steps:

.. code-block:: console

        pip install raftnode

A persistent database can be used instead of the in-memory data storage. By default, raftnode uses rocksdb. To install this version of raftnode, follow these instructions:

.. code-block:: console

        pip install raftnode[rocksdb]

Basic Usage
-----------

* Use in memory data store:

.. code-block:: console

        raftnode --ip <MY_IP:MY_PORT> --peers <PEER1:PORT1>,<PEER2:PORT2>,...,<PEERn:PORTn>

* ...OR use rocksdb database:

.. code-block:: console

        raftnode --ip <MY_IP:MY_PORT> --peers <PEER1:PORT1>,<PEER2:PORT2>,...,<PEERn:PORTn> --store database --volume <DIRECTORY TO STORE THE DATABASE>

**For detailed command line reference, click** `cli usage`_

.. _`cli usage`: https://raftnode.readthedocs.io/en/latest/cli.html

**For detailed usage, click** `client usage`_

.. _`client usage`: https://raftnode.readthedocs.io/en/latest/usage.html

For more detailed CLI instructions:
===================================

.. code-block:: console

        raftnode --help

Features
--------

* TODO

Credits
-------

This package was created with Cookiecutter_ and the `audreyr/cookiecutter-pypackage`_ project template.

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`audreyr/cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage
