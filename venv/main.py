"""
物流平台中控模块主函数

2019-11-07
ZYX
"""

from flask import Flask, jsonify, request, make_response, url_for,redirect, render_template, session, Session
from flask_httpauth import HTTPBasicAuth
import datetime
import pika
import os
import json, urllib
from urllib import parse
from urllib.request import urlopen

app = Flask(__name__, static_url_path = "")
app.config['SECRET_KEY'] = '123456'
auth = HTTPBasicAuth()

@app.route("/index")
def index():
    return render_template("index.html")

@app.route("/")
def main():
    return render_template("index.html")

@app.route("/order/<order_id>")
def showOrder(order_id):
    try:
        url = "http://127.0.0.1:5001/searchbyOrder"
        params = {
            'order_id': order_id
        }
        params = parse.urlencode(params) 

        f = urlopen("%s?%s" % (url, params))

        content = f.read()
        res = json.loads(content)
    except:
        Data = {
            'error_message': 'error1'
        }
        return render_template("order.html", Data = Data)
    message = res['order_message']
    if message != '0':
        order = message['orders'][0]
        times = order['order_transport_time'].split()
        order_time = []
        i = 0
        while i < len(times):
            order_time.append(times[i] +' '+ times[i+1])
            i += 2
        order_place = order['order_transport_place'].split()
        # order_details = order[11]
        print(len(order_time))
        print(order_time)
        n = len(order_time)
        Data = {
            'order_id':order['order_id'],
            'begin_time_1':order['begin_time_1'],
            'begin_time_2':order['begin_time_2'],
            'begin_name':order['begin_name'],
            'begin_phone':order['begin_phone'],
            'end_name':order['end_name'],
            'end_phone':order['end_phone'],
            'begin_city':order['begin_city'],
            'end_city':order['end_city'],
            'order_state':order['order_state'],
            'error_message': '0',
            'order_time': order_time,
            'order_place': order_place[:n],
            'n': n
        }
    else:
        Data = {
            'error_message': 'error2'
        }
    return render_template("order.html", Data = Data)

@app.route("/search")
def search():                                           # 订单查询页
    return render_template("search.html")

@app.route("/search/id", methods=['GET', 'POST'])
def searchid():                                         # 订单查询页搜索
    form_data = request.form
    order_id = form_data.get("ordertext")

    Data = {}
    try:
        url = "http://127.0.0.1:5001/searchbyOrder"
        params = {
            'order_id': order_id
        }
        params = parse.urlencode(params)

        f = urlopen("%s?%s" % (url, params))

        content = f.read()
        res = json.loads(content)
    except:
        Data = {
            'error_message': 'error1'
        }
        return render_template("search.html", Data = Data)
    orders = res['order_message']['orders']
    # print(orders)
    if orders != '0':
        Data = {
            'error_message': '0',
            'orders':[
                {
                'order_id':order['order_id'],
                'begin_time_1':order['begin_time_1'],
                'begin_time_2':order['begin_time_2'],
                'begin_name':order['begin_name'],
                'begin_phone':order['begin_phone'],
                'end_name':order['end_name'],
                'end_phone':order['end_phone'],
                'begin_city':order['begin_city'],
                'end_city':order['end_city'],
                'order_state':order['order_state']
                }
            for order in orders]
            }
        # print(Data)
    else:
        Data = {
            'error_message': 'error2'
        }
    return render_template("search.html", Data = Data)

@app.route("/city")
def city():                                             # 城市查询页
    return render_template("city.html")

@app.route("/create")
def create():                                           # 创建订单页路由
    return render_template("create.html")
@app.route("/create/failed")
def failed():                                           # 创建订单后失败页
    return render_template("createfailed.html")
@app.route("/create/success")
def success():                                          # 创建订单后成功页
    # 添加一个显示创建成功的订单的详细信息的页面
    return render_template("createsuccess.html")

