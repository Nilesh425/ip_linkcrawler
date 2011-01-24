class Iprods_Date_Utils:

    '''
    format time
    '''
    @classmethod
    def getInHMS(self, seconds):
        minutes, seconds = divmod(seconds, 60)
        hours, minutes   = divmod(minutes, 60)
        time = "%02d:%02d:%02d" % (hours, minutes, seconds)

        return time