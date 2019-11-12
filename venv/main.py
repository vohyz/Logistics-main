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

@app.route("/search/id", methods=['GET', 'POST'])
def searchid():
    form_data = request.form
    order_id = form_data.get("ordertext")
    print(order_id)
    conn,cursor = connect_mysql()                       # 连接到mysql
    sql = 'SELECT * FROM `order` WHERE `order_id` = %s'%order_id
    cursor.execute(sql) 
    order = cursor.fetchone()
    print(order)
    Data = {}
    if order:
        Data = {
            'order_id':order[0],
            'begin_time_1':order[1][:11],
            'begin_time_2':order[1][11:],
            'begin_name':order[2],
            'begin_phone':order[3],
            'end_name':order[4],
            'end_phone':order[5],
            'begin_city':order[6],
            'end_city':order[7],
            'order_state':order[8]
            }
    return render_template("search.html", Data = Data)

@app.route("/city")
def city():
    return render_template("city.html")

@app.route("/create")
def create():
    return render_template("create.html")
@app.route("/create/failed")
def failed():
    return render_template("createfailed.html")
@app.route("/create/success")
def success():
    return render_template("createsuccess.html")
@app.route("/create/order", methods=['GET', 'POST'])
def order():
    begin_name = request.form.get('order_begin_name')
    begin_phone = request.form.get('order_begin_phone')
    begin_city = request.form.get('order_begin_city')
    end_name = request.form.get('order_end_name')
    end_phone = request.form.get('order_end_phone')
    end_city = request.form.get('order_end_city')
    '''
    此处可能需要支付
    '''
    conn,cursor = connect_mysql()                       # 连接到mysql

    sql = 'SELECT max(`order_id`) from `order`'
    cursor.execute(sql) 
    orders = cursor.fetchone()
    neworder_id = orders[0] + 1
    '''
    此处需要发送给calculate

    获得返回信息后
    '''
    try:
        sql='INSERT into `order` VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)'
        t = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        args = (pymysql.escape_string(str(neworder_id)),\
            pymysql.escape_string(t),pymysql.escape_string(begin_name),\
                pymysql.escape_string(begin_phone),pymysql.escape_string(end_name),\
                    pymysql.escape_string(end_phone),pymysql.escape_string(begin_city),\
                        pymysql.escape_string(end_city),pymysql.escape_string('进行中'),\
                            pymysql.escape_string(t),pymysql.escape_string(begin_city),\
                                pymysql.escape_string('已出发'))
        cursor.execute(sql,args)
        conn.commit()
        cursor.close()
        conn.close()
        return redirect("/create/success")
    except Exception as e:
        print(e)
        return redirect("/create/failed")
    

@app.route('/login')
def login():
    return render_template('login.html')
    
@app.route('/login/in', methods=['GET', 'POST'])    
def login_in():
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
                    cursor.execute(sql, args)
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

@app.route('/usercenter')
def usercenter():
    if 'userphone' in session:
        userphone = session['userphone']
    else:
        return redirect('/')
    conn,cursor = connect_mysql()                       # 连接到mysql
    sql = 'SELECT * from user where user_phone = %s'%userphone
    cursor.execute(sql) 
    user = cursor.fetchone()

    sql = 'SELECT * from `order` where begin_user_phone = %s'%userphone
    cursor.execute(sql) 
    orders = cursor.fetchall()
    conn.commit()
    cursor.close()
    conn.close()
    Data =[]
    if orders:
        Data = {
            'user':user[0],
            'user_phone':userphone,
            'orders':[
                {
            'order_id':order[0],
            'begin_time_1':order[1][:11],
            'begin_time_2':order[1][11:],
            'begin_name':order[2],
            'begin_phone':order[3],
            'end_name':order[4],
            'end_phone':order[5],
            'begin_city':order[6],
            'end_city':order[7],
            'order_state':order[8],
            } 
            for order in orders]
            }
    return render_template('usercenter.html', Data = Data)

@app.route('/logout')
def logout():
    session.pop('userphone', None)
    return redirect('/')

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
    sql='INSERT into `order` VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)'
    t = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    args = (pymysql.escape_string('100000'),pymysql.escape_string(t),pymysql.escape_string('1号测试人员'),pymysql.escape_string('15316172791'),pymysql.escape_string('2号测试人员'),pymysql.escape_string('13131313131'),pymysql.escape_string('上海'),pymysql.escape_string('北京'),pymysql.escape_string('进行中'))
    cursor.execute(sql,args)
    conn.commit()
    cursor.close()
    conn.close()
    '''
    app.run(debug = True, host= '0.0.0.0')
