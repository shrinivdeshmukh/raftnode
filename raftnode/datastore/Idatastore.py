from abc import ABC, ABCMeta, abstractmethod


class IDatastore(ABC):

    @abstractmethod
    def put(self, key: str, value: str):
        '''
        Implement this function to insert data into database
        '''

    @abstractmethod
    def get(self, key: str):
        '''
        Implement this function to retrieve data from database
        '''

    @abstractmethod
    def connect(self):
        '''
        Implement this function to connect and interact
        with the database
        '''
