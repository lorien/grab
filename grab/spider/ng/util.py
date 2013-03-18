from multiprocessing import Process
from .parser import BaseParserSpider
from .generator import BaseGeneratorSpider

def create_process(spider_cls, result_queue, *args, **kwargs):
    # Create spider instance which will performe
    # actions specific to given role
    bot = spider_cls(result_queue, *args, **kwargs)

    # Return Process object binded to the `bot.run` method
    return Process(target=bot.run)


def build_generator_spider(spider_cls):
    """
    This method allow to create generator spider
    based on class of usual spider.

    Under the hood this method creates new class with
    custom `run` method which just calls `run_generator`
    method
    """

    class CustomGeneratorSpider(spider_cls, BaseGeneratorSpider):
        def run(self):
            self.run_generator()

    return CustomGeneratorSpider


def build_parser_spider(spider_cls):
    """
    This method allow to create parser spider
    based on class of usual spider.

    Nothing extra-special happens.
    We just inject get handler from original spider clas
    and mixes them with methods from BaseParserSpider
    """

    class CustomParserSpider(spider_cls, BaseParserSpider):
        pass

    return CustomParserSpider
