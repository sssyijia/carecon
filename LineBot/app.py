from __future__ import unicode_literals
from flask import Flask, request, abort, render_template, redirect, url_for
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import requests
import json
import configparser
import os
from urllib import parse
import pymysql

app = Flask(__name__, static_url_path='/static')
UPLOAD_FOLDER = 'static'
ALLOWED_EXTENSIONS = set(['pdf', 'png', 'jpg', 'jpeg', 'gif'])
# db = pymysql.connect(host='34.127.117.241', port=3306, user='user1', passwd='00001', db='handdb', charset='utf8')
# cursor = db.cursor()

config = configparser.ConfigParser()
config.read('config.ini')

line_bot_api = LineBotApi(config.get('line-bot', 'channel_access_token'))
handler = WebhookHandler(config.get('line-bot', 'channel_secret'))
my_line_id = config.get('line-bot', 'my_line_id')
end_point = config.get('line-bot', 'end_point')
line_login_id = config.get('line-bot', 'line_login_id')
line_login_secret = config.get('line-bot', 'line_login_secret')
my_phone = config.get('line-bot', 'my_phone')
HEADER = {
    'Content-type': 'application/json',
    'Authorization': F'Bearer {config.get("line-bot", "channel_access_token")}'
}


@app.route("/", methods=['POST', 'GET'])
def index():
    if request.method == 'GET':
        return 'ok'
    body = request.json
    events = body["events"]
    # destination = body["destination"]
    print(body)
    if "replyToken" in events[0]:
        payload = dict()
        replyToken = events[0]["replyToken"]
        payload["replyToken"] = replyToken
        if events[0]["type"] == "message":
            if events[0]["message"]["type"] == "text":
                text = events[0]["message"]["text"]

                if text == "上次測試結果":
                    user_line = events[0]["source"]["userId"]
                #line:168
                    payload["messages"] = [getLatestResult(user_line)]
                elif text == "開始測試":
                    user_line = events[0]["source"]["userId"]
                #line:168
                    payload["messages"] = [getlogin(user_line)]
                else:
                    payload["messages"] = [
                            {
                                "type": "text",
                                "text": text
                            }
                        ]
                replyMessage(payload)
    return 'OK'


@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    try:
        handler.handle(body, signature)

    except InvalidSignatureError:
        abort(400)

    return 'OK'
@handler.add(MessageEvent)
def handle_message(event):
    user_id = event.source.user_id

def getlogin(user_line):
    uid = user_line
    message = {
        "type": "template",
        "altText": "This is a buttons template",
        "template": {
            "type": "buttons",
            "thumbnailImageUrl": "https://careline.enadv.cloud/static/image/1672198295140.jpg",
            "imageAspectRatio": "rectangle",
            "imageSize": "cover",
            "imageBackgroundColor": "#FFFFFF",
            "title": "護聯網",
            "text": "點按開始測試，並『開啟外部瀏覽器』",
            "defaultAction": {
                "type": "uri",
                "label": "View detail",
                "uri": "http://example.com/page/123"
            },
            "actions": [
                {
                    "type": "uri",
                    "label": "開始測試",
                    "uri": "https://careline.enadv.cloud/show_add_user/"+uid
                }
            ]
        }
    }
    return message


def getLatestResult(user_line):

    uid = user_line
    db = pymysql.connect(host='34.127.117.241', port=3306, user='user1', passwd='00001', db='carecondb', charset='utf8')
    cursor = db.cursor()
    sql = "SELECT test_result , pic From UserInfo ui join test t on ui.User_id = t.user_id where Line_id = '" + uid + "' order by test_num desc; "
    try:
        cursor.execute(sql)
        result = cursor.fetchall()
        db.commit()
        print('success')

    except:
        # 發生錯誤時停止執行SQL
        db.rollback()
        print('error')
    db.close()
    if result[0][0] == '0' :
        test_result = '拳握'
    elif result[0][0] == '1' :
        test_result = '旋前抓握'
    elif result[0][0] == '2' :
        test_result = '靜態握筆'
    elif result[0][0] == '3' :
        test_result = '動態握筆'
    elif result[0][0] == '4' :
        test_result = '指側握筆'
    message = {
  "type": "template",
  "altText": "This is a buttons template",
  "template": {
    "type": "buttons",
    "thumbnailImageUrl": result[0][1],
    "imageAspectRatio": "rectangle",
    "imageSize": "cover",
    "imageBackgroundColor": "#FFFFFF",
    "title": test_result ,
    "text": "瞭解更多",
    "defaultAction": {
      "type": "uri",
      "label": "View detail",
      "uri": "http://example.com/page/123"
    },
    "actions": [
      {
        "type": "uri",
        "label": "推薦商品",
        "uri": "https://careline.enadv.cloud/product"
      },
      # {
      #   "type": "postback",
      #   "label": "衛教天地",
      #   "data": "action=add&itemid=123"
      # },
      {
        "type": "uri",
        "label": "衛教天地",
        "uri": "https://careline.enadv.cloud/"
      }
    ]
  }
}
    # message["type"] = "text"
    # message["text"] = result[0][0]+ "\n" + result[0][1]
    return message
    # message["text"] = "".join("$" for r in range(len(name)))
    # emojis_list = list()
    # for i, nChar in enumerate(name):
    #     emojis_list.append(
    #         {
    #           "index": i,
    #           "productId": productId,
    #           "emojiId": f"{lookUpStr.index(nChar) + 1 :03}"
    #         }
    #     )
    # message["emojis"] = emojis_list
    # print(message["emojis"])
    # return message


