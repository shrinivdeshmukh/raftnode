import time
from threading import Lock, Thread
from queue import Queue
from raftnode import cfg, logger
from raftnode.store import Store
from raftnode.transport import Transport


class Election:
    def __init__(self, transport: Transport, store: Store, queue: Queue):
        self.timeout_thread = None
        self.status = cfg.FOLLOWER
        self.term = 0
        self.vote_count = 0
        self.store = store
        self.__transport = transport
        self.__lock = Lock()
        self.q = queue
        self.init_timeout()

    def start_election(self):
        '''
        wait for the timeout, and start the leader
        election
        '''
        logger.info('starting election')
        self.term += 1
        self.vote_count = 0
        self.status = cfg.CANDIDATE
        self.peers = self.__transport.peers
        self.majority = ((1 + len(self.peers)) // 2) + 1
        self.init_timeout()
        self.increment_vote()
        self.ask_for_vote()

    def ask_for_vote(self):
        '''
        ask the other nodes in the cluster to vote 
        so that this node can become the leader
        '''
        for peer in self.peers:
            Thread(target=self.send_vote_request,
                   args=(peer, self.term)).start()

    def send_vote_request(self, voter: str, term: int):
        '''
        send vote request message to the voter node
        this message contains the current term of this node,
        the latest commit id and any cached data

        :param voter: address of the voter node in `ip:port`
                      format
        :type voter: str

        :param term: current term of this node
        :type term: int
        '''
        message = {
            'term': term,
            'commit_id': self.store.commit_id,
            'staged': self.store.staged
        }
        while self.status == cfg.CANDIDATE and self.term == term:
            vote_reply = self.__transport.vote_request(voter, message)
            if vote_reply:
                choice = vote_reply['choice']
                logger.debug(f'choice from {voter} is {choice}')
                if choice and self.status == cfg.CANDIDATE:
                    self.increment_vote()
                elif not choice:
                    term = vote_reply['term']
                    if term > self.term:
                        self.status = cfg.FOLLOWER
                break

    def decide_vote(self, term: int, commit_id: int, staged: dict) -> bool:
        '''
        on receiving vote request from the candidate node, decide 
        whether to vote for or against that node

        :param term: term of the candidate node
        :type term: int

        :param commit_id: latest commit_id that the 
                        that the candidate node holds
        :type commit_id: int

        :param staged: any cached/staged data by the candidate node
        :type staged: dict

        :returns: True if the voter can vote in favour of the candidate node
                  False otherwise
        :rtype: bool
        '''
        self.reset_timeout()
        if self.term < term and self.store.commit_id <= commit_id and (staged or (self.store.staged == staged)):
            self.reset_timeout()
            self.term = term
            return True, self.term
        else:
            return False, self.term

    def increment_vote(self):
        self.vote_count += 1
        if self.vote_count >= self.majority:
            with self.__lock:
                self.status = cfg.LEADER
                if self.q.empty():
                    self.q.put({'election': self})
                else:
                    election = self.q.get()
                    election.update({'election': self})
                    self.q.put(election)
            self.start_heartbeat()

    def start_heartbeat(self):
        '''
        If this node is elected as the leader, start sending
        heartbeats to the follower nodes
        '''
        # self.q.put({})
        # self.status == cfg.LEADER
        if self.store.staged:
            # logger.info(f"STAGED>>>>>>>>>>>, {self.store.staged}")
            if self.store.staged.get('delete', False):
                self.store.delete(self.term, self.store.staged,
                                  self.__transport, self.majority)
            else:
                self.store.put(self.term, self.store.staged,
                               self.__transport, self.majority)
        logger.info(f"I'm the leader of the pack for the term {self.term}")
        logger.debug('sending heartbeat to peers')
        for peer in self.peers:
            Thread(target=self.send_heartbeat, args=(peer,)).start()

    def send_heartbeat(self, peer: str):
        '''
        send the heartbeat the peer and analyze it's response

        :param peer: address of the follower node
        :type peer: str
        '''
        try:
            if self.store.log:
                self.update_follower_commit(peer)
            message = {'term': self.term, 'addr': self.__transport.addr}
            while self.status == cfg.LEADER:
                logger.debug(f'[PEER HEARTBEAT] {peer}')
                start = time.time()
                reply = self.__transport.heartbeat(peer=peer, message=message)
                if reply:
                    if reply['term'] > self.term:
                        self.term = reply['term']
                        self.status = cfg.FOLLOWER
                        self.init_timeout()
                delta = time.time() - start
                time.sleep((cfg.HB_TIME - delta) / 1000)
                logger.debug(f'[PEER HEARTBEAT RESPONSE] {peer} {reply}')
        except Exception as e:
            raise e

    def update_follower_commit(self, follower: str):
        '''
        update the followers log until it's log is in sync
        with the leader's log

        :param follower: address of the follower node in `ip:port` format
        :type follower: str
        '''
        first_message = {'term': self.term, 'addr': self.__transport.addr}
        second_message = {
            'term': self.term,
            'addr': self.__transport.addr,
            'action': 'commit',
        }
        reply = self.__transport.heartbeat(follower, first_message)
        cid = self.store.commit_id
        if reply:
            follower_cid = reply['commit_id']
            if follower_cid < self.store.commit_id:
                command_chunks = cfg.chunks(
                    list(self.store.log)[follower_cid:], 4)
                for chunk in command_chunks:
                    # while reply["commit_id"] < self.store.commit_id and abs(i) <= len(self.store.log):
                    second_message.update({'payload': chunk, 'commit_id': cid})
                    reply = self.__transport.heartbeat(
                        follower, second_message)

    def heartbeat_handler(self, message: dict) -> tuple:
        '''
        using this function, the follower node performs checks to validate the heartbeat
        data received from the leader

        :param message: heartbeat data as sent by the leader node
        :type message: dict

        :returns: term and latest commit_id of this (follower) node
        :rtype: tuple
        '''
        try:
            term = message['term']
            if self.term <= term:
                self.leader = message['addr']
                self.reset_timeout()
                logger.debug(f'got heartbeat from leader {self.leader}')
                if self.status == cfg.CANDIDATE:
                    self.status = cfg.FOLLOWER
                elif self.status == cfg.LEADER:
                    self.status = cfg.FOLLOWER
                    self.init_timeout()

                if self.term < term:
                    self.term = term

                if 'action' in message:
                    logger.debug(f'received command from leader {message}')
                    self.store.action_handler(message)
            return self.term, self.store.commit_id
        except Exception as e:
            raise e

    def handle_put(self, payload: dict) -> bool:
        '''
        Function to insert data into the database

        :param payload: data as received from the client
        :type payload: dict

        :returns: True if the data is inserted properly
                  False otherwise
        :rtype: bool
        '''
        reply = self.store.put(
            self.term, payload, self.__transport, self.majority)
        return reply

    def handle_get(self, payload: dict) -> dict:
        '''
        Retrieve data from the database

        :param payload: it contains `key` using which it's corresponding
                        value will be retrieved from the database
        :type payload: dict
        '''
        return self.store.get(payload)

    def handle_delete(self, payload: dict):
        return self.store.delete(self.term, payload, self.__transport, self.majority)

    def timeout_loop(self):
        '''
        if this node is not the leader, wait for the leader
        to send the heartbeat. If heartbeat is not received by the follower,
        within some unit time then start the election. This loop will
        run endlessly
        '''
        while self.status != cfg.LEADER:
            delta = self.election_time - time.time()
            if delta < 0:
                if self.__transport.peers:
                    self.start_election()
            else:
                time.sleep(delta)

    def init_timeout(self):
        '''
        initialize the timeout loop to check for missed
        heartbeats from the leader and start the election
        '''
        try:
            logger.info('starting timeout')
            self.reset_timeout()
            if self.timeout_thread and self.timeout_thread.is_alive():
                return
            self.timeout_thread = Thread(target=self.timeout_loop)
            self.timeout_thread.start()
        except Exception as e:
            raise e

    def reset_timeout(self):
        '''
        reset the election timeout after receiving heartbeat
        from the leader
        '''
        self.election_time = time.time() + cfg.random_timeout()
