#!/usr/bin/python
'''
' $Date: 2010-05-10 14:48:13 $
' $Revision: 1.6 $
' $Author: ctietze $
' Remarks:
'''

import ConfigParser
import cStringIO
from email import encoders
import logging
import os
import smtplib, email
import sys

import time
from time import strftime

from library.Iprods.Http.Utils import Iprods_Http_Utils
from library.Iprods.File.Utils import Iprods_File_Utils
from library.Iprods.Date.Utils import Iprods_Date_Utils
from library.Iprods.String.Utils import Iprods_String_Utils

from checker import Checker
from reader import Reader

class LinkCrawler:

    CONFIG_PATH = "config"
    CONFIG_FILE_NAME = "application.cfg"

    LOG_FILE = "/tmp/linkcrawler.out"
    LOG_FORMAT = "%(asctime)s %(levelname)s: %(message)s"
    LOG_DATE = "%d.%m.%Y %H:%M:%S"
    LOG_LEVEL = logging.INFO

    countExcluded   = 0
    countDouble     = 0
    elapsedTime     = 0
    lastReader      = -1

    cookie = None
    connection = None

    processedIntern = []
    failedIntern    = []
    checkedIntern   = {}
    processedExtern = []
    statusCodes     = {}
    result          = {}

    log = logging.getLogger("LinkCrawler")

    '''
    ${classdocs}
    '''
    def __init__(self, sitename=None):
        logging.basicConfig(filename=self.LOG_FILE,level=self.LOG_LEVEL,format =self.LOG_FORMAT ,datefmt = self.LOG_DATE)
        self.log.debug(">> __init__")
        self.log.info("Start crawling....")

        configIsLoaded = self.loadConfiguration()

        if configIsLoaded:
            if sitename is not None:
                siteIsLoaded = self.loadConfigurationSite(sitename)
                if siteIsLoaded:
                    self.run()
            else:
                self.log.info("No sitename passed... waiting for input...")
        self.log.debug("<< __init__")

    '''
    load application configuration
    '''
    def loadConfiguration(self):
        self.log.debug(">>> loadConfiguration")

        try:
            config = ConfigParser.ConfigParser()
            configfile = os.getcwd( ) + "/" + self.CONFIG_PATH + "/" + self.CONFIG_FILE_NAME
            config.readfp(open(configfile))

            # read default configs
            self.SEND_REPORT    = Iprods_String_Utils.smart_bool(config.get('application', 'SEND_REPORT'))
            self.WRITE_REPORT   = Iprods_String_Utils.smart_bool(config.get('application', 'WRITE_REPORT'))
            self.VERBOSE_REPORT = Iprods_String_Utils.smart_bool(config.get('application', 'VERBOSE_REPORT'))
            self.LINK_DEPTH     = config.getint('application', 'LINK_DEPTH')
            self.REPORT_PATH    = config.get('application', 'REPORT_PATH')
            self.REPORT_LEVEL   = config.get('application', 'REPORT_LEVEL')
            self.USERAGENT      = config.get('application', 'USERAGENT')
            self.CHECK_EXTERNAL = config.get('application', 'CHECK_EXTERNAL')
            self.MAX_THREADS = config.getint('application', 'MAX_THREADS')

            self.TIMEOUT      = config.getfloat('application', 'TIMEOUT')
            self.HTTP_TIMEOUT = config.getint('application', 'HTTP_TIMEOUT')

            self.SMTP_SERVER   = config.get('application', 'SMTP_SERVER')
            self.SMTP_TTLS     = config.get('application', 'SMTP_TTLS')
            self.SMTP_PORT     = config.get('application', 'SMTP_PORT')
            self.SMTP_USERNAME = config.get('application', 'SMTP_USERNAME')
            self.SMTP_PASSWORD = config.get('application', 'SMTP_PASSWORD')

            self.MAIL_SUBJECT = config.get('application', 'MAIL_SUBJECT')
            self.MAIL_TO      = config.get('application', 'MAIL_TO')
            self.MAIL_FROM    = config.get('application', 'MAIL_FROM')
            self.MAIL_CC      = config.get('application', 'MAIL_CC')
            self.MAIL_BCC     = config.get('application', 'MAIL_BCC')

            self.log.info("application config loaded successfully... [SEND_REPORT: %s, WRITE_REPORT: %s, VERBOSE_REPORT: %s, LINK_DEPTH: %s, REPORT_PATH: %s, REPORT_LEVEL: %s, USERAGENT: %s, TIMEOUT: %s, HTTP_TIMEOUT: %s, SMTP_SERVER: %s, SMTP_TTLS: %s, SMTP_PORT: %s, SMTP_USERNAME: %s, MAIL_SUBJECT: %s, MAIL_TO: %s, MAIL_FROM: %s, MAIL_BCC: %s]" % (self.SEND_REPORT, self.WRITE_REPORT, self.VERBOSE_REPORT, self.LINK_DEPTH, self.REPORT_PATH, self.REPORT_LEVEL, self.USERAGENT, self.TIMEOUT, self.HTTP_TIMEOUT, self.SMTP_SERVER, self.SMTP_TTLS, self.SMTP_PORT, self.SMTP_USERNAME, self.MAIL_SUBJECT, self.MAIL_TO, self.MAIL_FROM, self.MAIL_BCC))

        except StandardError:
            config = None
            exctype, value = sys.exc_info()[:2]
            self.log.exception("loadConfiguration failed. exctype: %s, value: %s [file: %s]"  %  (exctype, value, self.CONFIG_FILE_NAME))

        self.log.debug("<<< loadConfiguration [config: %s]", config)
        return config

    def loadConfigurationSite(self, sitename):
        config = ''
        self.log.debug(">>> loadConfigurationSite [sitename: %s]" % (sitename))

        if sitename:
            try:
                config = ConfigParser.ConfigParser()
                configfile = os.getcwd( ) + "/" + self.CONFIG_PATH + "/" + sitename + ".cfg"
                config.readfp(open(configfile))

                if (config.has_section(sitename)):
                    # read site configs
                    self.DOMAIN = config.get(sitename, 'DOMAIN')
                    self.PATH = config.get(sitename, 'PATH')

                    if (config.has_option(sitename, 'MAX_THREADS')):
                        self.MAX_THREADS = config.getint(sitename, 'MAX_THREADS')
                    if (config.has_option(sitename, 'LINK_DEPTH')):
                        self.LINK_DEPTH = config.getint(sitename, 'LINK_DEPTH')
                    if (config.has_option(sitename, 'REPORT_LEVEL')):
                        self.REPORT_LEVEL = config.get(sitename, 'REPORT_LEVEL')
                    if (config.has_option(sitename, 'EXCLUDE_PATTERN') and len(config.get(sitename, 'EXCLUDE_PATTERN').strip()) > 0):
                        self.EXCLUDE_PATTERN = config.get(sitename, 'EXCLUDE_PATTERN').strip().split(",")
                    else:
                        self.EXCLUDE_PATTERN = ''
                    if (config.has_option(sitename, 'INCLUDE_FILETYPES') and len(config.get(sitename, 'INCLUDE_FILETYPES').strip()) > 0):
                        self.INCLUDE_FILETYPES = config.get(sitename, 'INCLUDE_FILETYPES').strip().split(",")
                    else:
                        self.INCLUDE_FILETYPES = ''

                    if (config.has_option(sitename, 'CHECK_EXTERNAL')):
                        self.CHECK_EXTERNAL = Iprods_String_Utils.smart_bool(config.get(sitename, 'CHECK_EXTERNAL'))
                    if (config.has_option(sitename, 'SEND_REPORT')):
                        self.SEND_REPORT = Iprods_String_Utils.smart_bool(config.get(sitename, 'SEND_REPORT'))
                    if (config.has_option(sitename, 'WRITE_REPORT')):
                        self.WRITE_REPORT = Iprods_String_Utils.smart_bool(config.get(sitename, 'WRITE_REPORT'))
                    if (config.has_option(sitename, 'VERBOSE_REPORT')):
                        self.VERBOSE_REPORT = Iprods_String_Utils.smart_bool(config.get(sitename, 'VERBOSE_REPORT'))

                    if (config.has_option(sitename, 'TIMEOUT')):
                        self.TIMEOUT = config.getfloat(sitename, 'TIMEOUT')
                    if (config.has_option(sitename, 'HTTP_TIMEOUT')):
                        self.HTTP_TIMEOUT = config.getint(sitename, 'HTTP_TIMEOUT')

                    if (config.has_option(sitename, 'SMTP_SERVER')):
                        self.SMTP_SERVER = config.get(sitename, 'SMTP_SERVER')
                    if (config.has_option(sitename, 'SMTP_TTLS')):
                        self.SMTP_TTLS = config.get(sitename, 'SMTP_TTLS')
                    if (config.has_option(sitename, 'SMTP_PORT')):
                        self.SMTP_PORT = config.get(sitename, 'SMTP_PORT')
                    if (config.has_option(sitename, 'SMTP_USERNAME')):
                        self.SMTP_USERNAME = config.get(sitename, 'SMTP_USERNAME')
                    if (config.has_option(sitename, 'SMTP_PASSWORD')):
                        self.SMTP_PASSWORD = config.get(sitename, 'SMTP_PASSWORD')
                    if (config.has_option(sitename, 'MAIL_SUBJECT')):
                        self.MAIL_SUBJECT = "%s - %s" % (config.get(sitename, 'MAIL_SUBJECT'), self.DOMAIN)
                    if (config.has_option(sitename, 'MAIL_FROM')):
                        self.MAIL_FROM = config.get(sitename, 'MAIL_FROM')
                    if (config.has_option(sitename, 'MAIL_TO')):
                        self.MAIL_TO = config.get(sitename, 'MAIL_TO')
                    if (config.has_option(sitename, 'MAIL_CC')):
                        self.MAIL_CC = config.get(sitename, 'MAIL_CC')
                    if (config.has_option(sitename, 'MAIL_BCC')):
                        self.MAIL_BCC = config.get(sitename, 'MAIL_BCC')

                    self.log.info("site configuration loaded successfully... [sitename: %s, SEND_REPORT: %s, WRITE_REPORT: %s, VERBOSE_REPORT: %s, LINK_DEPTH: %s, REPORT_PATH: %s, REPORT_LEVEL: %s, USERAGENT: %s, TIMEOUT: %s, HTTP_TIMEOUT: %s, SMTP_SERVER: %s, SMTP_TTLS: %s, SMTP_PORT: %s, SMTP_USERNAME: %s, MAIL_SUBJECT: %s, MAIL_TO: %s, MAIL_FROM: %s, MAIL_BCC: %s]" % (sitename, self.SEND_REPORT, self.WRITE_REPORT, self.VERBOSE_REPORT, self.LINK_DEPTH, self.REPORT_PATH, self.REPORT_LEVEL, self.USERAGENT, self.TIMEOUT, self.HTTP_TIMEOUT, self.SMTP_SERVER, self.SMTP_TTLS, self.SMTP_PORT, self.SMTP_USERNAME, self.MAIL_SUBJECT, self.MAIL_TO, self.MAIL_FROM, self.MAIL_BCC))

                else:
                    config = None
                    self.log.error("loadConfigurationSite failed. [sitename:%s]. " % (sitename))
            except StandardError:
                config = None
                exctype, value = sys.exc_info()[:2]
                self.log.exception("loadConfigurationSite failed. exctype: %s, value: %s [sitename: %s]"  %  (exctype, value, sitename))

        self.log.debug("<<< loadConfigurationSite [config: %s]", config)
        return config


    def run(self):
        self.log.debug(">>> run [DOMAIN: %s, path: %s]" % (self.DOMAIN, self.PATH))

        try:
            start     = time.time()
            printTime = start + 30
            isFinished = False

            reader_threads = [Reader(self) for i in range(self.MAX_THREADS)]
            for thread in reader_threads:
                thread.setDaemon(True)
                thread.start()

            if self.CHECK_EXTERNAL is True:
                checker_threads = [Checker(self) for i in range(self.MAX_THREADS)]
                for thread in checker_threads:
                    thread.setDaemon(True)
                    thread.start()

            Reader.lock.acquire()
            Reader.result[self.PATH] = "busy"
            Reader.lock.release()
            Reader.queue.put(self.PATH)

            while True:
                actTime  = time.time()
                lastTime = actTime - self.lastReader
                #either queues are empty or reached max idle time


                if round(printTime,0) <=  round(actTime,0):
                    Reader.lock.acquire()
                    lenReader = len(Reader.result)
                    Reader.lock.release()

                    Checker.lock.acquire()
                    lenChecker = len(Checker.result)
                    Checker.lock.release()
                    print "status [links-read: %s, external-links: %s]" % (lenReader, lenChecker)
                    printTime = actTime + 15

                if (lastTime > 30)\
                    and Reader.queue.empty() and (self.CHECK_EXTERNAL is False or Checker.queue.empty()):
                #print "status [readerIsEmpty: %s, checkerIsEmpty: %s, lastReader: %s, lastTime: %s]" % (Reader.queue.empty(), Checker.queue.empty(), self.lastReader, lastTime)
                    break;

            Checker.queue.join()

            self.elapsedTime = (time.time() - start)

            if self.VERBOSE_REPORT or self.WRITE_REPORT or self.SEND_REPORT:
                report = self.generateReport('text')
                csv    = self.generateReport('csv')
                logFilename = Iprods_File_Utils.getValidFileName(self.DOMAIN, True)
                txtFile     = "%s%s.txt" % (self.REPORT_PATH, logFilename)
                csvFile     = "%s%s.csv" % (self.REPORT_PATH, logFilename)

                if self.VERBOSE_REPORT:
                    print report

                if self.WRITE_REPORT:
                    try:
                        Iprods_File_Utils.write2file(txtFile, report)
                    except:
                        exctype, value = sys.exc_info()[:2]
                        self.log.exception("write2file failed. exctype: %s, value: %s [filename: %s, report: %s]"  %  (exctype, value, txtFile, report))
                    try:
                        Iprods_File_Utils.write2file(csvFile, csv)
                    except:
                        exctype, value = sys.exc_info()[:2]
                        self.log.exception("write2file failed. exctype: %s, value: %s [filename: %s, csv: %s]"  %  (exctype, value, csvFile, csv))

                if self.SEND_REPORT:
                    self.smtpsend(self.MAIL_FROM, self.MAIL_CC, self.MAIL_BCC,\
                        self.MAIL_TO, self.MAIL_SUBJECT, report, csvFile)

        except StandardError:
            exctype, value = sys.exc_info()[:2]
            self.log.exception("run failed exc: %s, val: %s"  %  (exctype, value))

        self.log.debug("<<< run")

    '''
    generate the link report
    '''
    def generateReport(self, type):
        self.log.debug(">>> generateReport [type: %s]", type)
        data = cStringIO.StringIO()

        if type == 'text':
            data.write("Date: %s" % strftime("%Y-%m-%d %H:%M:%S"))
            data.write("\nDomain: %s" % self.DOMAIN)
            data.write("\nPath: %s" % self.PATH)
            data.write("\nShow Statuscodes: %s" % self.REPORT_LEVEL)
            if (self.EXCLUDE_PATTERN):
                data.write("\nExclude pattern: %s" % self.EXCLUDE_PATTERN)
            data.write("\nElapsed time: %s (h:m:s)" % Iprods_Date_Utils.getInHMS(self.elapsedTime))
            data.write("\nResult [internal: %s, external: %s, excluded: %s, double: %s]" % (len(self.processedIntern), len(self.processedExtern), self.countExcluded, self.countDouble))

            data.write("\n\nInternal Failed:")

            if len(self.failedIntern) > 0:
                for internal in self.failedIntern:
                    data.write("\n%s" % internal)

            data.write("\n\nExternal Failed:")

            if len(self.statusCodes) > 0:
                #{'200' : { 'URL' : [EXTERNALLINK1, EXTERNALLINK2 ....] }, '404' : {'URL' : [....]}
                #for key in sorted(self.statusCodes):
                codes = self.REPORT_LEVEL.split(',')
                for code in sorted(self.statusCodes, reverse=True):

                    Iprods_Http_Utils.isCodeInCodeRange(codes, code)
                    if self.showStatusCode(code):
                        data.write("\n\nHTTP_STATUS_CODE: %s\n" % code)
                        urls = self.statusCodes[code]
                        for url in urls:
                            data.write("\nURL: %s\n" % url)
                            for external in urls[url]:
                                data.write("EXT: %s\n" % external)


        if type == 'csv':
            if len(self.statusCodes) > 0:
                data.write("HTTP_STATUS_CODE, URL, EXTERN")
                #{'200' : { 'URL' : [EXTERNALLINK1, EXTERNALLINK2 ....] }, '404' : {'URL' : [....]}
                for code in sorted(self.statusCodes, reverse=True):
                    if self.showStatusCode(code):
                        urls = self.statusCodes[code]
                        for url in urls:
                            for external in urls[url]:
                                data.write("\n%s, %s, %s" % (code, url, external))

        #if len(self.processedExtern) > 0:
            #p.write("\n\nProcessed internal links\n %s" % str(self.processedIntern))
        #	data.write("\n\nProcessed external links\n%s" % str(self.processedExtern))

        report = data.getvalue()
        data.close()
        self.log.debug("<<< generateReport [report: %s]", report)
        return report

    def __del__(self):
        self.log.debug(">> __del__")

        # close connection if not already done
        #self.close()

        #shutdown logger
        self.log.info("Finished. Application stops now.")
        self.log.debug("<< __del__")
        logging.shutdown()

    def smtpsend(self, mailFrom, mailTo, mailCC, mailBCC, mailSubject, text, file=None):
        self.log.debug(">>> smtpsend [mailFrom: %s, mailTo: %s, mailCC: %s, mailBCC: %s, mailSubject: %s, text: %s]"  %  (mailFrom, mailTo, mailCC, mailBCC, mailSubject, text))
        result = None
        try:
            msg  = email.MIMEMultipart.MIMEMultipart()
            body = email.MIMEText.MIMEText(text)

            msg.attach(body)

            if file is not  None:
                attachment = email.MIMEBase.MIMEBase('text', 'plain')
                attachment.set_payload(open(file).read())
                attachment.add_header('Content-Disposition', 'attachment', filename=os.path.basename(file))
                encoders.encode_base64(attachment)
                msg.attach(attachment)

            msg.add_header('Subject', mailSubject)
            msg.add_header('From', mailFrom)
            msg.add_header('To', mailTo)
            if mailCC: msg['Cc'] = mailCC
            if mailBCC: msg['Bcc'] = mailBCC

            # now send the message
            server = smtplib.SMTP(self.SMTP_SERVER, self.SMTP_PORT)
            server.ehlo()

            if self.SMTP_TTLS:
                server.starttls()

            if self.SMTP_USERNAME and self.SMTP_PASSWORD:
                server.login(self.SMTP_USERNAME, self.SMTP_PASSWORD)

            result = server.sendmail(msg['From'], [mailTo, mailCC, mailBCC], msg.as_string())
            server.close()
        except :
            exctype, value = sys.exc_info()[:2]
            self.log.error("smtpsend failed. exctype: %s, value: %s [server: %s, port: %s, ttls: %s, user: %s] [mailFrom: %s, mailTo: %s, mailCC: %s, mailBCC: %s, mailSubject: %s, text: %s]"  %  (exctype, value, self.SMTP_SERVER, self.SMTP_PORT, self.SMTP_TTLS, self.SMTP_USERNAME, mailFrom, mailTo, mailCC, mailBCC, mailSubject, text))

        self.log.debug("<<< smtpsend [senderrs: %s]", result)
        return result
#
    def getLogger(self):
        return self.log

    def appendIntern(self, path):
        self.processedIntern.append(path)

if __name__ == '__main__':
    if len(sys.argv) > 1:
        LinkCrawler(sys.argv[1])
    else:
        LinkCrawler()
