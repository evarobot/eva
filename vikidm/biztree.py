#!/usr/bin/env python
# encoding: utf-8

import json
import treelib
import logging
import pprint

from vikicommon.util import escape_unicode
from vikidm.context import Concept
from vikidm.config import ConfigDM
log = logging.getLogger(__name__)


class BizUnit(treelib.Node):
    STATUS_STACKWAIT = "STATUS_STACKWAIT"  # 栈中等待状态
    STATUS_TREEWAIT = "STATUS_TREEWAIT"
    STATUS_CANDICATE = "STATUS_CANDICATE"
    STATUS_TRIGGERED = "STATUS_TRIGGERED"
    STATUS_ACTION_COMPLETED = "STATUS_ACTION_COMPLETED"
    STATUS_ABNORMAL = "STATUS_ABNORMAL"
    STATUS_WAIT_ACTION_CONFIRM = "STATUS_WAIT_ACTION_CONFIRM"
    STATUS_WAIT_TARGET = "STATUS_WAIT_TARGET"
    STATUS_TARGET_COMPLETED = "STATUS_TARGET_COMPLETED"
    STATUS_AGENCY_COMPLETED = "STATUS_AGENCY_COMPLETED"

    STATUS_DELAY_EXIST = "STATUS_DELAY_EXIST"

    def __init__(self, identifier, tag, data):
        super(BizUnit, self).__init__(tag, identifier, data=data)
        self.set_state(self.STATUS_TREEWAIT)

    def execute(self):
        raise NotImplementedError

    def activate(self):
        if not self.is_root() and self.state != BizUnit.STATUS_ABNORMAL:
            self.set_state(BizUnit.STATUS_TRIGGERED)

    def set_state(self, value):
        self.state = value

    def reset_concepts(self, tree, context):
        pass

    def executable(self):
        return self.state in [BizUnit.STATUS_TRIGGERED, Agent.STATUS_TARGET_COMPLETED,
                            BizUnit.STATUS_ACTION_COMPLETED, BizUnit.STATUS_ABNORMAL,
                            BizUnit.STATUS_AGENCY_COMPLETED]

class AbnormalHandler(BizUnit):
    ABNORMAL_ACTION_TIMEOUT = "ABNORMAL_ACTION_TIMEOUT"
    ABNORMAL_ACTION_FAILED = "ABNORMAL_ACTION_FAILED"
    ABNORMAL_INPUT_TIMEOUT = "ABNORMAL_INPUT_TIMEOUT"

    def __init__(self, bizunit, type_):
        self.tag = "AbnormalHandler"
        self.identifier = "AbnormalHandler"
        self.set_state(BizUnit.STATUS_TRIGGERED)
        self.parent = None
        self.data = {
            'trigger_concepts': []
        }
        self.target_concepts = []
        self.trigger_concepts = []
        self._handler_finished = False

        self.handler = self._get_handler(bizunit, type_)
        self.handler.parent = self

    def reset_concepts(self, tree, context):
        pass

    def _get_handler(self, bizunit, type_):
        if type_ == self.ABNORMAL_ACTION_FAILED:
            return ActionFailedAgent(bizunit)
        elif type_ == self.ABNORMAL_ACTION_TIMEOUT:
            return ActionTimeoutAgent(bizunit)
        elif type_ == self.ABNORMAL_INPUT_TIMEOUT:
            return InputTimeoutAgent(bizunit)

    def is_root(self):
        return False

    def execute(self, stack, tree):
        if self._handler_finished:
            self._mark_abnormal_unit(stack, tree, stack._items[-2])
            self.state = BizUnit.STATUS_ACTION_COMPLETED
            return self.state

        # push handler unit
        self.handler.set_state(Agent.STATUS_TRIGGERED)
        stack.push(self.handler)
        self.state = BizUnit.STATUS_STACKWAIT
        self._handler_finished = True
        return self.state

    def _mark_abnormal_unit(self, stack, tree, abnormal_unit):
        parent = tree.parent(abnormal_unit.identifier)

        def is_abnormal(bizunit):
            is_agency_parent = bizunit == parent and not parent.is_root()
            if bizunit == abnormal_unit or is_agency_parent:
                return True
            return False

        for unit in reversed(stack._items[:-1]):
            if is_abnormal(unit):
                unit.set_state(BizUnit.STATUS_ABNORMAL)


