'''
配置以Docker运行时为准，开发环境自己cp config.py后修改
'''

import os


class _ConfigApp:
    input_timeout = 10.0
    _host = "127.0.0.1"
    _port = 9999
    _debug = "True"

    @staticmethod
    def init_app(app):
        pass

    @property
    def host(self):
        host = os.environ.get("DM_HOST")
        return host if host is not None else self._host

    @property
    def port(self):
        port = os.environ.get("DM_PORT")
        return port if port is not None else self._port

    @property
    def debug(self):
        debug = os.environ.get("DEBUG")
        return debug if debug is not None else self._debug


class _ConfigLog(object):
    _log_level = 'DEBUG'
    _log_path = '/var/logs/Eva'

    @property
    def log_level(self):
        lv = os.environ.get("LOG_LEVEL")
        return lv if lv is not None else self._log_level

    @property
    def log_path(self):
        lv = os.environ.get("LOG_LEVEL")
        return lv if lv is not None else self._log_path


class _ConfigData(object):
    _cache_data_path = "/var/data/Eva/caches"
    _model_data_path = "/var/data/Eva/models"
    _data_server_host = "127.0.0.1"
    _data_server_port = 8887

    @property
    def cache_data_path(self):
        path = os.environ.get("CACHE_DATA_PATH")
        path = path if path is not None else self._cache_data_path
        os.makedirs(path, exist_ok=True)
        return path

    @property
    def model_data_path(self):
        path = os.environ.get("MODEL_DATA_PATH")
        path = path if path is not None else self._model_data_path
        os.makedirs(path, exist_ok=True)
        return path


    @property
    def data_server_host(self):
        hst = os.environ.get("DATA_SERVER_HOST")
        return hst if hst is not None else self._data_server_host

    @property
    def data_server_port(self):
        hst = os.environ.get("DATA_SERVER_PORT")
        return hst if hst is not None else self._data_server_port


ConfigLog = _ConfigLog()
ConfigData = _ConfigData()
ConfigApp = _ConfigApp()
