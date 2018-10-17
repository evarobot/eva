# encoding:UTF-8
import logging
import json
import requests
import time
log = logging.getLogger(__name__)


class ConfigChat(object):
    tuling_key = "3125b8b4f2d93f90cbaba3fe29a44709"    # turing123网站
    tuling_apiurl = "http://www.tuling123.com/openapi/api?"
    tuling_userid = "123"


class CasualTalk(object):
    """ 通用对话"""

    @classmethod
    def get_tuling_answer(self, question):
        try:
            t1 = time.time()
            params = {
                'key': ConfigChat.tuling_key,
                'info': question,
                'userid': ConfigChat.tuling_userid
            }
            headers = {'content-type': 'application/json'}
            json_data = requests.post(ConfigChat.tuling_apiurl,
                                      data=json.dumps(params),
                                      headers=headers,
                                      timeout=10).text
            rst = json.loads(json_data)['text'].encode('utf8')
            cost = (time.time() - t1) * 1000
            log.info("[tuling] Question:%s Answer:%s %sms",
                     question, rst, int(cost))
        except Exception:
            log.error('[tuling] 连接错误!')
            rst = '小逗困了，不和你闲聊了。'
        i = rst.find('http')
        if not i == -1:
            rst = rst[0: i]
        return rst


__all__ = ['CasualTalk']
if __name__ == '__main__':
    print(CasualTalk().get_tuling_answer('深圳明天什么天气'))
