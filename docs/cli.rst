##################
Commands Reference
##################

.. code-block:: console

    usage: raftnode [-h] [-d] --ip IP [--peers PEERS] [-t TIMEOUT] [-v VOLUME]

Named Arguments
^^^^^^^^^^^^^^^

**-\-ip,** ``required``

    IP address with PORT of this machine

    Example: ``--ip 192.168.0.101:5000``

**-\-peers,** ``optional``

    Comma separated IP addresses of other nodes in the cluster

    Example: ``--peers 192.168.0.101:5000,192.168.0.102:5000,192.168.0.103:5000``

**-d, -\-database,** ``optional``

    If set, the data will be stored in a persistent rocksdb database; otherwise, the data will be stored in an in-memory python dictionary

    Default: ``False``

**-v, -\-volume,** ``optional``

    The database files are kept in this directory. It will be created if it does not already exist.

    Default: ``./data``

    Example: ``--volume ./data``

**-t, -\-timeout,** ``optional``

    If peers are given, this timeout number is the interval (in seconds) after which all peers will get a ping; if peers do not answer, they will be removed from this node.

    Default: ``1`` (seconds)

    Example: ``--timeout 0.5``

.. .. argparse::
..    :module: raftnode.cli
..    :func: doc_argparse
..    :prog: raftnode