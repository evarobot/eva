#!/usr/bin/env python
# encoding: utf-8
import logging
import datetime
import threading

from evadm.context import Slot
from evadm.dm import DialogEngine
from evadm.util import cms_gate, nlu_gate, data_gate
from evadm.chat import CasualTalk
from evashare.util import time_now

log = logging.getLogger(__name__)


class DMRobot(object):
    """
    Every DMRobot instance corresponds to a device.
    """
    robots_pool = {}

    def __init__(self, robot_id, domain_id, domain_name):
        self.domain_id = domain_id
        self.domain_name = domain_name
        self.robot_id = robot_id
        self._dm = DialogEngine.get_dm("0.1")
        self._dm.init_from_db(self.domain_id)
        log.info("CREATE ROBOT: [{0}] of domain [{1}]"
                 .format(robot_id, self.domain_name))

    def _parse_question(self, question):
        """
        Convert question to intent, slots, slots with NLU.
        """
        question = question.strip(' \n')
        context = self.get_context()
        ret = nlu_gate.predict(self.domain_id, context, question)
        return ret["intent"], ret["slots"], ret["related_slots"]

    def _get_context_slots(self, intent):
        """
        Return slots correspond to all dirty slots in Context.
        """
        slots = {}
        ret2 = cms_gate.get_intent_slots_without_value(self.domain_id, intent)
        if ret2['code'] != 0:
            log.error("调用错误")
        else:
            for slot_name in ret2['slots']:
                value = self._dm.context[slot_name].value
                if value:
                    slots[slot_name] = value
        return slots

    def process_question(self, question, sid, conn_id=None):
        """ Process question from device.

        It will parse question to (`Intent`, Slots, Slots) with NLU and
        query database or call thirdparty service.

        Parameters
        ----------
        question : str, question text from human being.
        sid : str, session id.
        conn_id: str, websocket id

        Returns
        -------
        dict.

        """
        # if rpc, pass robot id
        intent, d_slots, related_slots = self._parse_question(question)
        ret = {
            "code": 0,
            "sid": "",
            "response": {
                "tts": "噪音导致的胡话",
                "web": {}
            },
            "event": {
                "intent": intent,
                "slots": {}
            },
            "nlu": {
                "intent": intent,
                "slots": {}
            }
        }
        if intent in [None, "nonsense"]:
            # When intent is invalid in current context, NLU return None.
            return ret
        if intent == "sensitive":
            ret["response"]["tts"] = "很抱歉，这个问题我还不太懂。"
            return ret

        slots = [Slot("intent", intent)]
        for slot_name, value_name in d_slots.items():
            slots.append(Slot(slot_name, value_name))
        ret = self._process_slots(slots, sid, intent)

        d_slots = {}
        for s_slot in related_slots:
            slot = self._dm.context[s_slot]
            if slot.value is not None:
                d_slots[slot.key] = slot.value

        ret["nlu"] = {
            "intent": intent,
            "slots": d_slots
        }
        ret["event"]["slots"] = d_slots
        if intent == "casual_talk":
            if self._is_manual_online():
                log.info('manual is online, send question to human agent')
                # 转人工，同时返回转人工标志
                ret["event"]["intent"] = "manual_talk"
                self.manual_talk(self.domain_id, self.robot_id, sid,
                                 question, ret, conn_id)
            else:
                tuling_answer = CasualTalk.get_tuling_answer(question)
                ret["response"]["tts"] = tuling_answer
                self.save_session(sid, question, tuling_answer, time_now(),
                                  intent)
        else:
            answer = ret["response"]["tts"]
            self.save_session(sid, question, answer, time_now(), intent)
        return ret

    def save_session(self, sid, question, answer, question_datetime, intent,
                     answer_timeout=False):
        """ Every session needs to to be saved.

        Parameters
        ----------
        sid : str, session id.
        question : str, question text from human being.
        answer ：str, answer by evadm, tuling, or human agent
        question_datetime: str, question time by client
        intent: str, intent
        answer_timeout: bool, set True if manual talk time out

        Returns
        -------
        bool.
        to tell if save success
        """
        params = {
            "domain_id": str(self.domain_id),
            "question": question,
            "answer": answer,
            "answerer": 'default_user',
            "question_datetime": question_datetime,
            "answer_datetime": time_now(),
            "machine_intent": intent,
            "robot_id": self.robot_id,
            "sid": str(sid),
            "answer_timeout": answer_timeout
        }
        return data_gate.save_session(**params)

    def _is_manual_online(self):
        """ Check to see if the manual is online
        Returns
        -------
        bool.
        """
        return cms_gate.check_human_agent_status('default_user')

    def response_check(self, sid):
        """ Check to see if the question has been answered
        Parameters
        ----------
        sid : str, session id.

        Returns
        -------
        bool.
        """
        return data_gate.is_session_complete(sid)

    def delay_task(self, session_info):
        """ Check to see if the question has been answered,
            if not , send tuling answer
        Parameters
        ----------
        sid : str, session id.

        Returns
        -------
        bool.
        """
        ret = session_info['ret']
        sid = ret['sid']
        intend = ret["event"]["intent"]
        latest_session = session_info['list'][-1]
        question = latest_session['question']
        question_datetime = latest_session['question_datetime']
        if not self.response_check(sid):
            tuling_answer = CasualTalk.get_tuling_answer(question)
            ret["response"]["tts"] = tuling_answer
            # 回答推送至客户，执行推送动作后就记录对话信息
            cms_gate.response_to_client(ret)
            # 写入对话日志
            self.save_session(sid, question, tuling_answer, question_datetime,
                              intend, True)
        else:
            log.info('session {} has been answered'.format(sid))

    def session_info(self, domain_id, robot_id, sid, question, ret):
        """ 拼接对话信息，获取当天最新十条对话信息，再加上最新的问题，同时加上前端所需信息
        Parameters
        ----------
        domain_id : str, domain_id.
        robot_id : str, robot_id.
        sid : str, session id.
        question : str, question text from human being.
        ret: dict, _process_slots return value

        Returns
        -------
        dict.
        """
        session_history = data_gate.session_history(domain_id, robot_id)
        today_session_log = session_history
        new_session = {
            "answer": "",
            "answer_datetime": "",
            "question": question,
            "question_datetime": time_now(),
            "robot_id": robot_id,
            "sid": sid,
        }
        today_session_log.append(new_session)
        exp_timestamp = int((datetime.datetime.now() + datetime.timedelta(
            seconds=10)).timestamp() * 1000)
        r = {
            'domain_id': domain_id,
            'robot_id': robot_id,
            "sid": sid,
            'exp_timestamp': exp_timestamp,
            'ret': ret,
            'list': today_session_log
        }
        return r

    def manual_talk(self, domain_id, robot_id, sid, question, ret, conn_id):
        """ 对话转人工, 传递问题至 cms 人工坐席, 同时启用延时任务
        Parameters
        ----------
        domain_id : str, domain_id.
        robot_id : str, robot_id.
        sid : str, session id.
        question : str, question text from human being.
        ret: dict, _process_slots return value.
        conn_id: str, websocket id

        Returns
        -------
        dict.
        """
        ret['conn_id'] = conn_id
        session_info = self.session_info(domain_id, robot_id, sid, question,
                                         ret)
        # send_message
        cms_gate.send_manual_question(session_info)
        # set delay task to ensure question to be answered
        timethread = threading.Timer(10, self.delay_task, [session_info])
        timethread.start()
        return session_info

    def _process_slots(self, slots, sid, intent=None):
        dm_ret = self._dm.process_slots(sid, slots)
        if not dm_ret:
            intent = 'casual_talk'
        if intent == 'casual_talk':
            ret = {
                "response": {
                    "tts": "图灵闲聊",
                    "web": {
                        "text": ""
                    }
                }
            }
        else:
            ret = cms_gate.response_id_to_answer(self.domain_id,
                                                 dm_ret["response_id"])
            if ret["code"] != 0:
                ret["event"] = {
                    "intent": "",
                    "slots": []
                }
                return ret
            event = {
                "intent": ret["event"]
            }
        event = {
            "intent": "casual_talk"
        }
        return {
            "code": 0,
            "sid": sid,
            "response": ret["response"],
            "event": event,
            "nlu": {
                "ask": dm_ret.get('target', ""),
            }
        }

    def get_context(self):
        """ Return context for NLU module.

        Returns
        -------
        {
            "visible_slots": list,

            "visible_intents": list,

            "agents": list
        }

        """
        return self._dm.get_visible_units()

    def process_slots(self, d_slots, sid):
        """ Process slots input from device

        Parameters
        ----------
        d_slots : dict, slots with diction format.
        sid : str, session id.

        Returns
        -------
        dict.

        """
        slots = [Slot(key, value) for key, value in d_slots.items()]
        return self._process_slots(slots, sid)

    def process_event(self, response_id):
        """ Process event from device.

        System will convert event to `Slots`

        Parameters
        ----------
        response_id : str, event id.

        Returns
        -------
        dict.

        """
        pass

    def process_confirm(self, sid, d_confirm):
        """ Process confirm form device.

        System use sid to identify which request to confirm.

        Parameters
        ----------
        sid : str, correspond to request sid.
        d_confirm : dict,
            {
                'code': 0,  // 0 -- success; others -- failed.

                'message': ''
            }

        Returns
        -------
        dict.
        {
            'code': 0,  // always success

            'message': ''
        }

        """
        return self._dm.process_confirm(sid, d_confirm)

    def update_slots_by_backend(self, d_slots):
        """ Update by business service.

        Parameters
        ----------
        d_slots : dict, dict of slots.

        Returns
        -------
        dict.
        {
            "code": 0   // alway success
        }

        """
        slots = [Slot(key, value) for key, value in d_slots.items()]
        self._dm.update_by_remote(slots)
        log.info(self._dm.context)
        return {
            "code": 0,
        }

    @classmethod
    def get_robot(self, robotid, domain_id, domain_name):
        """ Get a DMRobot instance with device id and it's application id.

        If there is no correspond robot instance in the robots buffer,
        create one. Otherwise, return the buffered one.

        Parameters
        ----------
        robotid : str, device id.
        domain_id : str, application id.
        domain_name : str, name of domain

        Returns
        -------
        DMRobot.

        """
        robot = DMRobot.robots_pool.get(robotid, None)
        if robot:
            return robot
        robot = DMRobot(robotid, domain_id, domain_name)
        DMRobot.robots_pool[robotid] = robot
        return robot

    @classmethod
    def reset_robot(self, robotid, domain_id, domain_name):
        """ Delete old robot from buffer and recreate new one.

        Parameters
        ----------
        robotid : str, device id.
        domain_id : str, application id.

        """
        robot = DMRobot(robotid, domain_id, domain_name)
        DMRobot.robots_pool[robotid] = robot
        return {
            "code": 0
        }
