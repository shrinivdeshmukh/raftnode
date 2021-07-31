"""Console script for raftnode."""
import argparse
import sys
from fabulous.color import bold, green, yellow, magenta, highlight_red
from fabulous import color
from raftnode import Node

def main():
    """Console script for raftnode."""
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('-d', '--database', help=str(render_help('If True, the data will be stored in a persistent rocksdb database; otherwise, the data will be stored in an in-memory python dictionary.') + '\n' + str(render_examples('Default: False'))),
                        action="store_true", default=False)
    parser.add_argument(
        '--ip', help=str(render_help("IP address of this machine;")) + '\n' + str(render_examples("Format: IP:PORT")) + '\n' + str(render_examples("Example: 192.168.0.101:5000")), required=True)
    parser.add_argument(
        '--peers', help=str(render_help('comma separated IP addresses of other nodes in the cluster')) + '\n' + str(render_examples('Format: IP1:PORT1,IP3:PORT3...,IPn:PORTn')) + '\n' + str(render_examples('Example: --peers 192.168.0.101:5000,192.168.0.102:5000,192.168.0.103:5000')), default=None)
    parser.add_argument('-t', '--timeout', help=str(render_help('if peers are given, this timeout number is the interval (in seconds) after which all peers will get a ping; if peers do not answer, they will be removed from this node.')
                                                    ) + '\n' + str(render_examples('Default: 1')) + '\n' + str(render_examples('Example --timeout 0.5')), default=1)
    parser.add_argument(
        '-v', '--volume', help=str(render_help('the database files will be kept in this directory.')) + '\n' + str(render_examples('Default: ./data')) + '\n' + str(render_examples('Example: --volume ./data')), default='data')
    args = parser.parse_args()

    store_type = 'memory'
    
    if args.peers:
        peers = args.peers.split(',')
    else:
        peers = list()

    if args.database:
        store_type = 'database'
        

    node = Node(my_ip=args.ip, peers=peers, timeout=args.timeout, store_type=store_type, data_dir=args.volume)
    node.run()

def render_help(msg: str):
    msg = bold(magenta(msg))
    return msg


def render_examples(msg: str):
    msg = yellow(msg)
    return msg


if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