@app.route("/create/order", methods=['GET', 'POST'])
def order():                                            # 创建订单提交
    begin_name = request.form.get('order_begin_name')
    begin_phone = request.form.get('order_begin_phone')
    begin_city = request.form.get('order_begin_city')
    end_name = request.form.get('order_end_name')
    end_phone = request.form.get('order_end_phone')
    end_city = request.form.get('order_end_city')
    '''
    此处可能需要支付
    ''' 

    # 此处调用订单模块的api

    try:
        url = "http://127.0.0.1:5001/create"
        params = {
            'order_begin_name': begin_name,
            'order_begin_phone': begin_phone,
            'order_begin_city': begin_city,
            'order_end_name': end_name,
            'order_end_phone': end_phone,
            'order_end_city': end_city
        }
        params = parse.urlencode(params)
        
        f = urlopen("%s?%s" % (url, params))
        
        content = f.read()
        res = json.loads(content)
        print(res)  
        if res['rst'] == 'ok':
            return redirect("/create/success")
        else:
            return redirect("/create/failed")
    except Exception as e:
        print(e)
        return redirect("/create/failed")

@app.route('/login')
def login():                                            # 登录界面路由
    return render_template('login.html')

@app.route('/login/in', methods=['GET', 'POST'])    
def login_in():                                         # 用户输入信息登录
    json_data = request.json                            # 获取数据
    userphone = json_data.get("mobile")
    sms_code = json_data.get("sms_code")

    try:
        url = "http://127.0.0.1:5004/login"
        params = {
            'userphone': userphone,
            "sms_code": sms_code
        }
        params = parse.urlencode(params)
        
        f = urlopen("%s?%s" % (url, params))
        
        content = f.read()
        res = json.loads(content)
        print(res)  
        if res['errno'] == 'ok':
            session['userphone'] = userphone
            session.permanent = True
            app.permanent_session_lifetime = datetime.timedelta(minutes=10)
            return jsonify(errno='ok', errmsg="登录成功")
        else:
            return jsonify(errno='notok', errmsg=res['errmsg'])
    except Exception as e:
        #print(e)
        return jsonify(errno='notok', errmsg="用户数据读取失败")

@app.route('/sms_code', methods=['GET', 'POST'])
def sms_code():                                         # 发送验证码
    json_data = request.json
    mobile = json_data.get("mobile")
    try:
        url = "http://127.0.0.1:5004/sms"
        params = {
            'userphone': mobile
        }
        params = parse.urlencode(params)
        
        f = urlopen("%s?%s" % (url, params))
        
        content = f.read()
        res = json.loads(content)
        print(res)  
        if res['errno'] == 'ok':
            return jsonify(errno=res['errno'], errmsg=res['errmsg'])
        else:
            return jsonify(errno=res['errno'], errmsg=res['errmsg'])
    except:
        return jsonify(errno='error', errmsg="发送失败")
    return jsonify(errno='ok', errmsg="发送成功")

@app.route('/usercenter')
def usercenter():                                       # 用户个人中心
    if 'userphone' in session:
        userphone = session['userphone']
    else:
        return redirect('/')
    # 此处整合到登录注册模块
    # //
    Data = {}
    try:
        url = "http://127.0.0.1:5001/searchbyUser"
        params = {
            'userphone': userphone
        }
        params = parse.urlencode(params)

        f = urlopen("%s?%s" % (url, params))

        content = f.read()
        res = json.loads(content)
    except:
        Data = {
            'user':userphone,
            'user_phone':userphone,
            'error_message': 'error1'
        }
        return render_template("usercenter.html", Data = Data)
    if res['order_message'] != '0':
        orders = res['order_message']['orders']
    else:
        orders = 'error'
    if orders != 'error':
        Data = {
            'user':userphone,
            'user_phone':userphone,
            'error_message': '0',
            'orders':[
                {
            'order_id':order['order_id'],
            'begin_time_1':order['begin_time_1'],
            'begin_time_2':order['begin_time_2'],
            'begin_name':order['begin_name'],
            'begin_phone':order['begin_phone'],
            'end_name':order['end_name'],
            'end_phone':order['end_phone'],
            'begin_city':order['begin_city'],
            'end_city':order['end_city'],
            'order_state':order['order_state'],
            } 
            for order in orders]
            }
    else:  
        Data = {
            'user':user[0],
            'user_phone':userphone,
            'error_message': 'error'
        }
    return render_template('usercenter.html', Data = Data)

@app.route('/logout')
def logout():                                           # 用户登出函数
    session.pop('userphone', None)
    return redirect('/')


if __name__ == '__main__':   
    app.run(debug = True, host= '0.0.0.0')
    '''userphone = '15316172791'
    url = "http://127.0.0.1:5004/sms"
    params = {
        'userphone': userphone
    }
    params = parse.urlencode(params)
    
    f = urlopen("%s?%s" % (url, params))
    content = f.read()
    res = json.loads(content)'''
    # print(res)  