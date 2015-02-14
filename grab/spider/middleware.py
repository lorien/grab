from grab.spider.error import StopTaskProcessing


class TestMiddleware(object):
    def process_response(self, spider, resp):
        raise StopTaskProcessing
        #return resp['task'].clone()