class Agency(BizUnit):
    TYPE_CLUSTER = "TYPE_CLUSTER"  # no delay exit
    TYPE_TARGET = "TYPE_TARGET"
    TYPE_SEQUENCE = "TYPE_SEQUENCE"
    TYPE_ROOT = "TYPE_ROOT"

    def __init__(self, tag, data):
        super(Agency, self).__init__(data["id"], tag, data)
        self.trigger_child = None
        self._type = data['type']
        self._handler_finished = False

    def __str__(self):
        return self.tag.encode('utf8')


    @classmethod
    def get_agency(self, tag, data):
        if data['type'] == Agency.TYPE_ROOT:
            return Agency(tag, data)
        elif data['type'] == Agency.TYPE_CLUSTER:
            return ClusterAgency(tag, data)
        elif data['type'] == Agency.TYPE_TARGET:
            return TargetAgency(tag, data)

    def execute(self, stack, tree, context):
        # root节点。
        return self.STATUS_STACKWAIT

    @property
    def state(self):
        return self.data['state']

    def set_state(self, value):
        self.data['state'] = value

    def reset_concepts(self, tree, context):
        for child in tree.children(self.identifier):
            child.reset_concepts(tree, context)


class ClusterAgency(Agency):
    """"""
    def __init__(self, tag, data):
        super(ClusterAgency, self).__init__(tag, data)

    def execute(self, stack, tree, context):
        if self._handler_finished:
            self.set_state(BizUnit.STATUS_AGENCY_COMPLETED)
            return
        self.trigger_child.set_state(Agent.STATUS_TRIGGERED)
        stack.push(self.trigger_child)
        self.trigger_child = None
        self.set_state(BizUnit.STATUS_STACKWAIT)
        self._handler_finished = True



class TargetAgency(Agency):
    """"""
    def __init__(self, tag, data):
        super(TargetAgency, self).__init__(tag, data)
        self.event_id = data['event_id']
        self._default_handler_finised = False
        self._timer = None

    def executable(self):
        return self.state in [BizUnit.STATUS_TRIGGERED, Agent.STATUS_TARGET_COMPLETED,
                            BizUnit.STATUS_ACTION_COMPLETED, BizUnit.STATUS_ABNORMAL,
                            BizUnit.STATUS_AGENCY_COMPLETED, BizUnit.STATUS_WAIT_TARGET]

    def activate(self):
        if self.state not in [BizUnit.STATUS_ABNORMAL, BizUnit.STATUS_WAIT_TARGET]:
            self.set_state(BizUnit.STATUS_TRIGGERED)
        if self._is_default_node(self.active_child):
            self.set_state(BizUnit.STATUS_WAIT_TARGET)
        self.active_child = None

    def _is_default_node(self, bizunit):
        return len(bizunit.target_concepts) == 0 and len(bizunit.trigger_concepts) == 1

    def restore_context(self, context):
        context.update_concept(self._intent.key, self._intent)

    def execute(self, stack, tree, context):
        if self.state == BizUnit.STATUS_WAIT_TARGET:
            return
        self.active_child = None
        candicate_children = []
        self._intent = context["intent"]
        for bizunit in tree.children(self.identifier):
            if len(bizunit.trigger_concepts) > 1:
                # result node
                trigger_satisified = all([context.satisfied(c) for c in bizunit.trigger_concepts])
                if trigger_satisified:
                    self.active_child = bizunit
                    break
            else:
                if len(bizunit.target_concepts) == 0 and self._default_handler_finised == False:
                        # default node
                        self.active_child = bizunit
                        self._default_handler_finised = True
                        self.active_child.set_state(Agent.STATUS_TRIGGERED)
                        stack.push(self.active_child)
                        self.set_state(BizUnit.STATUS_STACKWAIT)
                        log.debug("WAIT_INPUT Agency({0})".format(self.tag))
                        return
                else:
                    # target node
                    targets_completed = all([context.dirty(c) for c in bizunit.target_concepts])
                    if not targets_completed:
                        candicate_children.append(bizunit)

        if self.state != BizUnit.STATUS_WAIT_TARGET:
            if self.active_child is None:
                self.active_child = candicate_children[0]
            self.active_child.state = Agent.STATUS_TRIGGERED
            stack.push(self.active_child)
            self.set_state(BizUnit.STATUS_STACKWAIT)


        #if focus_unit.state in [BizUnit.STATUS_DELAY_EXIST, BizUnit.STATUS_WAIT_TARGET]:


