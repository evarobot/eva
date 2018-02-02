# encoding=utf-8

'''
配置以Docker运行时为准，开发环境自己cp config.py后修改
'''

import os
#from django.conf import settings

def init():
    #settings.configure()
    pass


class _ConfigLog(object):
    _log_level = 'INFO'
    log_to_file = True
    log_to_console = True
    log_path = '/var/log/viki_qa/'

    @property
    def log_level(self):
        lv = os.environ.get("LOG_LEVEL")
        return lv if lv != None else self._log_level


class _ConfigRedis:
    _host = "viki_redis"
    _port = 6379
    _db = 1

    @property
    def host(self):
        hst = os.environ.get("REDIS_HOST")
        return hst if hst != None else self._host

    @property
    def port(self):
        prt = os.environ.get("REDIS_PORT")
        return prt if prt!= None else self._port

    @property
    def db(self):
        d = os.environ.get("REDIS_DB")
        return d if d != None else self._db


class _ConfigMongo:
    _host = "127.0.0.1"
    _port = 27017
    _db = "viki"

    @property
    def host(self):
        hst = os.environ.get("MONGO_HOST")
        return hst if hst != None else self._host

    @property
    def port(self):
        prt = os.environ.get("MONGO_PORT")
        return int(prt) if prt!= None else self._port

    @property
    def database(self):
        d = os.environ.get("MONGO_DB")
        return d if d != None else self._db


class _ConfigApps(object):
    data_path = "/src/VikiQA/data"
    apps_path = os.path.join(data_path, "apps")


class _ConfigNeo4j:
    _host = "127.0.0.1"
    _port = 7474
    _namespace = "Cosmetics"

    @property
    def host(self):
        hst = os.environ.get("NEO4J_HOST")
        return hst if hst != None else self._host

    @property
    def port(self):
        prt = os.environ.get("NEO4j_PORT")
        return int(prt) if prt!= None else self._port

    @property
    def namespace(self):
        d = os.environ.get("NEO4j_NAMESPACE")
        return d if d != None else self._namespace


ConfigMongo = _ConfigMongo()
ConfigRedis = _ConfigRedis()
ConfigLog = _ConfigLog()
ConfigApps = _ConfigApps()
ConfigNeo4j = _ConfigNeo4j()
