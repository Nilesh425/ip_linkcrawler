#!/usr/bin/python
'''
' $RCSfile: test_LinkCrawler.py,v $
' $Source: /home/cvs/sc_webreport/src/test_LinkCrawler.py,v $
' $Date: 2010-05-10 14:48:13 $
' $Revision: 1.4 $
' $Author: ctietze $
' Remarks:
'''

import unittest
import sys
from linkcrawler import LinkCrawler

from library.Iprods.Http.Utils import Iprods_Http_Utils
from library.Iprods.File.Utils import Iprods_File_Utils
from library.Iprods.Date.Utils import Iprods_Date_Utils
from library.Iprods.String.Utils import Iprods_String_Utils

from checker import Checker
from reader import Reader

class SimplisticTest(unittest.TestCase):
    #def __init__(self):

    def test_getInHMS(self):
        print ">>> test_getInHMS"
        app = LinkCrawler()
        app.LOG_LEVEL = 10
        timeInHMS = Iprods_Date_Utils.getInHMS(3600)

        print "<<< test_getInHMS [seconds: 3600, timeInHMS: %s]\n" % (timeInHMS)
        self.failUnless(timeInHMS)

    def test_getUrlStatus(self):
        print ">>> test_getUrlStatus"
        app     = LinkCrawler()
        checker = Checker(app)
        configIsLoaded = app.loadConfigurationSite("unittest")

        if configIsLoaded is False:
            self.fail("load configuration failed")
        else:
            statusCode = checker.getStatusCode("http://www.google.de")

        print "<<< test_getUrlStatus [statusCode: %s]\n" % statusCode
        self.failUnless(statusCode)

    def test_loadConfiguration(self):
        print ">>> test_loadConfiguration"
        app = LinkCrawler()
        configIsLoaded = app.loadConfigurationSite("unittest")

        print "<<< test_loadConfiguration [configIsLoaded: %s]\n" % configIsLoaded
        self.failUnless(configIsLoaded)

    def test_isCodeInCodeRange_fail(self):
        print ">>> test_isCodeInCodeRange_fail"

        codes = "100,200,500"
        showCode = Iprods_Http_Utils.isCodeInCodeRange(codes, "405")

        print "<<< test_isCodeInCodeRange_fail [range: %s, code: 405, showCode: %s]\n" % (codes, showCode)
        self.failIf(showCode)

    def test_isCodeInCodeRange_success(self):
        print ">>> test_isCodeInCodeRange_success"

        codes = "100,200,500"
        showCode = Iprods_Http_Utils.isCodeInCodeRange(codes, "405")

        print "<<< test_isCodeInCodeRange_success [range: %s, code: 405, showCode: %s]\n" % (codes, showCode)
        self.failUnless(showCode)

    def test_smtpsend(self):
        print ">>> test_smtpsend"
        app = LinkCrawler()
        configIsLoaded = app.loadConfigurationSite("unittest")

        if configIsLoaded is False:
            self.fail("load configuration failed")
        else:
            sendResult = app.smtpsend("clemens.tietze@gms.de", "clemens.tietze@gmx.de", "", "", "Webreport Unittest test_smtpsend", "Lorem ipsum")

        print "<<< test_smtpsend [sendResult: %s]\n" % sendResult
        self.failIfEqual(sendResult, None)

    def test_write2file(self):
        print ">>> test_write2file"
        writeResult = True
        file = ""

        try:
            app = LinkCrawler()
            file = "%s%s.txt" % (app.REPORT_PATH, Iprods_File_Utils.getValidFileName("unittest"))
            Iprods_File_Utils.write2file(file, "Webreport Unittest test_write2file")
        except:
            writeResult = False
            exctype, value = sys.exc_info()[:2]
            print("exctype: %s, value: %s"  %  (exctype, value))

        print "<<< test_write2file [file: %s]\n" % (file)
        self.failUnless(writeResult)

    def test_extractLinks(self):
        print ">>> test_extractLinks"
        app    = LinkCrawler()
        reader = Reader(app)
        configIsLoaded = app.loadConfigurationSite("unittest")

        if configIsLoaded is False:
            self.fail("load configuration failed")
        else:
            response     = reader.getResponse('http://www.scandio.de')
            responseData = response[3]
            links = reader.extractLinks(responseData, 'http://www.scandio.de')

        print "<<< test_extractLinks [links: %s]\n" % links
        self.failUnless(links)

    def test_completeRelativePath(self):
        print ">>> test_completeRelativePath\n"
        app        = LinkCrawler()
        reader     = Reader(app)

        array = [['/en/de/index.html', '/aa/bb/index.htm']
                , ['/en/de/index.html', 'cc/dd/index.htm']
                , ['/en/de/index.html', '../cc/dd/index.htm']
                , ['/en/', 'search_iframe_en.htm']
                , ['/en/', '/search_iframe_en.htm']
                , ['/en/', '../search_iframe_en.htm']]

        for i in range(0, len(array)):
            relPath    = reader.completeRelativePath(array[i][0], array[i][1])
            print "test_completeRelativePath [path: %s, parent: %s, relPath: %s]\n" % (array[i][0],array[i][1],relPath)
            self.failUnless(relPath)

        print "<<< test_completeRelativePath \n"


if __name__ == '__main__':
    unittest.main()