def getCarouselMessage(data):
    message = {
      "type": "template",
      "altText": "this is a image carousel template",
      "template": {
          "type": "image_carousel",
          "columns": [
              {
                "imageUrl": F"{end_point}/static/taipei_101.jpeg",
                "action": {
                  "type": "postback",
                  "label": "台北101",
                  "data": json.dumps(data)
                }
              },
              {
                "imageUrl": F"{end_point}/static/taipei_1.jpeg",
                "action": {
                  "type": "postback",
                  "label": "台北101",
                  "data": json.dumps(data)
                }
              }
          ]
          }
        }
    return message


def getLocationConfirmMessage(title, latitude, longitude):
    data = {'title': title, 'latitude': latitude, 'longitude': longitude,
            'action': 'get_near'}
    message = {
      "type": "template",
      "altText": "this is a confirm template",
      "template": {
          "type": "confirm",
          "text": f"確認是否搜尋 {title} 附近地點？",
          "actions": [
              {
               "type": "postback",
               "label": "是",
               "data": json.dumps(data),
               },
              {
                "type": "message",
                "label": "否",
                "text": "否"
              }
          ]
      }
    }
    return message


def getCallCarMessage(data):
    message = {
      "type": "template",
      "altText": "this is a template",
      "template": {
          "type": "buttons",
          "text": f"請選擇至 {data['title']} 預約叫車時間",
          "actions": [
              {
               "type": "datetimepicker",
               "label": "預約",
               "data": json.dumps(data),
               "mode": "datetime"
               }
          ]
      }
    }
    return message



def replyMessage(payload):
    response = requests.post("https://api.line.me/v2/bot/message/reply", headers= HEADER, json=payload)
    return 'OK'


# @app.route('/show_add_user/<abc>')
# def show_add_user(abc):
#     return redirect("https://www.google.com" , code=302)
#
#
# @app.route('/line_login', methods=['GET'])
# def line_login():
#     if request.method == 'GET':
#         code = request.args.get("code", None)
#         state = request.args.get("state", None)
#         print(code)
#         print(state)
#         print(request)
#
#         if code and state:
#             HEADERS = {'Content-Type': 'application/x-www-form-urlencoded'}
#             url = "https://api.line.me/oauth2/v2.1/token"
#             FormData = {"grant_type": 'authorization_code', "code": code, "redirect_uri": F"{end_point}/line_login", "client_id": line_login_id, "client_secret":line_login_secret}
#             data = parse.urlencode(FormData)
#             content = requests.post(url=url, headers=HEADERS, data=data).text
#             content = json.loads(content)
#             url = "https://api.line.me/v2/profile"
#             HEADERS = {'Authorization': content["token_type"]+" "+content["access_token"]}
#             content = requests.get(url=url, headers=HEADERS).text
#             content = json.loads(content)
#             name = content["displayName"]
#             userID = content["userId"]
#             pictureURL = content["pictureUrl"]
#             statusMessage = content.get("statusMessage", "")
#
#             print(content)
#             return render_template('profile.html', name=name, pictureURL=pictureURL, userID=userID, statusMessage=statusMessage)
#         else:
#             return render_template('login0.html', client_id=line_login_id,
#                                    end_point=end_point)
#

if __name__ == "__main__":
    app.debug = True
    app.run(port=5002)
