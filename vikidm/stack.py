# coding=utf-8
# Copyright (C) 2017 AXMTEC.
# https://axm.ai/

"""
对话框管理框架子模块
stack 逻辑控制的栈结构模块
"""

import dm.logic_tree
import dm.agency
import time
import dm.agent
import dm.logic_node
import utils.assist_class_utils
import decimal
import const.ordinary_const as axm_con


# 计算完成对话的时间花费的装饰器
def cal_finish_dialog_time_decorator(func):
    """
    @param func:函数对象实例
    """
    def _wrapper(*args, **kwargs):
        # 清理条件
        clean_condition = axm_con.CLEAN_CONTEXT_INTERVAL_TIME * axm_con.CLEAN_CONTEXT_TIME_FACTOR
        res = func(*args, **kwargs)
        finish_time = time.time()
        if isinstance(res, dm.agent.Agent):
            time_manager = dm.logic_node.DialogTimeIntervalManager()
            pre_timestamp = time_manager.add(res.from_which_agency, finish_time)
            if clean_condition < (decimal.Decimal(finish_time) - decimal.Decimal(pre_timestamp)):
                return utils.assist_class_utils.ReturnResultAssist(axm_con.CLEAN_INTENT_CONTEXT,res.from_which_agency)
        elif isinstance(res, dm.agency.Agency):
            pass

        return res
    return _wrapper


class Stack(object):
    """
     模拟栈
    """
    __slots__ = ['__items', '__name']
    _instance = {}

    def __init__(self, name='stack'):
        """
        @param name: 栈名字, 可以通过它获取,创建的是哪个栈
        """
        self.__items = []
        if name not in self._instance:
            self._instance[name] = self

    # 获取实例
    @classmethod
    def get_instance(cls, name):
        if name not in cls._instance:
            s_obj = Stack(name)
            cls._instance[name] = s_obj
            return s_obj
        return cls._instance[name]

    # 是否为空
    def is_empty(self):
        return self.__items == []

    # 入栈
    def push(self, item):
        self.__items.append(item)

    # 出栈
    def pop(self):
        if not self.is_empty():
            return self.__items.pop()

    # 返回栈顶元素
    def peek(self):
        return self.__items[len(self.__items) - 1]

    # 栈大小
    def size(self):
        return len(self.__items)


class StackController(object):
    """
     栈逻辑控制
    """
    def __init__(self):
        pass

    # 处理栈名为意图的执行流程
    @staticmethod
    def stack_name_intent_handler(intent_event_id_key_str):
        """
        @type  intent_event_id_key_str: 字符串类型
        @param intent_event_id_key_str: 以意图命名的事件ID的key
        """
        # 这个名为intent的栈, 存放的是当前intent执行流程, 获取当前栈顶的是单个agent还是agency,
        # 如果是单个agent,则直接获取意图的事件ID的key 字符串, 如果是agency就获取agency的事件ID的字符串(主agent的事件ID的key)
        # 这样才能知道当前执行流程是执行单个agent还是agency, 如果是agency的主agent,则会继续使用agency下的局部控制流程,
        # 注意在应该是返回栈顶元素,并弹出栈,这样才能永远知道栈顶元素意图永远是最新期望的intent
        # 注意创建时候这两个参数栈名一定要一样,不然会获取默认的
        intent_stack = Stack(name="intent").get_instance("intent")
        intent_stack.push(intent_event_id_key_str)

    # 过滤出除了intent以外的其他实体的concepts
    @staticmethod
    def filter_concepst_except_intent(concepts_dict):
        """
        @type  concepts_dict : dict
        @param concepts_dict : 概念集(从NLU模块或者其他模块传给DM的概念集, 概念集有可能包含了intent和实体)
        """
        new_concepts_dict = {}
        for key, value in concepts_dict.iteritems():
            if key == u'intent':
                continue
            new_concepts_dict[key] = value
        return str(new_concepts_dict)

    # 分发事件ID, 返回执行结果
    @classmethod
    @cal_finish_dialog_time_decorator
    def dispatcher(cls, concepts_dict_str):
        """
        @type  concepts_dict_str : string
        @param concepts_dict_str : 概念集(从NLU模块或者其他模块传给DM的概念集, 概念集有可能包含了intent和实体)
        """

        tree_root = dm.logic_tree.LogicTree().get_root_node()
        # 注意这时候从NLU模块或者其他模块传给DM的概念集, 概念集有可能包含了intent和实体
        if concepts_dict_str in tree_root:
            # 如果事件ID,直接在树根下, 要么是单个agent, 要么是复杂agency的主agent(即agency下的触发条件为意图,而不是实体)
            type_obj = tree_root[concepts_dict_str]
            if isinstance(type_obj['tree_node_obj'], dm.agency.Agency):
                # 返回agency下主agent(主意图)对象实例  "{u'intent': u'eat.query'}"
                # 对于复杂的agency, 因为后面使用这个agency的主agent的key, 所以暂时压栈,不弹出
                StackController.stack_name_intent_handler(concepts_dict_str)
                agency_obj = tree_root[concepts_dict_str]['tree_node_obj']
                # 返回主意图时候, 收集下执行顺序
                agency_obj.collect_execute_order(agency_children_dict=tree_root[concepts_dict_str])
                # 返回主agent
                return tree_root[concepts_dict_str][concepts_dict_str]['tree_node_obj']
            else:
                # 单个agent对象实例
                # 对于单个agent,因为马上就执行了,所以压栈和出栈,是同时的,所以省略
                return type_obj['tree_node_obj']
        else:
            # 如果这时候 concepts_dict_str 包含了intent和实体, 肯定是agency下的某个agent,比如
            # '{'intent': 'eat.query', 'location': '麦当劳'}' 这个概念集
            # 肯定是复杂的agency下的除了主agent(主意图外的)其他agent
            # 获取当前栈顶的意图事件ID的key, 才能决定现在该是执行那个意图下的流程
            concepts_dict = eval(concepts_dict_str)
            if u'intent' in concepts_dict:
                # 如果传入的概念集中包含了意图, 就不去栈中找了
                master_agent_event_id_key_str = str({u'intent': unicode(concepts_dict[u'intent'])})

                # 对于复杂的agency, 因为后面使用这个agency的主agent的key, 所以暂时压栈,不弹出
                StackController.stack_name_intent_handler(master_agent_event_id_key_str)

                # 返回主意图时候, 收集下执行顺序
                agency_obj = tree_root[master_agent_event_id_key_str]['tree_node_obj']
                agency_obj.collect_execute_order(agency_children_dict=tree_root[master_agent_event_id_key_str])

                concepts_dict_str = StackController.filter_concepst_except_intent(concepts_dict)
            else:
                # 如果没有,就要去栈中找到
                master_agent_event_id_key_str = Stack(name="intent").get_instance("intent").peek()
            if master_agent_event_id_key_str and master_agent_event_id_key_str in tree_root:
                if isinstance(tree_root[master_agent_event_id_key_str]['tree_node_obj'], dm.agency.Agency):
                    agency_children_dict = tree_root[master_agent_event_id_key_str]
                    agency_obj = agency_children_dict['tree_node_obj']
                    # 调用agency的局部控制流程
                    return agency_obj.local_controller(concepts_dict_str, master_agent_event_id_key_str,
                                                       agency_children_dict)

