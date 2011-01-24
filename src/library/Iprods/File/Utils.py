

from time import strftime

class Iprods_File_Utils:

    '''
    creates a valid filename
    '''
    @classmethod
    def getValidFileName(self, filename, addTimestamp):
        file_name = filename.replace(".", "-")

        if addTimestamp is True:
            file_name = "%s_%s" % (file_name, strftime("%Y%m%d_%H%M"))
        return file_name

    '''
    write data to file
    '''
    @classmethod
    def write2file(self, filename, data):
        file_object = open(filename, "w")
        file_object.write(data)
        file_object.close()