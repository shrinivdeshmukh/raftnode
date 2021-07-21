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
    parser.add_argument('-s', '--store', help=str(render_help('this option specifies the data storage layer; memory is the default') + '\n' + str(render_examples('DEFAULT: memory')) + '\n' + str(render_examples('EXAMPLE: --store memory'))),
                        choices=('memory', 'database'), default='memory')
    parser.add_argument(
        '-d', '--database', help=str(render_help('the database\'s name; the data will be kept in this database; Only if -—store is database will this option work.')) + '\n' + str(render_examples('DEFAULT: default.db')) + '\n' + str(render_examples('EXAMPLE: --database default.db')), default='default.db')
    parser.add_argument(
        '--ip', help=str(render_help("IP address of this machine;")) + '\n' + str(render_examples("FORMAT: IP:PORT")) + '\n' + str(render_examples("EXAMPLE: 192.168.0.101:5000")), required=True)
    parser.add_argument(
        '--peers', help=str(render_help('comma separated IP addresses of other nodes in the cluster')) + '\n' + str(render_examples('FORMAT: IP1:PORT1,IP3:PORT3...,IPn:PORTn')) + '\n' + str(render_examples('EXAMPLE: --peers 192.168.0.101:5000,192.168.0.102:5000,192.168.0.103:5000')), default=None)
    parser.add_argument('-t', '--timeout', help=str(render_help('if peers are given, this timeout number is the interval after which all peers will get a ping; if peers do not answer, they will be removed from this node.')
                                                    ) + '\n' + str(render_examples('DEFAULT: 1')) + '\n' + str(render_examples('EXAMPLE --timeout 0.5')), default=1)
    parser.add_argument(
        '-v', '--volume', help=str(render_help('the database files will be kept in this directory.')) + '\n' + str(render_examples('DEFAULT: ./data')) + '\n' + str(render_examples('EXAMPLE: --volume ./data')), default='data')
    args = parser.parse_args()

    if args.peers:
        peers = args.peers.split(',')
    else:
        peers = list()

    node = Node(my_ip=args.ip, peers=peers, timeout=args.timeout, store_type=args.store, database=args.database, data_dir=args.volume)
    node.run()


def render_help(msg: str):
    msg = bold(magenta(msg))
    return msg


def render_examples(msg: str):
    msg = yellow(msg)
    return msg


if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
