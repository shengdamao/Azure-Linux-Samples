#coding=utf-8
from flask import Flask, jsonify, request, render_template,session
import pymongo
import pandas as pd
import datetime 
import time
import numpy as np

# Model
from data_model.manager import *
from data_model.channel import *
from data_model.webhook import *
from data_model.user import *
from data_model.tags import *


# line bot 相關元件
from linebot import LineBotApi
from linebot.models import *
from linebot.exceptions import LineBotApiError

class User:
    def __init__(self):
        self.client = pymongo.MongoClient("mongodb://james:wolf0719@cluster0-shard-00-01-oiynz.azure.mongodb.net:27017/?ssl=true&replicaSet=Cluster0-shard-0&authSource=admin&retryWrites=true&w=majority")
        self.col_user = self.client.ufs.users
        self.col_point_logs = self.client.ufs.point_logs
        self.col_user_log = self.client.ufs.user_log

    # 取得單一帳號資料
    def get_once(self,user_id,channel_id):
        find = {
            "user_id": user_id,
            "channel_id": channel_id
        }
        userdata = self.col_user.find_one(find)
        del userdata["_id"]
        return userdata
    #確認帳號存在
    def chk_once(self, user_id, channel_id):
        find = {
            "user_id": user_id,
            "channel_id": channel_id
        }
        cursor = self.col_user.find(find) 
        if(cursor.count() == 0):
            return False
        else:
            return True
    # 新增使用者
    def add_once(self,user_id,channel_id):
        jsondata = {
            "user_id":user_id,
            "channel_id":channel_id,
            "point":0,
            "created_datetime":datetime.datetime.now(),
            "last_datetime":datetime.datetime.now()
        }
        channel = Channel()
        channel_info = channel.get_channel(channel_id)
        channel_access_token = channel_info['channel_access_token']
        line_bot_api = LineBotApi(channel_access_token)
        profile = line_bot_api.get_profile(user_id)
        jsondata['name'] = profile.display_name
        jsondata['avator'] = profile.picture_url
        jsondata['status_message'] = profile.status_message
        
        self.col_user.insert_one(jsondata)

        # 新增LOG
        User().set_user_log(user_id,channel_id,"新增帳號")

        return True

    
    def update_user_main(self,user_id,channel_id,data):
        find = {
            "user_id":user_id,
            "channel_id":channel_id,
            
        }
        data["last_datetime"] =datetime.datetime.now()
        self.col_user.update_one(find,{"$set":data})
        return True
    # 設定使用者參數
    def set_user_tag(self,user_id,channel_id,tag):
        find = {
            "user_id":user_id,
            "channel_id":channel_id
        }
        tag = {
            "tag":tag,
            "date":datetime.datetime.now()
        }
        self.col_user.update_one(find,{"$push":{"tags":tag}})
        # 更新最後操作時間和 log
        data = {}
        data["last_datetime"] =datetime.datetime.now()
        self.col_user.update_one(find,{"$set":data})
        User().set_user_log(user_id,channel_id,"設定 Tag:{}".format(tag))

        # 設定 tag
        tags = Tags()
        # 如果是在追蹤清單中
        if tags.chk_once(channel_id,tag) == True:
            tag_limit = tags.chk_limit(channel_id,user_id,tag)
            # 如果額度還夠
            if tag_limit == True:
                # 執行動作
                tags.do_tag_act(channel_id, user_id,tag)
                tags.set_tag_log(channel_id, user_id,tag)

        return True
    # 取得使用者有使用到的 TAG
    def get_user_tags(self,user_id,channel_id):
        find = {
            "user_id":user_id,
            "channel_id":channel_id
        }
        user_data = self.col_user.find_one(find)
        res = []
        if "tags" in user_data:
            for t in user_data["tags"]:
                if t['tag'] not in res:
                    res.append(t['tag'])
        return res
    
    # 取得所有人
    def get_all_users(self,channel_id):
        find = {
            "channel_id":channel_id
        }
        datalist = []
        for d in self.col_user.find(find):
            del d["_id"]
            datalist.append(d)
        return list(datalist)


    #============================================================================
    #
    # 
    # 點數控制
    #
    # 
    # =================================================================

    # 新增點數
    def add_point(self,user_id,channel_id,point,point_note):
        user_data = User.get_once(self,user_id,channel_id)
        # print(user_data)
        old_point = 0
        if 'point' in user_data:
            old_point = user_data['point']
        new_point = int(old_point) + int(point)
        # 建立 log
        log_data = {
            "user_id":user_id,
            "channel_id":channel_id,
            'original':old_point,
            "point":point,
            "act":"add",
            "update_datetime":datetime.datetime.now(),
            "balance_point":new_point,
            "point_note":point_note
        }
        self.col_point_logs.insert_one(log_data)
        # 回寫主表
        find = {
            "user_id":user_id,
            "channel_id":channel_id
        }
        self.col_user.update_one(find,{"$set":{"point":new_point}})

        # 更新最後操作時間和 log
        data = {}
        data["last_datetime"] =datetime.datetime.now()
        self.col_user.update_one(find,{"$set":data})
        log = "新增點數({0}):{1}".format(point_note,point)
        User().set_user_log(user_id,channel_id,log)
        return new_point


    # 扣除點數
    def deduct_point(self,user_id,channel_id,point,point_note):
        user_data = User.get_once(self,user_id,channel_id)
        old_point = user_data['point']
        new_point = old_point - point
        # 建立 log
        log_data = {
            "user_id":user_id,
            "channel_id":channel_id,
            'original':old_point,
            "point":point,
            "act":"deduct",
            "update_datetime":datetime.datetime.now(),
            "balance_point":new_point,
            "point_note":point_note
        }
        self.col_point_logs.insert_one(log_data)
        # 回寫主表
        find = {
            "user_id":user_id,
            "channel_id":channel_id
        }
        self.col_user.update_one(find,{"$set":{"point":new_point}})

        # 更新最後操作時間和 log
        data = {}
        data["last_datetime"] =datetime.datetime.now()
        log = "扣除點數({0}):{1}".format(point_note,point)
        User().set_user_log(user_id,channel_id,log)
        return new_point

    # 取得交易紀錄
    def get_point_logs(self,user_id,channel_id):
        find = {
            "user_id":user_id,
            "channel_id":channel_id
        }
        logs_data = self.col_point_logs.find(find).sort("update_datetime",-1)
        datalist = []
        for row in logs_data:
            del row["_id"]
            datalist.append(row)
        
        return list(datalist)
    # 取得累績總點數
    def lifetime_record(self,user_id,channel_id):
        find = {
            "user_id":user_id,
            "channel_id":channel_id,
            "act":"add"
        }
        pipeline = [
            {'$match':find},
            {'$group': {'_id': "$user_id", 'point': {'$sum': '$point'}}},
        ]
        if self.col_point_logs.find(find).count() == 0:
            return 0
        else :
            res = self.col_point_logs.aggregate(pipeline)
            for data in res:
                print(data)
            return data['point']

    def set_user_log(self, user_id,channel_id,log_msg):
        log_data = {}
        log_data['log_note'] = log_msg
        log_data['datetime'] = datetime.datetime.now()
        log_data['user_id'] = user_id
        log_data['channel_id'] = channel_id
        self.col_user_log.insert_one(log_data)
        return True
    
    def get_user_log(self,user_id,channel_id):
        find = {
            "user_id": user_id,
            "channel_id": channel_id
        }
        logs_data = self.col_user_log.find(find).sort("datetime",-1)
        datalist = []
        for row in logs_data:
            del row["_id"]
            datalist.append(row)
        
        return list(datalist)





        
