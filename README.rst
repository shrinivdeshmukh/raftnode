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

        raftnode --ip <MY_IP:MY_PORT> --peers <PEER1:PORT1>,<PEER2:PORT2>,...,<PEERn:PORTn> --store database --database <DATABASE_NAME> --volume <DIRECTORY TO STORE THE DATABASE>

**For detailed usage, click** here_ 

.. _here: https://raftnode.readthedocs.io/en/latest/usage.html

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
