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

class Tags:
    def __init__(self):
        self.client = pymongo.MongoClient("mongodb://james:wolf0719@cluster0-shard-00-01-oiynz.azure.mongodb.net:27017/?ssl=true&replicaSet=Cluster0-shard-0&authSource=admin&retryWrites=true&w=majority")
        self.col_tag_main = self.client.ufs.tag_main
        self.col_tag_log = self.client.ufs.tag_log
        

    # 新增標籤主表資料
    # ===============================
    # tag_data = {
    #    channel_id:
    #    tag:
    #    tag_desc:
    #    limit_cycle:
    #    limit_qty:
    #    act:{
    #            act_key:
    #            act_value:
    #       }    
    # }
    def set_tag_main(self,tag_data):
        self.col_tag_main.insert_one(tag_data)
        return True
    # 取得所有追縱標籤資料
    def get_tag_list(self,channel_id):
        find = {
            "channel_id": channel_id
        }
        datalist = []
        for row in self.col_tag_main.find(find):
            del row["_id"]
            datalist.append(row)
        return list(datalist)
    # 確認 tag 要被追縱處理
    def chk_once(self,channel_id,tag):
        find = {
            "channel_id":channel_id,
            "tag":tag
        }
        if(self.col_tag_main.find(find).count() == 0):
            return False
        else:
            return True
    def get_once(self,channel_id,tag):
        find = {
            "channel_id":channel_id,
            "tag":tag
        }
        # print(find)
        tag_info = self.col_tag_main.find_one(find)
        # print(tag_info)
        del tag_info["_id"]
        return tag_info

    # 確認條件 True 通過 Flase 失敗
    # day,month,year,total
    def chk_limit(self,channel_id,user_id,tag):
        tag_data = Tags().get_once(channel_id,tag);
        now = datetime.datetime.now();
        find = {
                "channel_id":channel_id,
                "user_id":user_id,
                "tag":tag
            }

        if tag_data["limit_cycle"] == "none":
            return True
        elif tag_data['limit_cycle'] == 'day':
            day = "{0}-{1}-{2}".format(now.year, now.month, now.day)
            find['datetime'] = day
        elif tag_data['limit_cycle'] == 'month':
            day = "{0}-{1}".format(now.year, now.month)
            find['datetime'] = {"$regex": day}
        elif tag_data['limit_cycle'] == 'year':
            day = "{0}-".format(now.year)
            find['datetime'] = {"$regex": day}
       
        if(self.col_tag_log.find(find).count() >= tag_data['limit_qty']):
            return False
        else:
            return True

    # 記錄追蹤
    def set_tag_log(self,channel_id, user_id,tag):
        now = datetime.datetime.now();
        data = {
            "channel_id":channel_id,
            "user_id":user_id,
            'tag':tag,
            "datetime":"{0}-{1}-{2}".format(now.year, now.month, now.day)
        }
        self.col_tag_log.insert_one(data)
        return True

    # 執行動作
    def do_tag_act(self,channel_id,user_id,tag):
        # user = User()
        tag_data = Tags().get_once(channel_id,tag)
        
        if "act" in tag_data:
            for a in tag_data["act"]:
                if a["act_key"] == "add_user_point":
                    user.add_point(user_id,channel_id,a["act_value"],tag_data["tag_desc"])
        
        return True

    # 取得要被追縱的 tag
    def track_types(self,channel_id,track_types):
        find = {
            "channel_id": channel_id,
            "type":track_types
        }
        datalist = []
        for row in self.col_tag_main.find(find):
            datalist.append(row['tag'])
        return list(datalist)
    
    def track_types_count(self,channel_id,user_id,t_tags):
        find = {
            "channel_id": channel_id,
            "user_id":user_id,
            "tag":{"$in":t_tags}
        }
        return self.col_tag_log.find(find).count()