class Agent(BizUnit):
    TYPE_INPUT = "TYPE_INPUT"
    TYPE_INFORM = "TYPE_INFORM"

    def __init__(self, tag, data):
        data = {   # 用于tree.to_json(), 方便调试。
            'subject': data['subject'],
            'scope': data['scope'],
            'event_id': data['event_id'],
            'timeout': float(data['timeout']),
            'agency_entrance': data['agency_entrance'],
            'trigger_concepts': data['trigger_concepts'],
            'state': BizUnit.STATUS_TREEWAIT,
            'target_concepts': data['target_concepts']
        }

        self._trigger_concepts = list(self._deserialize_trigger_concepts(data))
        self._target_concepts = list(self._deserialize_target_concepts(data))
        self.type_ = Agent.TYPE_INPUT if self._target_concepts else Agent.TYPE_INFORM
        self.target_completed = False
        super(Agent, self).__init__(data["event_id"], tag, data)


    def activate(self):
        if self.state not in [BizUnit.STATUS_ACTION_COMPLETED, BizUnit.STATUS_ABNORMAL]:
            self.set_state(BizUnit.STATUS_TRIGGERED)

    def execute(self):
        """
        """
        if self.state == BizUnit.STATUS_TRIGGERED:
            log.debug("WAIT_CONFIRM Agent(%s)" % self.tag)
            self.set_state(BizUnit.STATUS_WAIT_ACTION_CONFIRM)
            return self.event_id
        elif self.state == BizUnit.STATUS_WAIT_ACTION_CONFIRM:
            self.set_state(BizUnit.STATUS_WAIT_TARGET)

    def reset_concepts(self, tree, context):
        parent = tree.parent(self.identifier)
        if parent.is_root() or parent.state == BizUnit.STATUS_TREEWAIT:
            for concept in self.trigger_concepts + self.target_concepts:
                if concept.life_type == Concept.LIFE_STACK and context.dirty(concept):
                    context.reset_concept(concept.key)
                    log.debug("RESET_CONCEPT [{0}]".format(concept.key))

    @property
    def subject(self):
        return self.data['subject']

    @subject.setter
    def subject(self, value):
        self.data['subject'] = value

    @property
    def scope(self):
        return self.data['scope']

    @scope.setter
    def scope(self, value):
        self.data['scope'] = value

    @property
    def event_id(self):
        return self.data['event_id']

    @event_id.setter
    def event_id(self, value):
        self.data['event_id'] = value

    @property
    def timeout(self):
        return self.data['timeout']

    @timeout.setter
    def timeout(self, value):
        self.data['timeout'] = value

    @property
    def agency_entrance(self):
        return self.data['agency_entrance']

    @property
    def trigger_concepts(self):
        return self._trigger_concepts

    @property
    def target_concepts(self):
        return self._target_concepts

    @property
    def state(self):
        return self.data['state']

    def set_state(self, value):
        self.data['state'] = value

    def _deserialize_trigger_concepts(self, data):
        for kv in data['trigger_concepts']:
            split_index = kv.find('=')
            key = kv[0: split_index]
            value = kv[split_index + 1:]
            yield Concept(key, value)

    def _deserialize_target_concepts(self, data):
        for key in data['target_concepts']:
            yield Concept(key)

    def __str__(self):
        return json.dumps(escape_unicode(self.data))


class DefaultHandlerAgent(Agent):
    def __init__(self, bizunit, data):
        data.update({
            'subject': '',
            'scope': '',
            'timeout': 0,
            'agency_entrance': False,
            'trigger_concepts': {},
            'state': '',
            'target_concepts': [],
        })
        self._trigger_concepts = []
        self._target_concepts = []
        super(DefaultHandlerAgent, self).__init__(data["event_id"], data)

    def execute(self):
        self.set_state(BizUnit.STATUS_WAIT_ACTION_CONFIRM)
        return self.event_id

    def reset_concepts(self, tree, context):
        pass


class ActionFailedAgent(DefaultHandlerAgent):
    def __init__(self, bizunit):
        data = {
            'event_id': 'FAILED|' + bizunit.event_id,
            'tag': 'FAILED|' + bizunit.event_id,
        }
        super(ActionFailedAgent, self).__init__(data["event_id"], data)


class InputTimeoutAgent(DefaultHandlerAgent):
    def __init__(self, bizunit):
        data = {
            'event_id': 'INPUT_TIMEOUT|' + bizunit.event_id,
            'tag': 'INPUT_TIMEOUT|' + bizunit.event_id,
        }
        super(InputTimeoutAgent, self).__init__(data["event_id"], data)


class ActionTimeoutAgent(DefaultHandlerAgent):
    def __init__(self, bizunit):
        data = {
            'event_id': 'ACTION_TIMEOUT|' + bizunit.event_id,
            'tag': 'ACTION_TIMEOUT|' + bizunit.event_id,
        }
        super(ActionTimeoutAgent, self).__init__(data["event_id"], data)


class BizTree(treelib.Tree):
    """ 业务配置树 """
    def __init__(self):
        super(BizTree, self).__init__()

    def add_subtree_from_json(self, json_subtree, parent):
        d_tree = json.loads(json_subtree)
        self._parse_node(d_tree, parent)

    def init_from_json(self, json_tree):
        self.add_subtree_from_json(json_tree, parent=None)

    def _parse_node(self, dict_node, parent):
        data = dict_node['data']
        tag = dict_node['data']['tag']
        if dict_node['children']:
            tr_node = Agency.get_agency(tag, data)
            self.add_node(tr_node, parent)
            for child in dict_node['children']:
                self._parse_node(child, tr_node)
        else:
            tr_node = Agent(tag, data)
            self.add_node(tr_node, parent)

    def __repr__(self):
        self.show()
        detail = pprint.pformat(json.loads(self.to_json(with_data=True)))
        return "--------------------------\n{0}".format(detail)
