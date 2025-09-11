import platform
import signal
import time
from subprocess import Popen

from psutil import NoSuchProcess, Process

from test_server import Response
from tests.util import only_grab_transport, skip_test_if, temp_file

SIGNAL_INT = signal.SIGINT


class BaseKeyboardInterruptTestCase(object):
    """
    I have no idea how to run this test on windows.
    Then I send CTRL_C_EVENT to process opened with Popen
    the whole testing process is hanged.
    """

    script_tpl = None

    @skip_test_if(lambda: platform.system() == "Windows", "windows platform")
    @only_grab_transport("pycurl")
    def test_sigint(self):
        """
        Setup test server sleep 0.01 for each request
        Start spider in separate python shell (untill sigin
            or max 200 requests)
        Wait 1 sec (~100 requests, in reality less
            because of process start-up time)
        Send SIGINT to the process
        Check it returned with 13 or 139 codes
        139 code means segfault (yeah...o_O) But as I see from logs
            it segfaults after successfully processing the SIGINT and
            this is all I need from this test
        """
        # logging.error('step-0')
        # pylint: disable=no-member
        self.server.add_response(Response(sleep=0.01), count=-1)
        # pylint: enable=no-member
        with temp_file() as path:
            with open(path, "w") as out:
                # pylint: disable=no-member
                out.write(self.script_tpl % ("", self.server.get_url()))
                # pylint: enable=no-member
            ret_codes = []
            for _ in range(10):
                # logging.error('step-1')
                proc = Popen("python %s" % path, shell=True)
                # logging.error('step-2')
                parent = Process(proc.pid)
                # logging.error('step-3')
                time.sleep(1)
                # logging.error('killing children')
                for child in parent.children():
                    # logging.error('CHILD: %s', child.pid)
                    # Sending multiple SIGINTs
                    # because in very rare cases the only
                    # sigint signals is ignored :-/
                    # do not send too fast
                    for _ in range(1):
                        try:
                            # logging.error('sending sigint')
                            child.send_signal(SIGNAL_INT)
                        except NoSuchProcess:
                            break
                        else:
                            time.sleep(1)
                if platform.system() == "Darwin":
                    # On OSX the Popen(shell=True) spawns only
                    # one process, no child
                    # logging.error('Killing parent')
                    # logging.error('PARENT: %s', parent.pid)
                    # Sending multiple SIGINTs
                    # because in very rare cases the only
                    # sigint signals is ignored :-/
                    # do not send too fast
                    for _ in range(1):
                        try:
                            # logging.error('sending sigint')
                            parent.send_signal(SIGNAL_INT)
                        except NoSuchProcess:
                            break
                        else:
                            time.sleep(1)
                # logging.error('step-4')
                ret = None
                for _ in range(20):
                    # print('before proc-poll-%d' % step)
                    ret = proc.poll()
                    if ret is not None:
                        break
                    time.sleep(0.1)
                else:
                    # logging.error('CHILD PROCESS DID NOT RETURN')
                    # raise Exception('Child process did not return')
                    # try to clean processes
                    try:
                        for child in parent.children():
                            child.send_signal(signal.SIGTERM)
                    except NoSuchProcess:
                        pass
                    time.sleep(0.5)
                    try:
                        parent.send_signal(signal.SIGTERM)
                    except NoSuchProcess:
                        pass
                # logging.error('step-5')
                # FIXME: find out the reasonf of segfault
                # the 130 signal means the program was terminated by ctrl-c
                # print('RET CODE: %s' % ret)
                ret_codes.append(ret)

            # Could fail in 10% (1 of 10)
            # pylint: disable=no-member
            self.assertTrue(sum(1 for x in ret_codes if x in (13, 130, 139)) >= 9)
            # pylint: enable=no-member
