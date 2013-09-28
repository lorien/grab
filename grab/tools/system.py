def check_ares_support():
    import pycurl

    return 'c-ares' in pycurl.version
