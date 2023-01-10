import os
import time
import cv2 as cv
import requests
import json
import pymysql
import configparser
from flask import Flask, request, jsonify, render_template, flash, url_for, redirect, send_from_directory, Response, session
from werkzeug.utils import secure_filename
from urllib import parse
from mediapipe_draw import image_draw, video_draw
from datetime import datetime
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage


app = Flask(__name__)
app.secret_key = 'a8f3a05220536fa39d1c600ae84f53be4155c6ae099191b0'
UPLOAD_FOLDER = './static/storage'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'mp4'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024     # maximum filesize 16MB
nowtime = F"{time.localtime(time.time())[0]}-{time.localtime(time.time())[1]}-{time.localtime(time.time())[2]}"
labels = ["拳握法", "旋前抓握", "靜態抓握", "動態抓握", "指側抓握"]

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

def imageurl(path, prediction, leftright):
    # print(path, prediction, leftright)
    sql = "INSERT INTO test(user_id, hand_used, test_result, pic)\
        values(%s,%s,%s,%s);"
    db = pymysql.connect(
        host='34.127.117.241',
        port=3306,
        user='user1',
        database="carecondb",
        password='00001',
        charset='utf8'
        )
    cursor = db.cursor()
    if 'lineid' in session:
        lineid = session['lineid']
        sql2 = "SELECT User_id FROM UserInfo WHERE Line_id = '"+lineid+"';"
        cursor.execute(sql2)
        userid = cursor.fetchall()
        data = [userid, leftright, prediction, path]
        cursor.execute(sql, data)
        db.commit()
    cursor.close()
    db.close()

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/upload_file', methods=['POST'])
def upload_file():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'filename' not in request.files:
            flash('不支援檔案格式')
            return redirect(url_for('/upload'))

        file = request.files['filename']
        # If the user does not select a file, the browser submits an empty file without a filename.
        if file.filename == '':
            flash('未選擇檔案')
            return redirect(url_for('/upload'))

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            extension = filename.split(".")[1]
            if extension == "mp4":
                video_draw(file, filename)
                flash('上傳成功')
                return render_template("uldet.html", filename=filename, extension=extension)
            else:
                image, prediction = image_draw(file)
                cv.imwrite(os.path.join(app.config['UPLOAD_FOLDER'], filename), image)
                # imageurl(("https://carecon.enadv.cloud/static/storage/" + filename), prediction)
                flash('上傳成功')
                return render_template("uldet.html", filename=filename, extension=extension, prediction=labels[prediction])
    return render_template("upload.html")

@app.route("/medijs")
def camera():
    return render_template("medijs.html")

@app.route('/axios', methods=['GET', 'POST'])
def axios():
    if request.method == 'POST':
        file = request.files['file']
        prediction = request.form.get("anwser")
        leftright = request.form.get("leftright")
        filename = secure_filename(file.filename)
        if 'lineid' in session:
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            imageurl(("https://carecon.enadv.cloud/static/storage/" + filename), prediction, leftright)
        return "success"
    
@app.route("/display/<filename>")
def display(filename):
    return redirect(url_for('static', filename='storage/'+filename))

@app.route("/")
def homepage():
    return render_template("index.html")

@app.route("/upload")
def upload():
    return render_template("upload.html")

@app.route("/product")
def product():
    return render_template("product.html")

@app.route('/show_add_user/<lineid>')
def show_add_user(lineid):
    session['lineid'] = lineid
    sql_cmd = "select * from UserInfo where Line_id = '"+ lineid +"';"
    db = pymysql.connect(
        host='34.127.117.241',
        port=3306,
        user='user1',
        database="carecondb",
        password='00001',
        charset='utf8'
        )
    cursor = db.cursor()
    query_data = cursor.execute(sql_cmd)
    db.commit()
    if query_data == 0:
        cursor.close()
        db.close()
        return render_template('show_add_user.html', username=lineid)
    else:
        sql_age = "SELECT Date_birth from UserInfo WHERE Line_id = '"+ lineid +"';"
        cursor.execute(sql_age)
        birthdate = cursor.fetchall()
        birthdate = F"{birthdate[0][0]}"
        age = ((datetime.strptime(nowtime, "%Y-%m-%d")-datetime.strptime(birthdate, "%Y-%m-%d"))//365).days
        print(age)
        cursor.close()
        db.close()
        return render_template("medijs.html", age=age)

@app.route("/do_add_user", methods=['POST'])
def do_add_user():
    name = request.form.get("name")
    gender  = request.form.get("gender")
    handedness = request.form.get("handedness")
    email = request.form.get("email")
    Date_birth = request.form.get("Date_birth")
    message= request.form.get("message")
    phone = request.form.get("phone")
    Line_id = request.form.get("Line_id")
    age = ((datetime.strptime(nowtime, "%Y-%m-%d")-datetime.strptime(Date_birth, "%Y-%m-%d"))//365).days
    session['age'] = age
    sql = "INSERT INTO UserInfo(Line_id, Name, Date_birth, gender, handedness, Email, Phone, Message) values(%s,%s,%s,%s,%s,%s,%s,%s);"
    data = (Line_id,name,Date_birth,gender,handedness,email,phone,message)
    print(data)
    db = pymysql.connect(
     host='34.127.117.241',
     port=3306,
     user='user1',
     database="carecondb",
     password='00001',
     charset='utf8'
      )
    cursor = db.cursor()
    cursor.execute(sql, data)
    db.commit()
    cursor.close()
    db.close()
    return redirect(url_for("line_login"))

@app.route('/line_login', methods=['GET'])
def line_login():
    if request.method == 'GET':
        code = request.args.get("code", None)
        state = request.args.get("state", None)

        if code and state:
            HEADERS = {'Content-Type': 'application/x-www-form-urlencoded'}
            url = "https://api.line.me/oauth2/v2.1/token"
            FormData = {"grant_type": 'authorization_code', "code": code, "redirect_uri": F"{end_point}/line_login", "client_id": line_login_id, "client_secret":line_login_secret}
            data = parse.urlencode(FormData)
            content = requests.post(url=url, headers=HEADERS, data=data).text
            content = json.loads(content)
            print(data)
            url = "https://api.line.me/v2/profile"
            HEADERS = {'Authorization': content["token_type"]+" "+content["access_token"]}
            content = requests.get(url=url, headers=HEADERS).text
            content = json.loads(content)
            # userID = content["userId"]
            # print(content)
            age = session['age']
            return render_template("medijs.html", age=age)
            
        else:
            return render_template('login.html', client_id=line_login_id,
                                   end_point=end_point)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5521)