###
# $Date: 2010-05-06 16:26:06 $
# $Revision: 1.2 $
# $Author: ctietze $
# Remarks:
# reads the response from the url, extracts all intern and external links
#
###

import threading
import Queue
import sys
import re
import httplib
import time
from checker import Checker

class Reader(threading.Thread):
    result    = {}
    lock      = threading.Lock()
    queue     = Queue.Queue()
    #reportApp = None
    connection = None
    lastReader = 0

    def __init__(self, reportApp):
        threading.Thread.__init__(self)
        self.reportApp = reportApp
        self.log       = reportApp.getLogger()

    def run(self):
        while True:

            if self.reportApp.TIMEOUT:
                time.sleep(self.reportApp.TIMEOUT)

            url  = Reader.queue.get()
            data = self.getResponseData(url)

            self.extractLinks(data, url)

            #print time.time()
            self.reportApp.lastReader = time.time()

            Reader.lock.acquire()
            Reader.result[url] = 'OK'
            Reader.lock.release()
            Reader.queue.task_done()

    '''
    getResponseData
    '''
    def getResponseData(self, path):
        self.log.info(">>> getData [path: %s]" % (path))

        resLocation = ''
        resStatus = ''
        resReason = ''
        responseData = ''

        response = self.getResponse (path)

        if len(response) > 2:
            resLocation = response[0]
            resStatus   = response[1]
            resReason   = response[2]

            # save path or modified location
            if resLocation != path:
                self.reportApp.appendIntern(resLocation)
            self.reportApp.appendIntern(path)

            if resStatus >= 200 and resStatus < 300:
                responseData = response[3]
            else:
                #self.failedIntern.append(path)
                self.log.error("getData. Statuscode not in range [resLocation: %s, resStatus: %s, resReason: %s]. Skipped." % (resLocation, resStatus, resReason))

        else:
            #self.failedIntern.append(path)
            self.log.error("getData. Response Error [response: %s]. Skipped." % (response))
        # FI resStatus >= 200 and resStatus < 300:

        self.log.debug("<<< getData [len(responseData): %s]", len(responseData))

        return responseData

    '''
    get a tuple of response values
    '''
    def getResponse(self, path):
        self.log.debug(">>> getResponse [ path: %s]" % ( path))
        status = ''
        res = []

        headers = {"Connection": "keep-alive", "User-Agent": self.reportApp.USERAGENT}
        #if self.cookie is not None:
        #    headers['Cookie'] = self.cookie

        try:
            self.connect()
            #self.log.info(">>> getResponse [ path: %s, headers: %s]" % ( path, headers))
            self.connection.request('GET', path, None, headers=headers)
            response    = self.connection.getresponse()
            res = (path, response.status, response.reason, response.read())
            status = res[1]
            #print("[DOMAIN: %s, path: %s, status: %s]" % (self.DOMAIN, path, res[1]))
            #if self.cookie is None:
            #    self.cookie = response.getheader('set-cookie')

            #WebReportApp.log.debug("[cookie: %s, status: %s, path: %s]" % (self.cookie , status, path))
            # perform redirect to get page
            if status == 301 or status == 302:
                path = response.getheader("location")
                res = self.getResponse(path)
        except :
            self.close()
            exctype, value = sys.exc_info()[:2]
            self.log.exception("getResponse failed. path: %s, value: %s]"  %  (path, value))

        self.log.debug("<<< getResponse [status: %s]", status)
        return res

    '''
    close connection to host
    '''
    def close(self):
        if self.connection is not None:
            self.connection.close()

    '''
    establish connection to host
    '''
    def connect(self):
        if self.connection is None:
            self.connection  = httplib.HTTPConnection(self.reportApp.DOMAIN, 80, timeout=10)

    '''
    extract all links from the data string
    '''
    def extractLinks(self, responseData, path):
        #self.log.debug(">>> extractLinks [responseData: %s, path: %s]" % (responseData, path))
        self.log.debug(">>> extractLinks [path: %s]" % (path))

        # get all external and internal links and save them to a dictionary
        allLinks = re.findall("<a.*?href=\"(.*?)\".*?>", responseData)

        self.log.debug("extractLinks [allLinks: %s]" % (allLinks))
        for href in allLinks:
            href = href.strip()
            # TODO does not find "href="fooo.html"  or href.find("/nbg/") != -1 or href.find("/nbg/") != -1
            if (href.find("://") != -1 or href.find("www") != -1) and href.find(self.reportApp.DOMAIN) == -1:
                if href not in Checker.result:
                    self.setLink(Checker, href, "in progress")
                self.log.debug("-- extern [href: %s]" % (href))
            else:
                href = href.replace(self.reportApp.DOMAIN, "")
                href = href.replace("http://", "")
                href = href.replace("https://", "")

                if href.startswith('/') is False:
                    href = self.completeRelativePath(path, href)
                if href not in Reader.result and href.lower().startswith(self.reportApp.PATH.lower()) is True and self.ignoreLink(href) == False:
                    self.setLink(self, href, "progress")
                    self.log.debug("-- intern [href: %s]" % (href))
                else:
                    self.log.debug("--- ignored [link: %s]. Skipped." % (href))

        self.log.debug("<<< extractLinks")

        return allLinks

    def setLink(self, thread, key, value):

        thread.lock.acquire()
        thread.result[key] = value
        thread.lock.release()
        thread.queue.put(key)

    '''
    complete internal relative paths to get server absolute paths
    '''
    def completeRelativePath(self, parentPath, path):
        self.log.debug(">>> completeRelativePath [parentPath: %s,  path: %s]" % ( parentPath, path))

        getPosition  = path.find("?")
        if getPosition != -1:
            path = path[0:getPosition]

        hashPosition = path.find("#")
        if hashPosition != -1:
            path = path[0:hashPosition]

        # extract parent path
        if parentPath.endswith('/') is False:

            p = re.compile("^\/.*\/([^\/]+)$")
            result = p.findall( parentPath )
            if result:
                parentPath = parentPath.replace(result[0], '')

        if path.startswith( '../') is True:
            parentPath = parentPath[0:-1] if parentPath.endswith('/') else parentPath
            arrParent  = parentPath.split('/')
            arrNewPath = []
            for i in range(0, len(arrParent) - path.count('../')):
                arrNewPath.append(arrParent[i])

            relPath = '/'.join(arrNewPath) + '/' + path.replace("../","")
        else:
            relPath = parentPath + '' + path

        self.log.debug("<<< completeRelativePath [relPath: %s]" % (relPath))
        return relPath

        '''
    check a link against an include and exclude list
    '''
    def ignoreLink(self, link):
        self.log.debug(">>> ignoreLink [link: %s]" % (link))
        result     = True
        isIncluded = True

        # only check files, no directories
        if link.find(".") != -1:
            if len(self.reportApp.INCLUDE_FILETYPES) > 0:
                isIncluded = self.isLinkInList(self.reportApp.INCLUDE_FILETYPES, link.lower())

        if len(self.reportApp.EXCLUDE_PATTERN) > 0:
            isExcluded = self.isLinkInList(self.reportApp.EXCLUDE_PATTERN, link.lower())

        if isIncluded is True and isExcluded is False:
            result = False

        self.log.debug("<<< ignoreLink [result: %s]" % (result))
        return result

    def isLinkInList(self, list, link):
        result = False

        if len(list) > 0:
            for entry in list:
                entry = entry.lower()

                if link.find(entry) > -1:
                    result = True
                    self.log.debug("isLinkInList: matches [needle: %s, include: %s]" % (link, entry))
                    break
        return result
