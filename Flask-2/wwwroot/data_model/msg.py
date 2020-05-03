#coding=utf-8
from flask import Flask, jsonify, request, render_template,session
import pymongo
import pandas as pd
from datetime import datetime
import time
import numpy as np

# Model
from data_model.manager import *
from data_model.channel import *
from data_model.webhook import *
from data_model.user import *
from data_model.tags import *


class Msg:
    def __init__(self):
        self.client = pymongo.MongoClient("mongodb://james:wolf0719@cluster0-shard-00-01-oiynz.azure.mongodb.net:27017/?ssl=true&replicaSet=Cluster0-shard-0&authSource=admin&retryWrites=true&w=majority")
        self.col_msg = self.client.ufs.msgs

    
    def add_once(self,datajson):
        datajson['manager_id']  = session.get("manager_id")
        datajson['msg_id']  = str(round(time.time()))
        datajson["created_datetime"] = datetime.today()
        self.col_msg.insert_one(datajson)
        return True

    def get_list(self,msg_type=None):
        find = {}
        if msg_type is not None:
            find = {
                "msg_type":msg_type
            }
        find["channel_id"] = session.get("channel_id")
        msgs = self.col_msg.find(find).sort("created_datetime",-1)
        
        datalist = []
        for d in msgs:
            datalist.append(d)
        return list(datalist)

    def get_once(self,msg_id):
        find = {"msg_id": msg_id}
        msg = self.col_msg.find_one(find)
        del msg["_id"]
        return msg
    
    # 尋找關鍵字訊昔
    def chk_listen_keyword(self,channel_id,listen_keyword):
        find = {
            "channel_id":channel_id,
            "type":"listen_keyword",
            "listen_keyword":listen_keyword
        }
        if self.col_msg.find(find).count() == 0:
            return False
        else :
            res = self.col_msg.find_one(find)
            del res["_id"]
            return res

    # 設定發送內容
    def set_msg_format(self,msg_id,channel_id,user_id):
        msg_data = Msg().get_once(msg_id)
        # 純文字訊息
        if msg_data["msg_type"] == "text":
            send_message = TextSendMessage(text=msg_data["text"])
        # 圖片
        elif msg_data["msg_type"] == "image":
            send_message = ImageSendMessage(
                original_content_url=msg_data['original_content_url'],
                preview_image_url=msg_data['original_content_url']
            )
        # 圖片帶連結
        elif msg_data['msg_type'] == "imagemap":
            
            action = []
            for action_item in msg_data['actions']:
                if action_item['act_type'] == "text":
                    action.append(MessageImagemapAction(
                                    text=action_item['text'],
                                    area=ImagemapArea(
                                        x=action_item['x'], y=action_item['y'], width=action_item['width'], height=action_item['height']
                                    )
                                ))
                if action_item['act_type'] == "link":
                    action.append(URIImagemapAction(
                                    link_uri=action_item['link_uri']+"?user_id="+user_id+"&channel_id="+channel_id,
                                    area=ImagemapArea(
                                        x=action_item['x'], y=action_item['y'], width=action_item['width'], height=action_item['height']
                                    )
                                ))
            
            send_message = ImagemapSendMessage(
                base_url=msg_data['base_url'],
                alt_text=msg_data['alt_text'],
                base_size=BaseSize(height=1040, width=1040),
                actions=action
            )
        return send_message


    # 單筆發送
    def send_message(self,channel_id,msg_id,user_id):
        channel = Channel()
        channel_info = channel.get_channel(channel_id)
        channel_access_token = channel_info['channel_access_token']
        
        send_message = Msg().set_msg_format(msg_id,channel_id,user_id)
        
        line_bot_api = LineBotApi(channel_access_token)
        line_bot_api.push_message(user_id, send_message)
        return True
           
    def reply_message(self,channel_id,msg_id,replyToken,user_id):

        channel = Channel()
        channel_info = channel.get_channel(channel_id)
        channel_access_token = channel_info['channel_access_token']
        send_message = Msg().set_msg_format(msg_id,channel_id,user_id)
        line_bot_api = LineBotApi(channel_access_token)
        line_bot_api.reply_message(replyToken, send_message)
        return True



