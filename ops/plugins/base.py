from ops.service import manager

class Base():

    def __init__(self):
        '''
        init this class
        '''
        pass

    def init_host(self):
        '''
        init this service
        '''
        pass

    @manager.periodic_task
    def get_all_data(self):
        """
        get all data of this source and then store them in db
        """
