#系統元件
from flask import Flask, jsonify, request, render_template,session,redirect,url_for,flash,Blueprint
import os
import json
import pymongo
import pandas as pd
import datetime
import hashlib
from datetime import timedelta
import time
import numpy as np
# line bot 相關元件
from linebot import LineBotApi
from linebot.models import *
from linebot.exceptions import LineBotApiError
# Model
from data_model.manager import *
from data_model.channel import *
from data_model.webhook import *
from data_model.user import *
from data_model.msg import *
from data_model.re_url import *

from api import *
from api_sys import *

from __init__ import app


#app = Flask(__name__)

app.config['SECRET_KEY'] = os.urandom(24)
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=31)
app.register_blueprint(api)
app.register_blueprint(api_sys)
manager = Manager()

# 登入管理者
@app.route("/login",methods=['GET', 'POST'])
def login():
    if request.method == "POST":
        manager_id = request.values["manager_id"]
        manager_pwd = request.values["manager_pwd"]
        # 先確認目前登入狀態
        if(manager.chk_now() == True):
            return redirect(url_for("channel"))
        else:
            # 如果未登入就去驗證
            if(manager.chk_id_pw(manager_id,manager_pwd) == True):
                # 登入 manager_id
                manager.login(manager_id)
                return redirect(url_for("channel"))
            else:
                flash(manager_id +" 帳號登入失敗，請檢查登入訊息後再重新登入")
                return render_template('login.html')
    else:
        return render_template('login.html')
# 登出
@app.route('/logout', methods=['GET'])
def logout():
    manager.logout()
    return redirect(url_for("login"))


# 首頁＆channel 列表
@app.route("/", methods=["GET", "POST"])
@app.route("/channel", methods=["GET", "POST"])
def channel():
    if(manager.chk_now() == True):
        channel = Channel()
        manager_id = session.get("manager_id")

        if(request.method == "POST"):
            jsondata = {
                "manager_id": manager_id,
                "channel_id":request.values["channel_id"],
                "channel_name":request.values["channel_name"],
                "channel_secret":request.values["channel_secret"],
                "channel_access_token":request.values["channel_access_token"]
            }
            channel.add_once(jsondata)
        datalist = channel.get_list(manager_id)
        return render_template("channel.html",datalist=datalist)
    else:
        return redirect(url_for("login"))

@app.route("/channel_info", methods=["GET", "POST"])
def channel_info():
    if(manager.chk_now() == True):
        manager_id = session.get("manager_id")
        if session.get("channel_id") is None:
            flash("請先選取要設定的 Channel ","danger")
            return redirect(url_for("channel"))
        else:
            channel_id = session.get("channel_id")
            return render_template("channel_info.html")
    else:
        return redirect(url_for("login"))


@app.route("/msg", methods=["GET", "POST"])
def msg():
    if(manager.chk_now() == True):
        msg = Msg()
        if session.get("channel_id") is None:
            flash("請先選取要設定的 Channel ","danger")
            return redirect(url_for("channel"))
        else:
            if(request.method == "POST"):
                msg.add_once(request.form.to_dict())
                flash("訊息設定完成，請點選操作工具發送","success")
            datalist = msg.get_list()
            
            return render_template("msg.html",datalist=datalist)
    else:
        return redirect(url_for("login"))




@app.route("/users", methods=["GET", "POST"])
def users():
    if(manager.chk_now() == True):
        manager_id = session.get("manager_id")
        if session.get("channel_id") is None:
            flash("請先選取要設定的 Channel ","danger")
            return redirect(url_for("channel"))
        else:
            channel_id = session.get("channel_id")
            datalist = user.get_all_users(channel_id)
            return render_template("users.html",datalist=datalist)
    else:
        return redirect(url_for("login"))

@app.route("/user_info/<channel_id>/<user_id>", methods=["POST", "GET"])
def user_info(channel_id, user_id):
    
    if(manager.chk_now() == True):
        manager_id = session.get("manager_id")
        user = User()
        user_info = user.get_once(user_id,channel_id)
        user_logs = user.get_user_log(user_id,channel_id)
        return render_template("user_info.html",user_info=user_info,user_logs=user_logs)
    else:
        return redirect(url_for("login"))


@app.route("/re_url/", methods=["GET", "POST"])
def re_url():
    if(manager.chk_now() == True):
        manager_id = session.get("manager_id")
        if session.get("channel_id") is None:
            flash("請先選取要設定的 Channel ","danger")
            return redirect(url_for("channel"))
        else:
            channel_id = session.get("channel_id")
            re_url = Re_url()
            if request.method == "POST":
                subject = request.values['subject']
                target_url = request.values['target_url']
                tags = request.values['tags']
                
                # 先將資料編碼，再更新 MD5 雜湊值
                m = hashlib.md5()
                m.update(str(time.time()).encode("utf-8"))
                link_id = m.hexdigest()[-6:]
                datajson = {
                    "subject":subject,
                    "target_url":target_url,
                    "tags":tags,
                    "channel_id":channel_id,
                    "url":link_id,
                    "link_id":link_id
                }
                
                re_url.add_once(datajson)
                
            urls = re_url.get_list(channel_id)
        return render_template("re_url.html",datalist=urls)
    else:
        return redirect(url_for("login"))

