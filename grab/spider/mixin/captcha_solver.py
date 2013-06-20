import logging
from ..task import Task
from grab.captcha import SolutionNotReady

logger = logging.getLogger('grab.spider.mixin.captcha_solver')

class CaptchaSolverInterface(object):
    def task_download_captcha(self, grab, task):
        logger.debug('Got captcha image')
        g_new = self.solver.backend.get_submit_captcha_request(grab.response.body)
        yield Task('submit_captcha', grab=g_new, meta=task.meta)

    def task_submit_captcha(self, grab, task):
        captcha_id = self.solver.backend.parse_submit_captcha_response(grab.response)
        g_new = self.solver.backend.get_check_solution_request(captcha_id)
        yield Task('check_solution', grab=g_new, delay=5, meta=task.meta)

    def task_check_solution(self, grab, task):
        try:
            solution = self.solver.backend.parse_check_solution_response(grab.response)
        except SolutionNotReady:
            logger.debug('SOLUTION IS NOT READY')
            yield task.clone(delay=task.original_delay)
        else:
            logger.debug('GOT CAPTCHA SOLUTION: %s' % solution)
            yield task.meta['handler'](solution, task.meta)


