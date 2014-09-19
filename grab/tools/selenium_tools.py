"""
Documentation:
* http://selenium.googlecode.com/svn/trunk/docs/api/py/webdriver/selenium.webdriver.common.action_chains.html
"""
import os
import logging
import time
import shutil
from selenium.webdriver.firefox.firefox_profile import FirefoxProfile
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import WebDriverException
from random import randint

from grab.util.py3k_support import *


def delete_dir(path):
    """
    Delete directory.
    """

    logging.debug('Deleting directory: %s' % path)
    for root, dirs, files in os.walk(path):
        for fname in files:
            os.unlink(os.path.join(root, fname))
        for _dir in dirs:
            shutil.rmtree(os.path.join(root, _dir))
    os.rmdir(path)


#def delete_selenium_profile(path):
    #"""
    #Delete temporary selenium profile directory.
    #"""

    #if os.path.exists(path):
        #if path.rstrip('/').endswith('webdriver-py-profilecopy'):
            #path = os.path.dirname(path)
        #delete_dir(path)


#def remove_old_profiles(tmp_dir, timeout):
    #"""
    #Delete any directory in given `tmp_dir` which looks like
    #firefox profile and which age is more than `timeout`.
    #"""

    #for fname in os.listdir(tmp_dir):
        #path = os.path.join(tmp_dir, fname)
        #age = time.time() - int(os.path.getctime(path))
        #if age > timeout:
            ## if firefox profile
            #if (os.path.exists(os.path.join(path, 'webdriver-py-profilecopy'))
                #or os.path.exists(os.path.join(path, 'prefs.js'))):
                #delete_dir(path)


def create_profile(path=None, user_agent=None, accept_language=None,
                   proxy=None, proxy_type=None, no_proxy_hosts=None,
                   download_directory=None,
                   download_content_type=None):
    """
    @paramDownload_content_type: CSV string
    """

    if path is not None:
        profile = FirefoxProfile(path)
    else:
        profile = FirefoxProfile()

    # Memory and cpu optimization
    profile.set_preference('browser.sessionhistory.max_total_viewers', 0)
    #profile.set_preference('browser.cache.memory.enable', False)
    #profile.set_preference('browser.cache.offline.enable', False)
    #profile.set_preference('browser.cache.disk.enable', False)
    profile.set_preference('browser.safebrowsing.enabled', False)
    profile.set_preference('browser.shell.checkDefaultBrowser', False)
    profile.set_preference('browser.startup.page', 0)
    profile.set_preference('dom.ipc.plugins.enabled.timeoutSecs', 15)
    profile.set_preference('dom.max_script_run_time', 10)
    profile.set_preference('extensions.checkCompatibility', False)
    profile.set_preference('extensions.checkUpdateSecurity', False)
    profile.set_preference('extensions.update.autoUpdateEnabled', False)
    profile.set_preference('extensions.update.enabled', False)
    profile.set_preference('network.http.max-connections-per-server', 30)
    profile.set_preference('network.prefetch-next', False)
    profile.set_preference('plugin.default_plugin_disabled', False)
    profile.set_preference('print.postscript.enabled', False)
    profile.set_preference('toolkit.storage.synchronous', 0)
    profile.set_preference('image.animation_mode', 'none')
    profile.set_preference('images.dither', False)
    profile.set_preference('content.notify.interval', 1000000)
    profile.set_preference('content.switch.treshold', 100000)
    profile.set_preference('nglayout.initialpaint.delay', 1000000)
    profile.set_preference('network.dnscacheentries', 200)
    profile.set_preference('network.dnscacheexpiration', 600)

    if user_agent is not None:
        profile.set_preference("general.useragent.override", user_agent)

    if accept_language is not None:
        profile.set_preference('intl.accept_languages', accept_language)

    if proxy is not None:
        logging.debug('Setting up proxy %s [%s]' % (proxy, proxy_type))
        server, port = proxy.split(':')
        if proxy_type == 'socks5':
            profile.set_preference("network.proxy.socks", server)
            profile.set_preference("network.proxy.socks_port", int(port))
        elif proxy_type == 'http':
            profile.set_preference("network.proxy.http", server)
            profile.set_preference("network.proxy.http_port", int(port))
        else:
            raise Exception('Unkown proxy type: %s' % proxy_type)
        profile.set_preference("network.proxy.type", 1)

    if no_proxy_hosts is not None:
        csv = ', '.join(no_proxy_hosts)
        profile.set_preference('network.proxy.no_proxies_on',
                               'localhost, 127.0.0.1, %s' % csv)

    if download_directory is not None and download_content_type is not None:
        profile.set_preference("browser.download.folderList", 2)
        profile.set_preference("browser.download.manager.showWhenStarting", False)
        profile.set_preference("browser.download.dir", download_directory)
        profile.set_preference("browser.helperApps.neverAsk.saveToDisk",
                               download_content_type)

    profile.update_preferences()
    return profile


