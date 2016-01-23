import logging
import multiprocessing

PARSER_PROCESS_JOIN_TIMEOUT = 3
logger = logging.getLogger('grab.spider.parser_pipeline')


class ParserPipeline(object):
    def __init__(self, bot, mp_mode, pool_size, shutdown_event,
                 network_result_queue, parser_result_queue,
                 requests_per_process):
        self.bot = bot
        self.mp_mode = mp_mode

        if not self.mp_mode:
            self.pool_size = 1
        else:
            if pool_size is not None:
                self.pool_size = pool_size
            else:
                self.pool_size = multiprocessing.cpu_count()
        self.shutdown_event = shutdown_event
        self.network_result_queue = network_result_queue
        self.parser_result_queue = parser_result_queue
        self.requests_per_process = requests_per_process

        self.parser_pool = []
        for x in range(self.pool_size):
            is_parser_idle, proc = self.start_parser_process()
            self.parser_pool.append({
                'is_parser_idle': is_parser_idle,
                'proc': proc,
            })

    def start_parser_process(self):
        if self.mp_mode:
            from multiprocessing import Process, Event
        else:
            from multiprocessing.dummy import Process, Event
        is_parser_idle = Event()
        if self.mp_mode:
            bot = self.bot.__class__(
                network_result_queue=self.network_result_queue,
                parser_result_queue=self.parser_result_queue,
                is_parser_idle=is_parser_idle,
                shutdown_event=self.shutdown_event,
                parser_requests_per_process=self.requests_per_process,
                parser_mode=True,
                meta=self.bot.meta)
        else:
            # In non-multiprocess mode we start `run_process`
            # method in new semi-process (actually it is a thread)
            # Because the use `run_process` of main spider instance
            # all changes made in handlers are applied to main
            # spider instance, that allows to suppport deprecated
            # spiders that do not know about multiprocessing mode
            bot = self.bot
            bot.network_result_queue = self.network_result_queue
            bot.parser_result_queue = self.parser_result_queue
            bot.is_parser_idle = is_parser_idle
            bot.shutdown_event = self.shutdown_event
            bot.parser_requests_per_process = self.requests_per_process,
            bot.meta = self.bot.meta
        proc = Process(target=bot.run_parser)
        if not self.mp_mode:
            proc.daemon = True
        proc.start()
        return is_parser_idle, proc

    def check_pool_health(self):
        for proc in self.parser_pool:
            if not proc['proc'].is_alive():
                self.bot.stat.inc('parser-pipeline-restore')
                logger.debug('Restoring died parser process')
                is_parser_idle, new_proc = self.start_parser_process()
                self.parser_pool.append({
                    'is_parser_idle': is_parser_idle,
                    'proc': new_proc,
                })
                self.parser_pool.remove(proc)

    def shutdown(self):
        for proc in self.parser_pool:
            if self.mp_mode:
                pname = proc['proc'].pid
            else:
                pname = proc['proc'].name
            logger.debug('Started shutdown of parser process: %s' % pname)
            proc['proc'].join(
                PARSER_PROCESS_JOIN_TIMEOUT)
            if proc['proc'].is_alive():
                if self.mp_mode:
                    print('Process %s does not respond. Finish him!' % pname)
                    proc['proc'].terminate()
                else:
                    # do nothing, because in
                    # non-mp mode parser threads
                    # have daemon=True flag
                    pass
            logger.debug('Finished joining parser process: %s' % pname)
