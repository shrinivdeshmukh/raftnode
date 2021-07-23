.. highlight:: shell

============
Installation
============


Stable release
--------------

To install raftnode, run this command in your terminal:

.. code-block:: console

    $ pip install raftnode

This will install the vanilla version of raftnode. The database shall be in-memory without persistent storage. The data will be lost after the node is killed, and shall be restored by other nodes when restarted.

.. code-block:: console

    $ pip install raftnode[rocksdb]

This will install the roskcdb version of raftnode. All the data will be persisted in rocksdb database.


This is the preferred method to install raftnode, as it will always install the most recent stable release.

If you don't have `pip`_ installed, this `Python installation guide`_ can guide
you through the process.

.. _pip: https://pip.pypa.io
.. _Python installation guide: http://docs.python-guide.org/en/latest/starting/installation/


From sources
------------

The sources for raftnode can be downloaded from the `Github repo`_.

You can either clone the public repository:

.. code-block:: console

    $ git clone git://github.com/shrinivdeshmukh/raftnode

Or download the `tarball`_:

.. code-block:: console

    $ curl -OJL https://github.com/shrinivdeshmukh/raftnode/tarball/master

Once you have a copy of the source, you can install it with:

.. code-block:: console

    $ python setup.py install


.. _Github repo: https://github.com/shrinivdeshmukh/raftnode
.. _tarball: https://github.com/shrinivdeshmukh/raftnode/tarball/master
