===============
Message Formats
===============

* ``put data`` - insert data into the cluster

.. code-block:: json

    {
        'type': 'put',
        'key': <KEY>,
        'value': <VALUE>,
        'namespace': <NAMESPACE> // default is default namespace
    }

* ``get data`` - get data from the cluster

.. code-block:: json

    {
        'type': 'get',
        'key': <KEY>,
        'namespace': <NAMESPACE> // default is default namespace
    }

* ``delete data`` - delete data from the cluster

.. code-block:: json

    {
        'type': 'delete',
        'key': <KEY>,
        'namespace': <NAMESPACE> // default is default namespace
    }

* ``get peers`` - get all the nodes in the cluster

.. code-block:: json

    {
        'type': 'peers'
    }