"""
Miscelanious helpers which automote common tasks.
"""
import types

def paginate(xpath):
    """
    That decorator allows you automatically iterates
    over Next links in the list of objects.

    Example of usage::

        @paginate('//a[text="Next"]')
        def task_search(self, grab, task):
            for elem in grab.xpath_list('//div[@class="product"]/h3/a'):
                yield Task('product', url=elem.get('href'))
    """

    def decorator(func):
        def fantom(self, grab, task):
            result = func(self, grab, task)
            if isinstance(result, types.GeneratorType):
                for item in result:
                    yield item
            else:
                yield result
            yield self.next_page_task(grab, task, xpath)
        return fantom
    return decorator
