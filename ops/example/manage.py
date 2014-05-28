from ops.service import manager

class TestManager(manager.Manager):

    def __init__(self, *args, **kwargs):
        print "i am init"

    @manager.periodic_task
    def test(self, raise_on_error=True):
        print "perioc\n"
