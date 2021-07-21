"""Top-level package for raftnode."""

__author__ = """Shrinivas Vijay Deshmukh"""
__email__ = 'shrinivas.deshmukh11@gmail.com'
__version__ = '0.1.0'

from raftnode.log import Logging
from os import getenv

log_level = getenv('LOG_LEVEL', 'INFO')
logger = Logging(log_level).get_logger()

from raftnode import config as cfg
from raftnode.raftnode import RaftNode as Node