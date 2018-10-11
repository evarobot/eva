# encoding=utf-8

'''
配置以Docker运行时为准，开发环境自己cp config.py后修改
'''

import os


class _ConfigDM(object):
    input_timeout = 10.0
    _host = "0.0.0.0"
    _port = 5000

    @property
    def host(self):
        host = os.environ.get("DM_HOST")
        return host if host is not None else self._host

    @property
    def port(self):
        port = os.environ.get("DM_PORT")
        return port if port is not None else self._port


class _ConfigLog(object):
    _log_level = 'INFO'
    log_to_file = True
    log_to_console = True
    # log_path = '/Users/bitmain/logs/VikiDM/'
    log_path = '/var/log/vikidm/'

    @property
    def log_level(self):
        lv = os.environ.get("LOG_LEVEL")
        return lv if lv is not None else self._log_level


class _ConfigMongo:
    _host = "127.0.0.1"
    _port = 27017
    _db = "viki"

    @property
    def host(self):
        hst = os.environ.get("MONGO_HOST")
        return hst if hst is not None else self._host

    @property
    def port(self):
        prt = os.environ.get("MONGO_PORT")
        return int(prt) if prt is not None else self._port

    @property
    def database(self):
        d = os.environ.get("MONGO_DB")
        return d if d is not None else self._db


ConfigMongo = _ConfigMongo()
ConfigLog = _ConfigLog()
ConfigDM = _ConfigDM()
