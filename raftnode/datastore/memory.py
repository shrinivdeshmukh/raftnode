from raftnode.datastore.Idatastore import IDatastore


class MemoryStore(IDatastore):

    '''
    A class that implements IDatastore. It is responsible
    for storing data in-memory and retrieving it 
    using python dictionary
    '''

    def __init__(self):
        self.__db = dict()

    def connect(self):
        '''
        create/connect to the in-memory data store
        '''
        return self.__db

    def put(self, key: str, value):
        '''
        insert values into the in-memory datastore

        :param key: key using which data will be stored
                    in the dictionary
        :type key: str

        :param value: the actual data to be stored in the
                    dictionary
        :type value: any
        '''
        try:
            self.__db.update({key: value})
        except Exception as e:
            raise e

    def get(self, key: str) -> dict:
        '''
        fetch data form the in-memory datastore

        :param key: key using which data will be fetched from the
                    dictionary
        :type key: str

        :returns: data in dictionary format
        :rtype: dict
        '''
        try:
            data = self.__db.get(key, None)
            return data
        except Exception as e:
            raise e
