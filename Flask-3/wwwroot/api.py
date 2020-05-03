from flask import Flask, jsonify, request, render_template,session,redirect,url_for,flash,Blueprint
import os
import json

# Model
from data_model.manager import *
from data_model.channel import *
from data_model.webhook import *
from data_model.user import *
from data_model.tags import *


api = Blueprint('api', __name__)
user = User()
channel = Channel()

 #============================================================================
    #
    # 
    # 會員
    #
    # 
    # =================================================================
# =================================================================
# 取得會員資料
@api.route("/api/v0/get_user_info/<channel_id>/<user_id>", methods=["POST", "GET"])
def v0_get_user_info(channel_id,user_id):
    # 確認 channel_id
    if(channel.chk_once(channel_id) == False):
        json_data = {'sys_code':"404","sys_msg":"channel not found"}
        return json_data
    # 確認 user_id
    if(user.chk_once(user_id,channel_id) == False):
        json_data = {'sys_code':"404","sys_msg":"user not found"}
        return json_data
    user_info = user.get_once(user_id,channel_id)
    if "tags" in user_info:
        del user_info['tags'] # 不需要歷史紀錄
    json_data = {'sys_code':"200","sys_msg":"success","data":user_info}

    return json_data

# # =================================================================    
@api.route("/api/v0/add_user/<channel_id>/<user_id>", methods=["POST", "GET"])
def v0_add_user(channel_id, user_id):
    # 確認 channel_id
    if(channel.chk_once(channel_id) == False):
        json_data = {'sys_code':"404","sys_msg":"channel not found"}
        return json_data
    # 確認 user_id
    if(user.chk_once(user_id,channel_id) == True):
        json_data = {'sys_code':"500","sys_msg":"會員重覆"}
        return json_data
    
    
    user.add_once(user_id,channel_id)
    # 取得會員資料
    user_info = user.get_once(user_id,channel_id)
    json_data = {'sys_code':"200","sys_msg":"success","data":user_info}

    return json_data
# # 設定會員資料 
@api.route("/api/v0/set_user_info/<channel_id>/<user_id>", methods=["POST", "GET"])
def v0_set_user_info(channel_id, user_id):
    # 確認 channel_id
    if(channel.chk_once(channel_id) == False):
        json_data = {'sys_code':"404","sys_msg":"channel not found"}
        return json_data
    # 確認 user_id
    if(user.chk_once(user_id,channel_id) == False):
        json_data = {'sys_code':"404","sys_msg":"user not found"}
        return json_data
    
    # 取得輸入資料
    jsondata = request.get_json()
    update_data = {}
    if ("name" in jsondata):
        update_data['name'] = jsondata["name"]
    if ("avator" in jsondata):
        update_data['avator'] = jsondata["avator"]
    # 輸入更新
    user.update_user_main(user_id,channel_id,update_data)
    # 取得會員資料
    user_info = user.get_once(user_id,channel_id)
    del user_info['tags'] # 不需要歷史紀錄
    json_data = {'sys_code':"200","sys_msg":"success","data":user_info}

    return json_data

# # 設定會員標籤
@api.route('/api/v0/set_user_tag/<channel_id>/<user_id>/<tag>')
def v0_set_user_tag(channel_id,user_id,tag):
    # user = User()
    # 確認 channel_id
    if(channel.chk_once(channel_id) == False):
        json_data = {'sys_code':"404","sys_msg":"channel not found"}
        return json_data
    # 確認 user_id
    if(user.chk_once(user_id,channel_id) == False):
        json_data = {'sys_code':"404","sys_msg":"user not found"}
        return json_data
    # 設定 tag
    tags = Tags()
    

    # 如果是在追蹤清單中
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


    user.set_user_tag(user_id,channel_id,tag)
    json_data = {'sys_code':"200","sys_msg":"success"}
    return json_data

# # 取回會員標籤清單
@api.route('/api/v0/get_user_tags/<channel_id>/<user_id>/')
def get_user_tags(channel_id, user_id):
    # 確認 channel_id
    if(channel.chk_once(channel_id) == False):
        json_data = {'sys_code':"404","sys_msg":"channel not found"}
        return json_data
    # 確認 user_id
    if(user.chk_once(user_id,channel_id) == False):
        json_data = {'sys_code':"404","sys_msg":"user not found"}
        return json_data
    tags = user.get_user_tags(user_id,channel_id )
    json_data = {'sys_code':"200","sys_msg":"success","tags":tags}

    return json_data

