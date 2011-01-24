Requirements
************

Python > 2.5.2
http://www.python.org/download/releases

To use smtp authentication over ssl you have to configure python with SSL

* Required package libssl-dev (e.g Ubuntu dapper)
$ ./configure --with-ssl
$ make
$ make install


Test enviroment
***************
Ubuntu 6.06 Python 2.6 with SSL (self compiled)
Ubuntu 7.04 Python 2.5.2
Ubuntu 8.10 Python 2.6.5


Before you start
****************
* check the following vars in the linkcrawler.py class and change
them for your needs

* CONFIG_PATH = "config"
* CONFIG_FILE_NAME = "application.cfg"
* LOG_FILE = "/tmp/linkcrawler.out"

* check the default settings in the config file

* Execute test_linkcrawler.py to run a unittest


Execute App
***********
* by shell
$ python linkcrawler.py [SITENAME]

* by crontab
$ crontab -e // edit crontab
// Example execute app once a month
0      0       1       *       *       /path-to-the-app/linkcrawler.py [SITENAME] >/dev/null 2>&1


Know open issues
****************
* Add missing unit-tests
* set log level at command line LOG_LEVEL
* set log level for every site separatly
* checkExternalLink: doesn't save double external links
* processedExtern: should be a dictionary to save the last valid response code