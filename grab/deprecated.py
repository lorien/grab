from grab.util.misc import deprecated

class DeprecatedThings(object):
    """
    This super-class contains all deprecated things that are
    still in Grab class for back-ward compatibility.
    """

    @deprecated(use_instead='grab.doc.text_search')
    def search(self, *args, **kwargs):
        return self.doc.text_search(*args, **kwargs)

    @deprecated(use_instead='grab.doc.text_assert')
    def assert_substring(self, *args, **kwargs):
        return self.doc.text_assert(*args, **kwargs)

    @deprecated(use_instead='grab.doc.text_assert_any')
    def assert_substrings(self, *args, **kwargs):
        return self.doc.text_assert_any(*args, **kwargs)
