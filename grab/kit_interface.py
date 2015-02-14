class GrabKitInterface(object):
    def __init__(self, grab):
        self.grab = weakref.proxy(grab)

    def select(self, *args, **kwargs):
        from grab.selector import KitSelector

        qt_doc = self.grab.transport.kit.page.mainFrame().documentElement()
        return KitSelector(qt_doc).select(*args, **kwargs)
