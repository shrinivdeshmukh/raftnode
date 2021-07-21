"""Main module."""
from threading import Thread
from raftnode import logger
from raftnode.election import Election
from raftnode.store import Store
from raftnode.transport import Transport


class RaftNode(Transport):

    def __init__(self, my_ip: str, peers: list, timeout: int, **kwargs):
        self.__store = Store(**kwargs)
        self.__transport = Transport(my_ip, timeout=timeout)
        self.__election = Election(
            transport=self.__transport, store=self.__store)
        self.__peers = peers

    def run(self):
        logger.info('starting transport')
        self.start_transport()
        logger.info('adding peers')
        self.start_adding_peers(peers=self.__peers)
        logger.info('initializing timeout')
        self.start_timeout()

    def start_transport(self):
        Thread(target=self.__transport.serve, args=(self.__election,)).start()

    def start_adding_peers(self, peers):
        if peers:
            for peer in peers:
                Thread(target=self.__transport.req_add_peer,
                       args=(peer,)).start()

    def start_timeout(self):
        self.__election.init_timeout()