# 轉址動作
@app.route("/re_url/<link_id>", methods=["GET", "POST"])
def re_url_go(link_id):
    re_url = Re_url()
    tags = Tags()
    data = re_url.get_once(link_id)
    if 'user_id' in request.values and 'channel_id' in request.values :
        channel_id = request.values['channel_id']
        user_id = request.values['user_id']
        print(data)
        if 'tags' in data:
            # 如果是在追蹤清單中
            tag = data['tags']
            if tags.chk_once(channel_id,tag) == True:
                tag_limit = tags.chk_limit(channel_id,user_id,tag)
                # 如果額度還夠
                if tag_limit == True:
                    # 動作
                    tag_data = tags.get_once(channel_id,tag);
                    # tags.do_tag_act(channel_id,user_id,tag)
                    if "act" in tag_data:
                        for a in tag_data["act"]:
                            if a["act_key"] == "add_user_point":
                                user.add_point(user_id,channel_id,a["act_value"],tag_data["tag_desc"])

                    tags.set_tag_log(channel_id, user_id,tag)
        return redirect(data['target_url'])

    return data['target_url']



@app.route("/tags/", methods=["GET", "POST"])
def tags():
    if(manager.chk_now() == True):
        manager_id = session.get("manager_id")
        if session.get("channel_id") is None:
            flash("請先選取要設定的 Channel ","danger")
            return redirect(url_for("channel"))
        else:
            channel_id = session.get("channel_id")
            
                
            
        return render_template("tags.html")
    else:
        return redirect(url_for("login"))



# 商品管理
@app.route("/products", methods=["GET", "POST"])
def products():
    if(manager.chk_now() == True):
        manager_id = session.get("manager_id")
        if session.get("channel_id") is None:
            flash("請先選取要設定的 Channel ","danger")
            return redirect(url_for("channel"))
        else:
            channel_id = session.get("channel_id")
            return render_template("products.html")
    else:
        return redirect(url_for("login"))



# 訂單管理
@app.route("/orders", methods=["GET", "POST"])
def orders():
    if(manager.chk_now() == True):
        manager_id = session.get("manager_id")
        if session.get("channel_id") is None:
            flash("請先選取要設定的 Channel ","danger")
            return redirect(url_for("channel"))
        else:
            channel_id = session.get("channel_id")
            return render_template("orders.html")
    else:
        return redirect(url_for("login"))

@app.route("/order_info", methods=["GET", "POST"])
def order_info():
    if(manager.chk_now() == True):
        manager_id = session.get("manager_id")
        if session.get("channel_id") is None:
            flash("請先選取要設定的 Channel ","danger")
            return redirect(url_for("channel"))
        else:
            channel_id = session.get("channel_id")
            return render_template("order_info.html")
    else:
        return redirect(url_for("login"))



# 腳本訓息
@app.route("/scripts", methods=["GET", "POST"])
def scripts():
    if(manager.chk_now() == True):
        manager_id = session.get("manager_id")
        if session.get("channel_id") is None:
            flash("請先選取要設定的 Channel ","danger")
            return redirect(url_for("channel"))
        else:
            channel_id = session.get("channel_id")
            return render_template("scripts.html")
    else:
        return redirect(url_for("login"))





# 單純抓取 webhook 回傳資料
@app.route("/webhook/<channel_id>", methods=["POST", "GET"])
def webhook(channel_id):
    channel = Channel()
    webhook = Webhook()
    user = User()
    jsondata = request.get_json()
    try:
        
        jsondata["channel_id"] = channel_id
        channel_data = channel.get_channel(channel_id)
        channel_access_token = channel_data["channel_access_token"]
        event = jsondata["events"][0]
        user_id = event["source"]["userId"]
        jsondata["user_id"] = user_id
        webhook.add_log(jsondata)

        # 使用者紀錄
        if(user.chk_once(user_id,channel_id) == True):
            user.set_user_tag(user_id,channel_id,event['type'])
        else :
            user.add_once(user_id,channel_id)
            user.set_user_tag(user_id,channel_id,event['type'])

        # 如果有回覆碼可以用
        if "replyToken" in event:
            replyToken = event["replyToken"]
            # 回覆
            line_bot_api = LineBotApi(channel_access_token)
        
            # 檢查腳本關鍵字觸發
            msg = Msg()
            if "message" in event:
                msg_data = msg.chk_listen_keyword(channel_id,event['message']['text'])
                if msg_data != False:
                    msg.reply_message(channel_id,msg_data['msg_id'],replyToken,user_id)
        
        

    except (EOFError, KeyboardInterrupt):

        print(EOFError)
        
    # mycol = client.ufs.webhook
    # df = pd.DataFrame(jsondata, index=[0])
    # mycol.insert_many(df.to_dict('records'))
    return "replyToken"


if __name__ == '__main__':
    app.debug = True
    app.run()
