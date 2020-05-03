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

class Channel:
    def __init__(self):
        self.client = pymongo.MongoClient("mongodb://james:wolf0719@cluster0-shard-00-01-oiynz.azure.mongodb.net:27017/?ssl=true&replicaSet=Cluster0-shard-0&authSource=admin&retryWrites=true&w=majority")
        self.col_channel = self.client.ufs.channel
    # 取得 manager_id 所屬的 channel
    def get_list(self,manager_id):
        mycol = self.client.ufs.channel
        find = {"manager_id":manager_id}
        
        # datas = mycol.find(find).sort("create_datetime",-1)
        datas = mycol.find(find)
        datalist = []
        for d in datas:
            datalist.append({
                "channel_id":d["channel_id"],
                "channel_secret":d["channel_secret"],
                "channel_name":d["channel_name"],
                "channel_access_token":d["channel_access_token"]
            })
        return list(datalist)
    # 新增 Channel 
    def add_once(self,jsondata):
        mycol = self.client.ufs.channel
        df = pd.DataFrame(jsondata, index=[0])
        mycol.insert_many(df.to_dict('records'))
        return True

    # 取得單一 channel 資料
    def get_channel(self, channel_id):
        mycol = self.client.ufs.channel
        find = {"channel_id":channel_id}
        data = mycol.find_one(find)
        return data

    def chk_once(self,channel_id):
        find = {"channel_id":channel_id}
        if(self.col_channel.find(find).count() == 0):
            return False
        else:
            return True

