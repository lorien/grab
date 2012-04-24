from Queue import PriorityQueue

class QueueBackend(PriorityQueue):
    def __init__(self, database, **kwargs):
        PriorityQueue.__init__(self, **kwargs)
