import socket
import time
from queue import Queue
from json import JSONDecodeError, dumps, loads
from threading import Lock, Thread

from raftnode import cfg, logger


class Transport:

    def __init__(self, my_ip: str, timeout: int, queue: Queue):
        self.host, self.port = my_ip.split(':')
        self.port = int(self.port)
        self.addr = my_ip
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind((self.host, self.port))
        self.server.listen()
        self.peers = list()
        self.lock = Lock()
        self.q = queue
        Thread(target=self.ping, args=(timeout,)).start()

    def serve(self):
        '''
        :param election: instance of the Election class
        :type election: Election

        This function starts a socket server and listen endlessly to
        the clients. It also checks the message types and delegates the 
        message handling responsibility accordingly.

        Message types supported are:

        * add_peer: 
            this message type means that a new peer has popped up
            in the cluster and should be added to the peers list
            of this server
        * heartbeat: 
            the leader, once elected, sends heartbeats to the 
            follower nodes, notifying them that it is alive
            and running
        * vote_request: 
            when a leader is down or there is no leader
            in the network, any one node randomly
            becomes a candidate and sends out vote request
            to other nodes. The other nodes can either
            vote in favour or against the candidate node
        * ping: 
            every node pings every other node from it's peers list
            to check if the peer is alive or dead. If it's dead, this
            node will remove the peer from it's peers list
        * put: 
            message with type put is received from the client connected
            to this cluster. If this node is the leader, it will put the 
            data into the database. If it's not the leader, it will redirect the 
            request to the leader node and send the leader's response back
            to the client
        * get: 
            message with type get is received from the client connected
            to this cluster. If this node is the leader, it will retrieve
            the data from the database and give it back to the client. If
            it's not the leader, it will redirect the request to the leader node
            and send the leader's response back to the client
        * data: 
            this type of message is sent by the leader to the follower
            nodes along with the heartbeat. It contains the current term
            and the latest commit_id
        '''
        self.election = self.q.get()['election']
        while True:
            if not self.q.empty():
                election = self.q.get()
                if bool(election):
                    self.election = election
            if isinstance(self.election, dict):
                self.election = self.election['election']
            logger.debug(
                f'current membership status of this node: {self.election.status}')
            client, address = self.server.accept()
            try:
                msg = client.recv(1024).decode('utf-8')
            except ConnectionResetError as e:
                continue
            msg = self.decode_json(msg)
            if isinstance(msg, dict):
                msg_type = msg['type']
                if msg_type == 'add_peer':
                    all_peers = self.peers.copy()
                    msg.update({'sender': self.addr})
                    self.add_peer(msg)
                    client.send(self.encode_json(
                        {'type': 'add_peer', 'payload': all_peers}))
                elif msg_type == 'heartbeat':
                    term, commit_id = self.election.heartbeat_handler(
                        message=msg)
                    client.send(self.encode_json(
                        {'type': 'heartbeat', 'term': term, 'commit_id': commit_id}))
                elif msg_type == 'vote_request':
                    choice, term = self.election.decide_vote(
                        msg['term'], msg['commit_id'], msg['staged'])
                    client.send(self.encode_json(
                        {'type': 'vote_request', 'term': term, 'choice': choice}))
                elif msg_type == 'ping':
                    msg.update({'is_alive': True, 'addr': self.addr})
                    client.send(self.encode_json(msg))
                elif msg_type == 'peers':
                    if self.election.status == cfg.LEADER:
                        peers_response = {'type': 'peers'}
                        peers_response.update({'peers': self.peers})
                        client.send(self.encode_json(peers_response))
                    else:
                        reply = self.redirect_to_leader(self.encode_json(msg))
                        client.send(bytes(reply, encoding='utf-8'))
                else:
                    reply = self.__resolve_msg(msg)
                    if reply:
                        client.send(self.encode_json(reply))
            else:
                send_msg = 'hey there; from {}'.format(self.addr)
                client.send(bytes(self.addr, encoding='utf-8'))
            client.close()

    def __resolve_msg(self, msg: dict):
        try:
            msg_type = msg['type']
            if self.election.status == cfg.LEADER:
                client_response = {'type': msg_type}
                handler = getattr(self.election, f'handle_{msg_type}')
                reply = handler(msg)
                client_response.update({'data': reply})
                return client_response
            else:
                reply = self.redirect_to_leader(self.encode_json(msg))
                return self.decode_json(reply)
        except Exception as e:
            raise e

    def redirect_to_leader(self, message: dict):
        '''
        If this node is not the leader, this function will
        redirect the request along with the message to the
        leader of the cluster

        :param message: message to send to the client
        :param type: dict
        '''
        try:
            logger.info(
                f'[LEADER REDIRECT] redirecting to leader at address {self.election.leader}')
            leader_host, leader_port = (self.election.leader).split(':')
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((leader_host, int(leader_port)))
            s.send(message)
            leader_reply = s.recv(1024).decode('utf-8')
            return leader_reply
        except ConnectionRefusedError as e:
            return {'data': 'leader unavailable'}
        except AttributeError as e:
            if "object has no attribute" in e.args[0]:
                time.sleep(1)
        except ConnectionResetError as e:
            return {'data': 'connection reset by peer'}

    def __proxy_client(self, addr: str, message=None):
        if not message:
            message = {'type': 'echo', 'payload': 'whatsup?'}
        client = self.reconnect(addr)
        if not client:
            return
        client.send(self.encode_json(message))
        msg = client.recv(1024).decode('utf-8')
        client.close()
        return

    def req_add_peer(self, addr: str):
        '''
        When this node starts, it send out a message to all
        the peers to add itself in their peers list

        :param addr: address of this node in the format ip:port
        :type addr: str
        '''
        client = self.reconnect(addr)
        if not client:
            logger.info(f'Could not connect to peer {addr}')
            return
        message = self.encode_json({'type': 'add_peer', 'payload': self.addr})
        client.send(message)
        msg = client.recv(1024).decode('utf-8')
        reply = self.decode_json(msg)
        all_peers = reply['payload']
        with self.lock:
            self.peers.append(addr)
        if all_peers:
            with self.lock:
                for peer in all_peers:
                    self.peers.append(peer)
        self.peers = list(set(self.peers))

    def add_peer(self, message: dict):
        '''
        This functions adds any new peers to their list of peers

        :param message: message received from the new peer
        :type message: dict
        '''
        try:
            reciever_address = message['sender']
            new_peer = message['payload']
            if new_peer not in self.peers:
                with self.lock:
                    self.peers.append(new_peer)
            if self.election.status == cfg.LEADER:
                self.election.start_heartbeat()
        except Exception as e:
            raise e

    def reconnect(self, addr: str):
        '''
        This function tries to connect this node to the peer at address addr
        20 times. If the peer is not connected in 20 tries, it returns False

        :param addr: address of the other peer 
        :type addr: str
        '''
        i = 0
        # while i < 20:
        try:
            host, port = addr.split(':')
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.connect((host, int(port)))
            return client
        except ConnectionRefusedError:
            client.close()
            time.sleep(0.002)
            if addr in self.peers:
                with self.lock:
                    self.peers.remove(addr)
            del client
        except TimeoutError as e:
            logger.info(f'Timeout error connecting to peer {addr}')
            logger.info(f'Removing peer {addr} from list of peers')
            if addr in self.peers:
                with self.lock:
                    self.peers.remove(addr)
            client.close()
        except Exception as e:
            client.close()
            raise e
        # finally:
        #     i += 1
    # else:
    #     with self.lock:
    #             self.peers.remove(addr)
    #     return False

    def ping(self, timeout: float):
        '''
        send a ping message to all the peers in the peers list

        :param timeout: time interval after which all peers will get a ping
                        from this node
        :type timeout: float
        '''
        while True:
            if self.peers:
                logger.debug(f'peers >>> {self.peers}')
                for peer in self.peers:
                    Thread(target=self.echo, args=(peer,)).start()
            else:
                logger.debug('ping  >>> no peers to ping')
            time.sleep(timeout)

    def echo(self, peer):
        '''
        This function will send the ping message to the peer
        at the address `addr`

        :param peer: address of the peer in `ip:port` format
        '''
        try:
            client = self.reconnect(peer)
            if not client:
                return
            echo_msg = self.encode_json({'type': 'ping'})
            client.send(echo_msg)
            echo_reply = self.decode_json(client.recv(1024).decode('utf-8'))
            client.close()
            if echo_reply:
                logger.debug('ping  >>> {}'.format(echo_reply))
                if echo_reply['is_alive']:
                    return True
            return False
        except ConnectionResetError as e:
            logger.info(f'[ECHO]lost connection to peer {peer}')
            return None

    def heartbeat(self, peer: str, message: dict = None) -> dict:
        '''
        If this node is the leader, it will send a heartbeat message
        to the follower at address `peer`

        :param peer: address of the follower in `ip:port` format
        :type peer: str

        :param message: heartbeat message; it consists current term and
                        address of this node (leader node)
        :type message: dict

        :returns: heartbeat message response as received from the follower
        :rtype: dict
        '''
        try:
            client = self.reconnect(peer)
            if not client:
                return
            message.update({'type': 'heartbeat'})
            heartbeat_message = self.encode_json(message)
            client.send(heartbeat_message)
            heartbeat_reply = client.recv(1024).decode('utf-8')
            if bool(heartbeat_reply):
                heartbeat_reply = self.decode_json(heartbeat_reply)
            client.close()
            return heartbeat_reply
        except ConnectionResetError as e:
            logger.info(f'[HEARTBEAT]lost connection to peer {peer}')
            return None

    def vote_request(self, peer: str, message: dict = None):
        '''
        sends vote request to the peer and return vote response to
        this node

        :param peer: address of the peer in `ip:port` format
        :type peer: str

        :param message: vote message; this will be sent to the
                        other nodes
        :type message: dict

        :returns: vote response as received from the voter node
        :rtype: dict
        '''
        try:
            client = self.reconnect(peer)
            if not client:
                return
            message.update({'type': 'vote_request'})
            vote_request_message = self.encode_json(message)
            client.send(vote_request_message)
            vote_reply = self.decode_json(client.recv(1024).decode('utf-8'))
            client.close()
            return vote_reply
        except ConnectionResetError as e:
            logger.info(f'[VOTE REQUEST]lost connection to peer {peer}')
            return None

    def send_data(self, peer=None, message: dict = None):
        '''
        sends heartbeat data to the peer and returns response to
        this node

        :param peer: address of the peer in `ip:port` format
        :type peer: str

        :param message: heartbeat data message; it contains term
                        and latest commit_id
        :type message: dict

        :returns: vote response as received from the voter node
        :rtype: dict
        '''
        client = self.reconnect(peer)
        if not client:
            return
        message.update({'type': 'data'})
        data_message = self.encode_json(message)
        client.send(data_message)
        data_reply = self.decode_json(client.recv(1024).decode('utf-8'))
        client.close()
        return data_reply

    def encode_json(self, msg: dict) -> bytes:
        '''
        convert json to bytes object

        :param msg: message in dict format
        :type msg: dict

        :returns: json message converted to bytes
        :rtype: bytes
        '''
        if isinstance(msg, dict):
            return bytes(dumps(msg), encoding='utf-8')
        return msg

    def decode_json(self, msg):
        '''
        convert bytes object to json

        :param msg: bytes object as received from the client
                    or other node
        :type msg: bytes

        :returns: bytes message converted to json
        :rtype: dict
        '''
        if isinstance(msg, str):
            try:
                return loads(msg)
            except JSONDecodeError as e:
                logger.exception('JSON format incorrect {}'.format(msg))
            except Exception as e:
                raise e
        return msg
