from raftnode.datastore.Idatastore import IDatastore


class MemoryStore(IDatastore):

    def __init__(self):
        self.__db = dict()

    def connect(self):
        return self.__db

    def put(self, key: str, value):
        try:
            self.__db.update({key: value})
        except Exception as e:
            raise e

    def get(self, key: str):
        try:
            data = self.__db.get(key, None)
            return data
        except Exception as e:
            raise e
