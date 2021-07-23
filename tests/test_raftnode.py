#!/usr/bin/env python

"""Tests for `raftnode` package."""


import unittest

from raftnode import raftnode

import socket
import time
from json import dumps, loads
import sys
from os import kill
from signal import SIGKILL

class TestRaftnode(unittest.TestCase):
    """Tests for `raftnode` package."""

    @classmethod
    def setUpClass(cls):
        cls.n1 = raftnode.RaftNode(my_ip='127.0.0.1:5000', peers=['127.0.0.1:5001', '127.0.0.1:5002'], timeout=0.02)
        cls.n2 = raftnode.RaftNode(my_ip='127.0.0.1:5001', peers=['127.0.0.1:5000', '127.0.0.1:5002'], timeout=0.02)
        cls.n3 = raftnode.RaftNode(my_ip='127.0.0.1:5002', peers=['127.0.0.1:5000', '127.0.0.1:5001'], timeout=0.02)
        time.sleep(1)
        cls.n1.run()
        time.sleep(1)
        cls.n2.run()
        time.sleep(1)
        cls.n3.run()

    def test1(self):
        time.sleep(10)
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect(('127.0.0.1', 5000))
        client.send(bytes(dumps({'type': 'put', 'key': 'name', 'value': 'John Doe'}), encoding='utf-8'))
        msg = client.recv(1024).decode('utf-8')
        print("MESSAGE", msg)
        client.close()

    # @classmethod
    # def tearDownClass(cls):

if __name__ == '__main__':
    unittest.main()