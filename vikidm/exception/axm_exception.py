# coding=utf-8
# Copyright (C) 2017 AXMTEC.
# https://axm.ai/


"""
    自定义对话框管理系统的的异常模块
"""


class AXMException(Exception):
    """
    自定义的异常的基类
    """
    message = 'An unknown exception'

    def __init__(self, msg=None, **kwargs):
        self.kwargs = kwargs
        if msg is None:
            msg = self.message

        try:
            msg = msg % kwargs
        except Exception:
            msg = self.message
        self.message = msg
        super(AXMException, self).__init__(msg)


class AXMCustomServerinternalError(Exception):
    """
    自定义的服务器内部错误
    """
    message = u'自定义的服务器内部错误'

    def __init__(self, message=None):
        if message is not None:
            self.message = message

        super(AXMCustomServerinternalError, self).__init__(self.message)


class AXMNOTROOTNODEMessageError(AXMException):
    message = u'挂载agency下面的agent时候, self参数不是根节点实例对象'


class AXMTreeNodeDataMessageError(AXMException):
    message = u'创建树的节点信息时候, 初始化data数据不是类TreeNodeData的实例数据'


class AXMAddChildNodeMessageError(AXMException):
    message = u'创建孩子的孩子节点时候, 孩子节点也必须是类TreeNode实例'


class AXMAddChildNodeParentNodeMessageError(AXMException):
    message = u'创建孩子的孩子节点时候, 父亲节点不是字典类型'


class AXMAgentEventIDNoSameError(AXMException):
    message = u'当前意图栈的栈顶的EventID和传入到DM系统的意图ID不一样, 业务无法识别, ' \
              u'可能是压入到intent栈错误,无法获取最新的'


class AXMRouterPathOverapError(AXMException):
    message = u'RequestHandler子类建立的路由映射覆盖了之前的router_path=%(router_path)s ' \
              u'类名=%(class_name)s 的 路由路径,这样会导致请求调用不到旧的业务,建议重新设置新的路由路径 '


class AXMQADeleteAssociatedIntentError(AXMException):
    message = u'当删除QA文档时候,删除相关的意图引用时候出错, 意图名name=%(name)s ' \
              u'不存在MongoDB数据库的意图文档里面'


class AXMQAExistsError(AXMException):
    message = u'项目名称domain=%(domain)s,意图名称intent=%(intent)s, 已经存在在QA文档里面! ' \
              u'原因:当添加QA文档时候,QA文档的domain 加 intent字段是唯一的,因为一个意图' \
              u'一个意图可以被不同项目的不同qa引用,但是同一个项目只有一个qa引用一个意图' \



class AXMQAAssociatedSlotNameDuplicateError(AXMException):
    message = u'项目名称domain=%(domain)s,qa标题title=%(title)s,已经关联一个' \
              u'槽值associated_value_name=%(associated_value_name)s ,不允许重复关联! '


class AXMIntentExistsError(AXMException):
    message = u'项目名称domain=%(domain)s,意图名称name=%(name)s, 已经存在在Intent文档里面! ' \
              u'原因:Intent文档的domain 加 name字段是唯一的'


class AXMTreeNodeModelExistsError(AXMException):
    message = u'项目名称domain=%(domain)s,事件ID event_id=%(event_id)s, 已经存' \
              u'在TreeNodeModel文档里面! ' \
              u'原因:TreeNodeModel文档的domain 加 event_id字段是唯一的, 事件ID是唯一的' \
              u' 不然会出现问题'


class AXMSlotAssociatedValueNameError(AXMException):
    message = u'项目名称domain=%(domain)s,创建槽名称name=%(name)s的时候, 必须关联一个槽值! '


class AXMSlotAssociatedValueNameDuplicateError(AXMException):
    message = u'项目名称domain=%(domain)s,槽名称name=%(name)s,已经关联一个' \
              u'槽值associated_value_name=%(associated_value_name)s ,不允许重复关联! '


class AXMSlotDeleteAssociatedValueNotExistsError(AXMException):
    message = u'项目名称domain=%(domain)s,槽名称name=%(name)s,去除关联的' \
              u'槽值associated_value_name=%(associated_value_name)s ,的时候,关联的这个槽值已经不存在, ' \
              u'详情请查看Slot文档的values数组看看是否存在相关槽值的引用! '


