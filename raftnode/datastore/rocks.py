from json import JSONDecodeError, dumps, loads
from os import getenv, makedirs, path

import rocksdb

from raftnode.datastore.Idatastore import IDatastore


class RockStore(IDatastore):

    '''
    A class that implements IDatastore. It enables storing the data
    into a database called rocksdb in (key, value) format

    :param database: name of the database; database will be created
                    if it doesn't exist, default=defaiult.db
    :type database: str

    :param data_dir: directory where the database files will be stored,
                    default=./data
    :type data_dir: dict

    :param config: rocksdb specific configurations
    :type config: dict
    '''
    def __init__(self, database: str = 'default.db', data_dir: str = 'data', config: dict = None):
        if not config:
            config = dict()
        self.__data_dir = getenv('DATA_DIR', path.join('.', data_dir))
        self.__check_data_dir()
        self.__config = rocksdb.Options()
        self.__set_config(config=config)
        self.__database = path.join(self.data_dir, database)

    @property
    def database(self):
        '''
        rocksdb database name
        '''
        return self.__database

    @property
    def data_dir(self):
        '''
        database files storage directory
        '''
        return self.__data_dir

    @property
    def encoding(self):
        '''
        bytes encoding property
        '''
        return 'utf-8'

    def __check_data_dir(self):
        if not path.exists(self.data_dir):
            makedirs(self.data_dir)

    def __set_config(self, config: dict = None):
        self.__config.create_if_missing = config.get('create_if_missing', True)
        self.__config.max_open_files = config.get('max_open_files', 300000)
        self.__config.max_background_flushes = config.get(
            'allow_concurrent_memtable_write', 100)
        self.__config.write_buffer_size = config.get(
            'write_buffer_size', 67108864)
        self.__config.max_write_buffer_number = config.get(
            'max_write_buffer_number', 100)
        self.__config.target_file_size_base = config.get(
            'target_file_size_base', 67108864)

        self.__config.table_factory = rocksdb.BlockBasedTableFactory(
            filter_policy=rocksdb.BloomFilterPolicy(10),
            block_cache=rocksdb.LRUCache(2 * (1024 ** 3)),
            block_cache_compressed=rocksdb.LRUCache(500 * (1024 ** 2)))

    def connect(self):
        '''
        create/connect to rocksdb database
        '''
        db = rocksdb.DB(self.database, self.__config)
        return db

    def put(self, key: str, value):
        '''
        insert values into rocksdb database

        :param key: name of the key
        :type key: str

        :param value: value to be inserted into
                    the database
        :type value: any
        '''
        db = None
        try:
            db = self.connect()
            key, value = self.__bytes_encode(key), self.__bytes_encode(value)
            db.put(key, value)
        except Exception as e:
            raise e
        finally:
            db = None

    def get(self, key: str) -> dict:
        '''
        retrieve data from database and return it 
        to the client

        :param key: key using which data will be retrieved from 
                    the database
        :type key: str

        :returns: data from the database in dictionary format
        :rtype: dict 
        '''
        db = None
        try:
            db = self.connect()
            key = self.__bytes_encode(key)
            value = db.get(key)
            if not value:
                return None
            return self.__bytes_decode(value)
        except Exception as e:
            raise e
        finally:
            db = None

    def __bytes_encode(self, data):
        if isinstance(data, str):
            return bytes(data, encoding=self.encoding)
        elif isinstance(data, (dict, list, tuple)):
            return bytes(dumps(data), encoding=self.encoding)
        else:
            raise TypeError(f'Invalid type {type(data)} passed')

    def __bytes_decode(self, data: bytes):
        data = data.decode(self.encoding)
        try:
            data = loads(data)
        except JSONDecodeError:
            pass
        return data
