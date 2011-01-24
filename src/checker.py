###
# $Date: 2010-05-06 16:26:06 $
# $Revision: 1.2 $
# $Author: ctietze $
# Remarks:
# checks all external links which are in the queue
###

import threading
import Queue
import httplib
import sys
import urlparse
import time

class Checker(threading.Thread):
    result    = {}
    lock      = threading.Lock()
    queue     = Queue.Queue()
    reportApp = None

    def __init__(self, reportApp):
        threading.Thread.__init__(self)

        self.reportApp = reportApp
        self.log = reportApp.getLogger()

    def run(self,):
        while True:

            if self.reportApp.TIMEOUT:
                time.sleep(self.reportApp.TIMEOUT)

            url  = Checker.queue.get()
            code = self.getStatusCode(url)
            Checker.lock.acquire()
            Checker.result[url] = code
            Checker.lock.release()
            Checker.queue.task_done()

    '''
    get status code
    '''
    def getStatusCode(self, url):
        self.log.debug(">>> getStatusCode [url: %s]" % (url))
        url = url.strip()
        (scheme, netloc, path, params, query, fragment) = urlparse.urlparse(url)
        status = 400

        if netloc != '':
            try:
                if sys.version_info < (2,6):
                    conn = httplib.HTTPConnection(netloc, 80)
                else:
                    conn = httplib.HTTPConnection(netloc, 80, timeout=10)

                conn.request("HEAD", path)
                res    = conn.getresponse()
                status = res.status
                conn.close()
            except:
                exctype, value = sys.exc_info()[:2]
                self.log.exception("getStatusCode failed. [netloc: %s, path: %s, exctype: %s, value: %s]  "  %  (netloc, path, exctype, value))

        self.log.debug("<<< getStatusCode [status: %s]" % (status))
        return status