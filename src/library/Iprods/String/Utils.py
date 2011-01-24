class Iprods_String_Utils:
    '''
    parse string to boolean
    '''
    @classmethod
    def smart_bool(self, string):
        if string is True or string is False:
            return string

        string = str(string).strip().lower()
        return not string in ['false','f','n','0','']