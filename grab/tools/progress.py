import sys 
import logging

logger = logging.getLogger('grab.tools.progress')


class Progress(object):
    def __init__(self, step=None, total=None, stop=None, name='items', level=logging.DEBUG):
        if total is None and step is None:
            raise Exception('Both step and total arguments are None')
        if total and not step:
            step = int(total / 20) 
        if step == 0:
            step = total
        self.step = step
        self.count = 0 
        self.total = total
        self.stop = stop
        self.name = name
        self.logging_level = level

    def tick(self):
        self.count += 1
        if not self.count % self.step:
            if self.total:
                percents = ' [%d%%]' % int((self.count / float(self.total)) * 100)
            else:
                percents = ''
            logger.log(self.logging_level, 'Processed %d %s%s' % (self.count, self.name, percents))
        if self.count == self.stop:
            logger.log(self.logging_level, 'Reached stop value %d' % self.stop)
            sys.exit()
