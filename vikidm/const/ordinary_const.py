# coding=utf-8
# Copyright (C) 2017 AXMTEC.
# https://axm.ai/

"""
  这个模块定义了一些DM系统以普通类型的常量
"""


PROJECT_ROOT_EVENT_ID = "root_event_id"  # Project项目根节点的事件ID
AGENCY_EVENT_ID = "agency_event_id"  # Agency节点的事件ID
AGENCY_NAME = "agency"  # Agency 表示一个复杂业务
CLEAN_CONTEXT_INTERVAL_TIME = 15  # 对话上下文清理的时间间隔, 以秒为单位
CLEAN_CONTEXT_TIME_FACTOR = 1.0006  # 对话上下文清理的时间因子, 真正的清理时间是按 CLEAN_CONTEXT_INTERVAL_TIME 乘以因子
DM_NOT_IMPLEMENT = u"None--------------DM系统对当前意图暂时没有找到对应的处理, 可能还没创建对应的业务配置树"
CLEAN_INTENT_CONTEXT = u"None--------------当前意图的对话的上下文环境已经被清理"
LOG_LEVEL = 'DEBUG'  # 自定义的日志等级, 通过提升它的等级可以把自定义DEBUG的日志输出屏蔽掉
LOG_FILENAME = 'my_log.log'  # 自定义的日志输出文件
OUT_LOG = 1  # 1: 日志输出到控制台 2: 日志输出到文件 3:日志两者都会输出

DATABASE_CONNECT_ERROR = u'数据库连接错误, 请检查是否开启了数据库,并查看连接方式,比如用户名密码是否正确'

