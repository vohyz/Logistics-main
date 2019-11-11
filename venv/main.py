"""
物流平台中控模块主函数

2019-11-07
ZYX
"""

from flask import Flask, jsonify, request, make_response, url_for,redirect, render_template, session, Session
from flask_httpauth import HTTPBasicAuth
from aliyunsdkcore.client import AcsClient
from aliyunsdkcore.request import CommonRequest
import datetime
import pymysql
import random
import os

app = Flask(__name__, static_url_path = "")
app.config['SECRET_KEY'] = '123456'
auth = HTTPBasicAuth()

@app.route("/index")
def index():
    return render_template("index.html")

@app.route("/")
def main():
    return render_template("index.html")

@app.route("/search")
def search():
    return render_template("search.html")

@app.route("/city")
def city():
    return render_template("city.html")

@app.route("/create")
def create():
    return render_template("create.html")

@app.route("/create/order")
def order():
    return render_template("create.html")

@app.route('/login')
def login():
    return render_template('login.html')
    
@app.route('/login/in', methods=['GET', 'POST'])    
def login_in():
    print('login')
    json_data = request.json                            # 获取数据
    userphone = json_data.get("mobile")
    sms_code = json_data.get("sms_code")

    conn,cursor = connect_mysql()                       # 连接到mysql

    try:                                                # 判断验证码是否通过
        sql = 'SELECT phonenumber,code from sms_code'
        cursor.execute(sql)
        p_code = cursor.fetchall()
        #print(p_code)
        #print((userphone, sms_code) )
        if (userphone, sms_code) in p_code:             # 验证码通过
            try:                                        # 判断手机是否已被注册
                sql = 'SELECT user_phone from user'
                cursor.execute(sql)
                phonenumbers = cursor.fetchall()
                if (userphone,) in phonenumbers:        # 如果手机号已存在，则直接登录
                    session['userphone'] = userphone
                else:                                   # 如不存在则存入数据库再登录
                    sql = 'INSERT into user VALUES (%s,%s,%s)'
                    args = ('Null', 'Null', userphone)
                    session['userphone'] = userphone
                conn.commit()
                cursor.close()
                conn.close()
                session.permanent = True
                app.permanent_session_lifetime = datetime.timedelta(minutes=10)
                return jsonify(errno='ok', errmsg="登录成功")
            except Exception as e:
                return jsonify(errno='notok', errmsg="用户数据读取失败")
        else:                                           # 验证码不通过
            return jsonify(errno='notok', errmsg="验证码错误")
    except Exception as e:
        return jsonify(errno='notok',errmsg="数据库查询错误")

@app.route('/sms_code', methods=['GET', 'POST'])
def sms_code():                                         # 发送验证码
    json_data = request.json
    mobile = json_data.get("mobile")

    conn,cursor = connect_mysql()                       # 连接到mysql

    try:                                                # 判断手机是否已被注册
        sql = 'SELECT user_phone from user'
        cursor.execute(sql)
        phonenumbers = cursor.fetchall()
        if (mobile,) in phonenumbers:
            return jsonify(errno='dataexist',errmsg="该手机号已经被注册")
    except Exception as e:
        return jsonify(errno='databaseerror',errmsg="数据库查询错误")

    result = random.randint(0, 999999)                  # 生成验证码
    sms_code = "%06d" % result
    print("验证码：{}".format(sms_code))

    
    try:                                                # 调用阿里云去发送短信
        getaliyun(mobile, sms_code)
    except Exception as e:
        return jsonify(errno='databaseerror', errmsg="发送短信失败")

    try:                                                # 将手机号和验证码存入数据库
        sql = 'SELECT phonenumber from sms_code'
        cursor.execute(sql)
        phonenumbers = cursor.fetchall()
        if (mobile,) in phonenumbers:
            sql = 'UPDATE sms_code SET code = %s WHERE phonenumber = %s'
            args = (sms_code, mobile)
        else:
            sql = 'INSERT into sms_code VALUES (%s,%s)'
            args = (mobile, sms_code)
        result = cursor.execute(sql, args)
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        return jsonify(errno='codestoreerror', errmsg="手机验证码保存失败")

    return jsonify(errno='ok', errmsg="发送成功")

def connect_mysql():#链接mysql
    conn = pymysql.connect(host="cdb-518aglpe.bj.tencentcdb.com", port=10101, user="root", password="zyx1999zyx", database="service")
    cursor = conn.cursor() 
    return conn,cursor

def getaliyun(phonenumber, code):#调用阿里云去发送短信
    client = AcsClient('LTAIyNuWycN5rsY5', 'vRqO3bw3o93LmvD9m24W12bK2InFHn', 'cn-hangzhou')
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
    request.add_query_param('TemplateCode', "SMS_177242135")
    request.add_query_param('TemplateParam', "{\"code\":\"%s\"}"%code)

    response = client.do_action(request)
    print(str(response, encoding = 'utf-8'))

if __name__ == '__main__':
    '''
    conn,cursor = connect_mysql()
    sql='truncate table user'
    cursor.execute(sql)
    '''
    app.run(debug = True, host= '0.0.0.0')
