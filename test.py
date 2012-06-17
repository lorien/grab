# coding: utf-8
import csv
import logging

from grab.spider import Spider, Task
from grab import Grab

class ElibSpider(Spider):
    
    initial_urls = ['http://elibrary.ru/querybox.asp?scope=newquery',]
      
    def prepare(self):
        #prepare file for writing
        self.result_file = csv.writer(open('result.txt', 'w'))

    def task_initial(self, grab, task):
        print 'ELibrary query page'
        ftext = 'example'
        grab.set_input('ftext',ftext.replace("\"\g",'#').encode('utf-8'))
       
        result_url = u'http://elibrary.ru/query_results.asp'
  
        yield Task('query', url=result_url)

    def task_query(self, grab, task):
        no_match = u'Не найдено статей, соответствующих запросу'
        if(grab.search(no_match)):
            print no_match
        print grab.xpath_text("//div[@id='thepage']")  

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
  
    bot = ElibSpider(thread_number=1)
    bot.run()
    
    #But this code works
    g = Grab()
    
    g.go('http://elibrary.ru/querybox.asp?scope=newquery')
    ftext = u'sql'
    g.set_input('ftext',ftext.replace("\"\g",'#').encode('utf-8'))
    g.submit(url = 'http://elibrary.ru/query_results.asp' )
    
    g.go('http://elibrary.ru/query_results.asp')
    no_match = u'Не найдено статей, соответствующих запросу'
    if(g.search(no_match)):
        print no_match
    print g.xpath_text("//div[@id='thepage']")  
