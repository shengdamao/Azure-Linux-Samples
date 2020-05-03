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

class Webhook:
    def __init__(self):
        self.client = pymongo.MongoClient("mongodb://james:wolf0719@cluster0-shard-00-01-oiynz.azure.mongodb.net:27017/?ssl=true&replicaSet=Cluster0-shard-0&authSource=admin&retryWrites=true&w=majority")
    
    def add_log(self,jsondata):
        # 記錄原始得到資料
        webhook_log = self.client.ufs.webhook_log
        # print(jsondata)
        df = pd.DataFrame(jsondata, index=[0])
        
        webhook_log.insert_many(df.to_dict('records'))
        # 整理資料
        # newjson = {
        #     "user_id":jsondata["user_id"],
        #     "replyToken":jsondata['event'][0]["replyToken"],
        #     "date":datetime.date.today(),
        #     "channel_id":jsondata["channel_id"],
        #     "timestamp":jsondata["timestamp"],
        # }
        
        # if jsondata["events"][0]['message']['type'] == "text":
        #     newjson['text'] = jsondata["events"][0]['message']['text']
        
        # webhook = self.client.ufs.webhook
        # df2 = pd.DataFrame(newjson, index=[0])
        
        # webhook.insert_many(df2.to_dict('records'))

        return True