class AXMDocumentModelExistsError(AXMException):
    message = u'项目名称domain=%(domain)s,名称name=%(name)s, 已经存在%(document_cls_name)s文档里面! ' \
              u'原因:%(document_cls_name)s文档的domain 加 name字段是唯一的'


class AXMValueDocumentModelRuleExistsError(AXMException):
    message = u'项目名称domain=%(domain)s,名称name=%(name)s, 匹配方式(人工规则) rule=%(rule)s,' \
              u'已经存在%(document_cls_name)s文档里面! ' \



class AXMValueDocumentModelRuleNotExistsError(AXMException):
    message = u'项目名称domain=%(domain)s,名称name=%(name)s, 匹配方式(人工规则) rule=%(rule)s,' \
              u'不存在%(document_cls_name)s文档里面! ' \



class AXMDocumentModelNotExistsError(AXMException):
    message = u'项目名称domain=%(domain)s,名称name=%(name)s, 不存在%(document_cls_name)s文档里面! ' \
              u'请查看是否创建'


class AXMDomainProjectNotExistsError(AXMException):
    message = u'项目名称 project_id=%(project_id)s不存在Domain文档里面!,查看是否不小心删除项目了 '


class AXMQANotExistsError(AXMException):
    message = u'项目名称domain=%(domain)s,意图名称intent=%(intent)s, ' \
              u'不存在在QA文档里面,请检查是否请求参数有误! '


class AXMIntentNotExistsError(AXMException):
    message = u'项目名称 domain=%(domain)s,意图名称 name=%(name)s 的不存在在Intent文档里面! ' \
              u'(比如创建qa时候,必须在Intent文档中存在相关的意图) '


class AXMSlotNotExistsError(AXMException):
    message = u'项目名称 domain=%(domain)s,槽名称 name=%(name)s 的不存在在Slot文档里面! ' \
              u'(比如创建qa时候,必须在Slot文档中存在相关的槽) '


class AXMJSONDataFormatError(AXMException):
    message = u'传递的JSON数据格式有误,请检查是否是正确的JSON格式!'


class AXMAddDomainProjectNameUniqueError(AXMException):
    message = u'Domain项目的英文名称 project_id= %(project_id)s ,中文名称name=%(name)s,该项目已经存在,' \
              u'因为项目名称中英文都是是唯一的!, 请你检查是否是其中条件之一项目名字冲突了'


class AXMDomainProjectNNotExistsError(AXMException):
    message = u'Domain项目的名称 project_id= %(project_id)s , name= %(name)s ,不存在!'


class AXMDomainProjectIdNNotExistsError(AXMException):
    message = u'Domain项目的名称 project_id= %(project_id)s,不存在!'


class AXMDNamedObjectExistsError(AXMException):
    message = u'Domain项目的名称 project_id= %(project_id)s , 的命名空间name_objects字段中已经存在type=%(type)s' \
              u',name=%(name)s 的NameObject文档'


class AXMNotAllowDeleteError(AXMException):
    message = u'不允许删除! 原因:它可能是被本项目下某个qa或者某个槽引用了'


class AXMUserRegisterPwdNotSameError(AXMException):
    message = u'两次输入的密码不匹配'


class AXMUserRegisterPwdLenError(AXMException):
    message = u'密码长度太短,密码至少5位起'


class AXMUserRegisterUserNameExistsError(AXMException):
    message = u'用户名 username=%(username)s 已存在'


class AXMUserRegisterUserNameNotExistsError(AXMException):
    message = u'用户名 username=%(username)s 不存在'


class AXMUserRegisterRoleNotExistsError(AXMException):
    message = u'role=%(role)s 无此角色'


class AXMUserRegisterPhoneFormatError(AXMException):
    message = u'手机号码格式错误'


class AXMUserLoginError(AXMException):
    message = u'用户名或者密码错误'


class AXMRoleNotAuthError(AXMException):
    message = u'角色 role=%(role)s 无此权限'





