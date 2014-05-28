import abc

class Base():
    __metaclass__ == abc.ABCMeta

    def __init__(self):
        pass

    @abc.abstractmethod
    def get_all_data(self):
        """
        get all data of this source and then store them in db
        """
