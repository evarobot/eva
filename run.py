# coding=utf-8
# Copyright (C) 2017 AXMTEC.
# https://axm.ai/

"""
    系统启动的主模块
"""


import tornado.web
import tornado.httpserver
import tornado.ioloop
import tornado.options as opt
import controller.base as base
import settings
import mongoengine as db
import log.axm_log as axm_log
import const.ordinary_const as ord_con

opt.define("port", default=9090, help="Run server on a specific port", type=int)
opt.define("host", default="192.168.0.98", help="Run server on a specific host")


class Application(tornado.web.Application):
    def __init__(self):
        handlers = base.collect_handlers()
        tornado.web.Application.__init__(self, handlers, **settings.tornado)

        # 连接mongodb数据库
        self.connect_mongodb()
        # DM对话框系统的数据库初始化
        self.dm_db_init()

    # 连接mongodb数据库
    def connect_mongodb(self):
        try:
            mongodb = settings.database["mongodb"]
            db.connect(db=mongodb["name"], host=mongodb["host"], port=mongodb["port"])
        except Exception as e:
            axm_log.AXMLogger().get_logger().error(ord_con.DATABASE_CONNECT_ERROR)
            axm_log.AXMLogger().get_logger().info(e)

    # DM对话框系统的数据库初始化
    def dm_db_init(self):
        import dm
        dm.dm_db_init()


def main():
    opt.parse_command_line()
    http_server = tornado.httpserver.HTTPServer(Application())
    http_server.listen(opt.options.port, opt.options.host)
    tornado.ioloop.IOLoop().instance().start()

if __name__ == "__main__":
    main()
