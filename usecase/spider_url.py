import setup_script
from grab.spider import Spider, Task
import logging

class CustomSpider(Spider):
    initial_urls = ['http://ezinearticles.com/?What-I-Learnt-Losing-%A360,000-My-First-Year-as-a-Full-time-Trader&id=50262']

    def task_initial(self, grab, task):
        print grab.xpath_text('//title')

logging.basicConfig(level=logging.DEBUG)
bot = CustomSpider()
bot.setup_cache(
    backend='mongo',
    database='spider_test',
)
bot.run()
