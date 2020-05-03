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

class Re_url:
    def __init__(self):
        self.client = pymongo.MongoClient("mongodb://james:wolf0719@cluster0-shard-00-01-oiynz.azure.mongodb.net:27017/?ssl=true&replicaSet=Cluster0-shard-0&authSource=admin&retryWrites=true&w=majority")
        self.col_reurl = self.client.ufs.reurl

    def add_once(self,deta):
        self.col_reurl.insert_one(deta)
        return True

    def get_list(self,channel_id):
        find = {
            "channel_id":channel_id
        }
        datas = self.col_reurl.find(find)
        datalist = []
        for d in datas:
            del d["_id"]
            datalist.append(d)
        return list(datalist)


    def get_once(self,link_id):
        find = {
            "link_id": link_id
        }
        data = self.col_reurl.find_one(find)
        del data["_id"]
        return data