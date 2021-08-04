
import logging
import os


class Logging:
    def __init__(self, log_level, **kwargs):
        self.log_level = log_level
        self.logger = logging.getLogger()
        self.__log_params = kwargs.copy()
        if kwargs.get('filename', None):
            self.__check_log_dir(kwargs.get('filename'))

    def __check_log_dir(self, path: str):
        folder = os.path.dirname(path)
        if not os.path.exists(folder):
            os.makedirs(folder)

    def get_logger(self):
        logging.basicConfig(**self.__log_params, level=self.log_level,
                            format='%(asctime)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S')
        return self.logger
