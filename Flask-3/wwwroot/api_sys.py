from flask import Flask, jsonify, request, render_template,session,redirect,url_for,flash,Blueprint
import os
import re
import json
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


api_sys = Blueprint('api_sys', __name__)

# 設定腳本
# 2020-03-09 改成 script 和 msg 共用設定和資廖庫
@api_sys.route('/api_sys/set_msg/', methods=["POST"])
def set_msg():
    # 取得輸入資料
    jsondata = request.get_json()
    # print(jsondata)
    # msg = Msg()
    # msg.add_once(jsondata)
    json_data = {'sys_code':"200","sys_msg":"success"}
    return json_data
        


@api_sys.route('/api_sys/set_channel/<channel_id>')
def set_channel(channel_id):
    session["channel_id"] = channel_id
    json_data = {'sys_code':"200","sys_msg":"success",'channel_id':channel_id}

    return json_data

# 發送
@api_sys.route('/api_sys/send_message/<channel_id>/<msg_id>')
def send_message(channel_id,msg_id):
    msg = Msg()
    channel = Channel()
    user = User()
    user_id = "Ufd5d3bb5d828bfcef65344c0bd5b5c07"
    msg_data = msg.get_once(msg_id)
   

    # # # 整理會員名單
    users = []
    user_ids = []
    users = user.get_all_users(channel_id)
    # # line_bot_api = LineBotApi(channel_access_token)
    # # # U7e053ed8fcca7e8bf4b82ac79accf8cc
    # # # res = line_bot_api.push_message('U7e053ed8fcca7e8bf4b82ac79accf8cc', send_message)
    # # # 發送訊息
    for user_data in users:
        
        # 設定log
        user.set_user_log(user_data['user_id'],channel_id,"發送訊息"+msg_data['subject'])
        msg.send_message(channel_id,msg_id,user_data['user_id'])

    json_data = {'sys_code':"200","sys_msg":"success"}

    return json_data