# 取得須要被統計的標籤使用次數
@api.route('/api/v0/get_tag_count/<channel_id>/<user_id>/<track_types>')
def get_tag_count(channel_id, user_id,track_types):
    tags = Tags()
    # 確認 channel_id
    if(channel.chk_once(channel_id) == False):
        json_data = {'sys_code':"404","sys_msg":"channel not found"}
        return json_data
    # 確認 user_id
    if(user.chk_once(user_id,channel_id) == False):
        json_data = {'sys_code':"404","sys_msg":"user not found"}
        return json_data
    
    # 取得要被追縱的 tag
    t_tags = tags.track_types(channel_id,track_types)
    # print(t_tags)
    c = tags.track_types_count(channel_id,user_id,t_tags)
    # print(c)
    json_data = {'sys_code':"200","sys_msg":"Success","count":c}
    return json_data


#============================================================================
    #
    # 
    # 點數
    #
    # 
    # =================================================================
# =================================================================
# # 增加點數
@api.route('/api/v0/add_user_point/<channel_id>/<user_id>', methods=["POST", "GET"])
def add_user_point(channel_id, user_id):
    jsondata = request.get_json()
    point = jsondata["point"]
    point_note = jsondata["point_note"]

    new_point = user.add_point(user_id,channel_id,point,point_note)
    json_data = {'sys_code':"200","sys_msg":"success",'new_point':new_point}

    return json_data


# 扣儲點數
@api.route('/api/v0/deduct_user_point/<channel_id>/<user_id>', methods=["POST", "GET"])
def deduct_user_point(channel_id, user_id):
    if(channel.chk_once(channel_id) == False):
        json_data = {'sys_code':"404","sys_msg":"channel not found"}
        return json_data
    # 確認 user_id
    if(user.chk_once(user_id,channel_id) == False):
        json_data = {'sys_code':"404","sys_msg":"user not found"}
        return json_data
    jsondata = request.get_json()
    point = jsondata["point"]
    point_note = jsondata["point_note"]

    new_point = user.deduct_point(user_id,channel_id,point,point_note)
    json_data = {'sys_code':"200","sys_msg":"success",'new_point':new_point}

    return json_data

# # 點數查詢
@api.route('/api/v0/get_user_points/<channel_id>/<user_id>', methods=['GET'])
def get_user_points(channel_id, user_id):
    if(channel.chk_once(channel_id) == False):
        json_data = {'sys_code':"404","sys_msg":"channel not found"}
        return json_data
    # 確認 user_id
    if(user.chk_once(user_id,channel_id) == False):
        json_data = {'sys_code':"404","sys_msg":"user not found"}
        return json_data
    user_data = user.get_once(user_id,channel_id)
    
    if "point" in user_data:
        point = user_data["point"]
        lifetime_record=user.lifetime_record(user_id,channel_id)
    else:
        point = 0
        lifetime_record=0

    json_data = {
        "sys_code": "200",
        "sys_msg": "Success",
        "canuse_point": point,
        "used_point": lifetime_record-point,
        "lifetime_record":lifetime_record
    }
    return json_data
# 查詢點數記錄
@api.route('/api/v0/get_user_points_log/<channel_id>/<user_id>', methods=['GET'])
def get_user_points_log(channel_id, user_id):
    if(channel.chk_once(channel_id) == False):
        json_data = {'sys_code':"404","sys_msg":"channel not found"}
        return json_data
    # 確認 user_id
    if(user.chk_once(user_id,channel_id) == False):
        json_data = {'sys_code':"404","sys_msg":"user not found"}
        return json_data
    user_data = user.get_once(user_id,channel_id)
    if "point" in user_data:
        point = user_data["point"]
        lifetime_record=user.lifetime_record(user_id,channel_id)
        point_logs = user.get_point_logs(user_id,channel_id)
    else:
        point = 0
        lifetime_record=0
        point_logs = []

    json_data = {
        "sys_code": "200",
        "sys_msg": "Success",
        "canuse_point": point,
        "used_point": lifetime_record-point,
        "lifetime_record":lifetime_record,
        "point_logs":point_logs
    }
    return json_data


#============================================================================
    #
    # 
    # 標籤
    #
    # 
    # =================================================================
# =================================================================

@api.route('/api/v0/set_tag_main', methods=['POST'])
def set_tag_main():
    jsondata = request.get_json()
    tags = Tags()
    if tags.chk_once(jsondata['channel_id'],jsondata['tag']) == True:
        return  {'sys_code':"500","sys_msg":"重複設定"}
    else:
        tags.set_tag_main(jsondata)
        return "jsondata"


@api.route('/api/v0/send_message/<channel_id>/<user_id>/<msg>', methods=['POST',"GET"])
def send_message(channel_id, user_id, msg):
    channel = Channel()
    
    channel_info = channel.get_channel(channel_id)
    channel_access_token = channel_info['channel_access_token']
    line_bot_api = LineBotApi(channel_access_token)
    
    res = line_bot_api.push_message(user_id, TextSendMessage(text=msg))
    return "12345"



    
    