def close_alert(browser, times=3):
    """
    Send ENTER keys which should close any alert/prompt/etc UI dialog window.
    By default, send multiple ENTER signals.
    """

    for x in xrange(times):
        try:
            ActionChains(browser).send_keys(Keys.ENTER).perform()
        except WebDriverException as ex:
            if 'Modal dialog present' in str(ex):
                logging.debug('Ignoring exception about modal dialog')
                pass
            else:
                raise


def safe_integer(value, default):
    try:
        int_value = int(value)
    except (ValueError, TypeError) as ex:
        logging.debug('Non-fatal error', exc_info=ex)
        int_value = 0
    if not int_value:
        int_value = default
    return int_value


def mouse_move(browser, sleep=0.1, absolute=False, x=None, y=None):
    """
    Move mouse to random location inside visible viewport.
    """

    # This thing is disabled because it seems selenium do not want to
    # maximize window until the page is loaded completely
    # It is enabled again because it anyway wait for something to
    # get window size and coordinates ))
    logging.debug('Maximizing window')
    browser.maximize_window()

    logging.debug('Getting viewport size and offset')
    # View is the visible area of web page

    # Find view size
    view_width = safe_integer(browser.execute_script('return window.innerWidth'), 200)
    view_height = safe_integer(browser.execute_script('return window.innerHeight'), 200)

    # Find view offset
    view_x = safe_integer(browser.execute_script('return window.pageXOffset'), 0)
    view_y = safe_integer(browser.execute_script('return window.pageYOffset'), 0)

    # Find left-top and right-bottom points of the view
    view_ltop = (view_x, view_y)
    view_rbottom = (view_x + view_width, view_y + view_height)
    logging.debug('Viewport coordinates: (%d, %d) - (%d, %d)' % (
        view_ltop[0], view_ltop[1],
        view_rbottom[0], view_rbottom[1]))

    # If x or y is not given then create random coordinates
    if x is None:
        x = randint(0, view_width)
    if y is None:
        y = randint(0, view_height)
    mode = 'absolute' if absolute else 'relative'
    logging.debug('Moving cursor to position (%s): (%d, %d)' % (mode, x, y))

    # If coordinates is not absolute then
    # find absolute position using viewport position
    if not absolute:
        x += view_x
        y += view_y

    # Get HTML document which position probably always is 0
    html_element = browser.find_element_by_xpath('//html')

    # Use move_to_element_with_offset instead move_by_offset
    # because move_by_offset accept relative coordinates
    ActionChains(browser).move_to_element_with_offset(html_element, x, y).perform()

    if sleep:
        time.sleep(sleep)


def click(browser, elem=None):
    """
    Just click at current cursor position.
    If `elem` is given then move cursor to its location and
    then click on it.
    """

    if elem:
        logging.debug('Moving cursor to element %s' % elem)
        ActionChains(browser).move_to_element(elem).perform()
        logging.debug('Clicking on element %s' % elem)
        elem.click()
    else:
        logging.debug('Clicking at current position')
        ActionChains(browser).click().perform()


def send_keys(browser, *keys):
    """
    Emulate typing on keyboard.
    Any key with length more than one character is treated as 
    attribute of `Keys` class i.e. "PAGE_DOWN" --> Keys.PAGE_DOWN
    """
    for key in keys:
        if len(key) > 1:
            code = getattr(Keys, key)
        else:
            code = key
        ActionChains(browser).send_keys(code).perform()
