import sys
class Iprods_Http_Utils:

    '''
    check if statuscode is in the range of the config http status codes
    e.g. 404 in the range between 400 and 499
    '''
    def isCodeInCodeRange(self, codes, code):
        result = False

        if code != '' :
            for level in self.REPORT_LEVEL.split(','):
                diff = -1
                try:
                    diff = int(code) - int(level)
                except ValueError:
                    exctype, value = sys.exc_info()[:2]
                    raise Exception("isCodeInCodeRange failed. exctype: %s, value: %s [code: %s, level: %s, diff %s]"  %  (exctype, value, code, level, diff))


                if diff > -1 and diff < 100:
                    result = True
                    break

        return result