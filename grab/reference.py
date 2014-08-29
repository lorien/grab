from grab.selector import XpathSelector


class Reference(object):
    def __init__(self, node, query=None, query_args=None):
        self._node = node
        self._query = query
        self._query_args = {} if query_args is None else query_args

    def __getattr__(self, key):
        return Reference(self._node, query=key)

    def _selector(self):
        return XpathSelector(self._node)

    def _text(self):
        return self._selector().select('.//%s' % self._query).text()

    def _node(self):
        return self._selector().node()

    #def __call__(self, **kwargs):
        #self.query_args.update(kwargs)
        #return self
