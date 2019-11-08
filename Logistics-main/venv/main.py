"""
物流平台中控模块主函数

2019-11-07
ZYX
"""

from flask import Flask, jsonify, request, make_response, url_for,redirect, render_template, session
from flask_httpauth import HTTPBasicAuth
from aliyunsdkcore.client import AcsClient
from aliyunsdkcore.request import CommonRequest
import random
import os

app = Flask(__name__, static_url_path = "")
auth = HTTPBasicAuth()

@app.route("/index")
def index():
    return render_template("index.html")

@app.route("/")
def main():
    return render_template("index.html")

@app.route("/search")
def search():

    return "ok"

def getaliyun(phonenumber):
    client = AcsClient('LTAIyNuWycN5rsY5', 'vRqO3bw3o93LmvD9m24W12bK2InFHn', 'cn-hangzhou')
    key = random.randrange(10000, 99999)
    request = CommonRequest()
    request.set_accept_format('json')
    request.set_domain('dysmsapi.aliyuncs.com')
    request.set_method('POST')
    request.set_protocol_type('https') # https | http
    request.set_version('2017-05-25')
    request.set_action_name('SendSms')

    request.add_query_param('RegionId', "cn-hangzhou")
    request.add_query_param('PhoneNumbers', phonenumber)
    request.add_query_param('SignName', "vohyz")
    request.add_query_param('TemplateCode', "SMS_176531663")
    request.add_query_param('TemplateParam', "{\"code\":\"%s\"}"%key)

    response = client.do_action(request)
    # python2:  print(response) 
    print(str(response, encoding = 'utf-8'))
    return key

if __name__ == '__main__':
    app.run(debug = True, host= '0.0.0.0')
