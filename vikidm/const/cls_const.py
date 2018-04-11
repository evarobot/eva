# coding=utf-8
# Copyright (C) 2017 AXMTEC.
# https://axm.ai/

"""
  这个模块定义了一些DM系统以类属性方式定义的枚举类型的常量
"""


class StateTranstion(object):
    """
    # 封装树节点的状态改变
    """
    SUCCESS = 'SUCCESS'
    FAILED = 'FAILED'
    TIMEOUT = 0.0


class AgentType(object):
    """
    # 封装agent 的真正的对话执行单元, 分为四种类型
    """
    INFORM = 'INFORM'    # 输出一个对话, 不求输入.如:欢迎光临
    EXPECT = 'EXPECT'    # 等待输入, 但不会事先有"请求" 输出. 如:系统启动后等待输入
    INPUT = 'INPUT'      # 有输出的"请求", 并且等待输入. 如:你叫什么名字?
    EXECUTE = 'EXECUTE'  # 负责 执行一段代码, 比如查询数据库


class BaseEnum(dict):
    """
    枚举基类
    """
    def __setattr__(self, attr, value):
        self[attr] = value

    def __getattr__(self, attr):
        return self[attr]

# 角色类型
Role = BaseEnum()
Role.PRJ_VISITOR = "prj_visitor"     # 访客
Role.SUPER_ADMIN = "super_admin"     # 超级管理员, 拥有所有项目的所有权限及用户管理权限
Role.PRJ_EDITOR = "prj_editor"       # 项目编辑人员


