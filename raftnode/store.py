import time
from os import getenv, makedirs, path
from threading import Lock, Thread
from collections import deque
import shelve

from raftnode import cfg, logger
from raftnode.datastore.memory import MemoryStore

class Store:

    def __init__(self, store_type: str = 'memory', data_dir: str = 'data'):
        self.commit_id = 0
        self.log = deque()
        self.staged = None
        self.db = self.__get_database(store_type, data_dir=data_dir)
        self.__lock = Lock()
        self.__data_dir = getenv('DATA_DIR', data_dir)
        self.__log_file = getenv('LOG_FILENAME', 'OrderedLog')
        self.__data_file = getenv('DATA_FILENAME', 'data.json')
        self.__check_data_dir()
        self.__session()

    def __session(self):
        self.f = shelve.open(path.join(self.__data_dir,self.__log_file), writeback=True)
        try:
            if self.f['data']:
                self.commit_id = self.f['data'][-1]['commit_id']
                logger.debug(f'[SHELVE LOG] commit id, {self.commit_id}')
        except KeyError as e:
            self.f['data'] = self.log
            logger.debug(f'[SHELVE LOG] Initial log, {self.f["data"]}')
    
    def __flush(self):
        self.f['data'].append(self.staged)
        logger.info(f'[DATA INSERT] {self.f["data"][-1]}')
        self.f.close()

    def __check_data_dir(self):
        if not path.exists(self.__data_dir):
            makedirs(self.__data_dir)

    def __get_database(self, store_type: str, **kwargs):
        '''
        get instance of the database

        :param store_type: type of data store to be used; either memory or database
        :type store_type: str
        '''
        if store_type == 'database':
            from raftnode.datastore.rocks import RockStore
            database = kwargs.get('database', None)
            data_dir = kwargs.get('data_dir', None)
            db = RockStore(data_dir=data_dir)
        else:
            db = MemoryStore()
        return db

    def action_handler(self, message: dict):
        '''
        handle the commit and log actions sent by the leader node

        :param message: log/commit data as received from the leader
        :type message: dict
        '''
        with self.__lock:
            action = message['action']
            payload = message['payload']
            if action == 'log':
                self.staged = payload
            elif action == 'commit':
                if isinstance(payload, list):
                    for command in payload:
                # cid = message.get('commit_id', self.commit_id)
                        namespace = command.get('namespace', 'default')
                        delete = command.get('delete', False)
                        leader_cid = command
                        logger.debug(f'[OLD COMMANDS] adding command {command}')
                        if not self.staged:
                            self.staged = command
                        self.commit(namespace, delete)
                else:
                    namespace = payload.get('namespace', 'default')
                    delete = payload.get('delete', False)
                    logger.debug(f'[COMMAND] {payload}')
                    if not self.staged:
                        self.staged = payload
                    self.commit(namespace, delete)
        return

    def put(self, term: int, payload: dict, transport, majority: int) -> bool:
        '''
        Insert data into the database. If this is the leader node, first broadcast
        the message to all the followers and wait for atleast `majority + 1`
        confirmations. Once `majority + 1` followers confirm, send out a commit
        message. This will instruct the followers to commit the data to their databases

        :param term: term of this node
        :type term: int

        :param payload: data to be inserted into log or database
        :type payload: dict

        :param transport: instance of the Transport class
        :type transport: Transport

        :param majority: how many nodes constitute the majority
        :type majority: int
        '''
        namespace = payload.get('namespace', 'default')
        with self.__lock:
            self.staged = payload
            waited = 0
            log_message = {
                'term': term,
                'addr': transport.addr,
                'payload': payload,
                'action': 'log',
                'commit_id': self.commit_id
            }
            log_confirmations = [False] * len(transport.peers)
            Thread(target=self.send_data, args=(
                log_message, transport, log_confirmations,)).start()

            while sum(log_confirmations) + 1 < majority:
                waited += 0.05
                time.sleep(0.05)
                if waited > cfg.MAX_LOG_WAIT / 1000:
                    logger.info(
                        f"waited {cfg.MAX_LOG_WAIT} ms, update rejected:")
                    return False

            commit_message = {
                "term": term,
                "addr": transport.addr,
                "payload": payload,
                "action": "commit",
                "commit_id": self.commit_id
            }
        self.commit(namespace)
        Thread(target=self.send_data,
            args=(commit_message, transport,)).start()
        logger.info(
            "majority reached, replied to client, sending message to commit")
        return True

    def send_data(self, message: dict, transport, confirmations: list = None):
        '''
        send the log or commit data to the follower nodes and record their 
        responses in the `confirmations` list

        :param message: data toe be sent to the follower nodes
        :type message: dict

        :param transport: instance of the transport class
        :type transport: Transport

        :param confirmations: list of the confirmations (initialized to False)
        :type confirmations: list
        '''
        for i, peer in enumerate(transport.peers):
            reply = transport.heartbeat(peer, message)
            if reply and confirmations:
                confirmations[i] = True

    def get(self, payload: dict):
        '''
        retrieve data from the database based on the `key` in the 
        `payload`

        :param payload: dictionary consisting the key using which the
                        data needs to be retrieved from the database
        :type payload: dict 
        '''
        namespace = payload.get('namespace', 'default')
        key = payload["key"]
        value = self.db.get(key=key, namespace=namespace)
        payload.update({'value': value})
        return payload

    def delete(self, term: int, payload: dict, transport, majority: int):
        namespace = payload.get('namespace', 'default')
        with self.__lock:
            self.staged = payload
            waited = 0
            log_message = {
                'term': term,
                'addr': transport.addr,
                'payload': payload,
                'action': 'log',
                'commit_id': self.commit_id
            }
            log_confirmations = [False] * len(transport.peers)
            Thread(target=self.send_data, args=(
                log_message, transport, log_confirmations,)).start()

            while sum(log_confirmations) + 1 < majority:
                waited += 0.0005
                time.sleep(0.0005)
                if waited > cfg.MAX_LOG_WAIT / 1000:
                    logger.info(
                        f"waited {cfg.MAX_LOG_WAIT} ms, update rejected:")
                    return False

            commit_message = {
                "term": term,
                "addr": transport.addr,
                "payload": payload,
                "action": "commit",
                "commit_id": self.commit_id
            }
            Thread(target=self.send_data,
                args=(commit_message, transport,)).start()
            self.commit(namespace, delete=True)
        logger.info(
            "majority reached, replied to client, sending message to commit")
        return True

    def commit(self, namespace: str, delete: bool=False, **kwargs):
        '''
        commit the message to the database after getting
        atleast `majority + 1` confirmations from the 
        follower nodes
        '''
        self.commit_id += 1
        cid = kwargs.get('commit_id', self.commit_id)
        # with self.__lock:
        self.staged.update({'commit_id': cid})
        if self.staged not in self.log:
            logger.debug(f'[APPEND LOG] {self.staged}')
            # self.log.append(self.staged)
            self.__flush()
            self.__session()
            self.log = self.f['data']
        key = self.staged['key']
        if delete:
            value = self.db.delete(key=key, namespace=namespace)
            self.staged = None
            logger.debug(f"[DELETE COMMAND] {self.staged}")
            return value
        value = self.staged['value']
        self.staged = None
        self.db.put(key, value, namespace=namespace)
        logger.info(f"[PUT COMMAND], {self.staged}")
