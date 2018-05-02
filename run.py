# coding=utf-8
import sys
import logging

import tornado.httpserver
from tornado.options import define, parse_command_line, options

from vikidm.libs.route import Route
from vikidm.controller import init_controllers
from vikidm.config import ConfigDM

from vikidm.config import ConfigLog
from vikicommon.log import init_logger
init_logger(level=ConfigLog.log_level, path=ConfigLog.log_path)
log = logging.getLogger(__name__)

reload(sys)
sys.setdefaultencoding("utf-8")

define("port", type=int, default=ConfigDM.port,
       help="the server port")
define("address", type=str, default=ConfigDM.host,
       help="the server address")
define("debug", type=bool, default=False,
       help="switch debug mode")
parse_command_line()

init_controllers()

urls = Route.routes()

application = tornado.web.Application(urls, cookie_secret="fa5012f23340edae6db5df925b345912", autoreload=True)
app_server = tornado.httpserver.HTTPServer(application, xheaders=True)
app_server.listen(options.port, options.address)
tornado.ioloop.IOLoop.instance().start()
