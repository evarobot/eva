# VikiDM


。
  * 如果输入就是概念和值：则直接走对话DM引擎。
* DM引擎
  * 输入： 概念和值
  * 输出： 上下文信息和事件ID。


#### 终端到DM请求
``` 
/dm/robot/event
    ｛
          "robotid": ppepper的ID,
          "project": 项目名, 
          "sid": "xxxx", // session id
          "event_id": "xxxxxx",
      }
/dm/robot/question
     ｛
          "robotid": ppepper的ID,
          "project": 项目名, 
           "sid": "xxxx", // session id
          "question": "请问你叫什么名字",
       }
/dm/backend/concepts
     ｛
          "robotid": ppepper的ID,
          "project": 项目名, 
          "question": "请问你叫什么名字",
       }
/dm/robot/concepts
      ｛
          "robotid": ppepper的ID,
          "project": 项目名, 
           "sid": "xxxx", // session id
          "concepts": {
              "XXX": "YYY"
         }
       }
```

#### DM到终端请求返回
接口：
* /dm/robot/event
* /dm/robot/question
* /dm/robot/concepts
```
    {
      "code": 0,  // 非0都是错误
        "message": "",
        "event_id": "weather.query: date=今天&city=明天",    // 事件ID
        "sid": "xxxx", // session id
        "nlu": {
            "intent": "",
            "slots": {
              "槽1": "值1",
              "槽2": "值2"
            }
        }
        "debug": {
            "context": "上下文变量",
            "stack": "上下文栈情况"
        }
        "action": { 
           "tts": "xxxxxxxxxx"， // 机器人要说的话
           "web": {
              "text": "xxxxx
           }
        }
       
    }
```
接口：
* /dm/backend/concepts
```
    {
      "code": 0,  // 非0都是错误
        "message": "",
        "context": "xxxx"
    }
```

#### 终端到DM确认

```
    ｛
          "robotid": ppepper的ID,
          "project": 项目名, 
          "sid": "xxxx", // session id
          "result": {
              "code": 0, // 非0表示失败
              "message": "" // 错误消息
          }
      }
```


#### DM到终端确认返回
```
    {
      "code": 0,  // 非0都是错误
      "message": "",    
    }
```
