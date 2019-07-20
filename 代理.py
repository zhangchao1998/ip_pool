import requests
from lxml import etree
import pymysql
import time
import smtplib
from email.mime.text import MIMEText
import os


headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.131 Safari/537.36'
}


def test_ip(ip,host):
    """
    用于对代理IP的可用性进行验证
    如果可用返回True
    如果不可用返回False
    """
    proxies = {'https':str(ip)+':'+str(host)}
    try:
        response = requests.get(url='https://www.baidu.com/', headers=headers, proxies=proxies, timeout=2)
    except:
        return False
    else:
        if response.status_code == 200:
            return True
        else:
            return False


def send_email(title,text):
    """
    用于发送邮件
    需要输入两个参数
    邮件标题title和邮件内容text
    """
    mailserver = "smtp.163.com"          #smtp服务器
    username_send = "username@163.com"          #发送方的邮箱地址
    password = "password"          #发送邮箱的密码
    username_to = "username@qq.com"          #接收方的邮箱地址，如有多个用逗号隔开
    mail = MIMEText(text)          #邮件内容
    mail['Subject'] = title          #邮件标题
    mail['From'] = username_send
    mail['To'] = username_to
    smtp = smtplib.SMTP(mailserver, port=25)          #Windows环境下使用
    # smtp = smtplib.SMTP_SSL(mailserver,port=465)          #Linux环境下使用
    smtp.login(username_send, password)
    smtp.sendmail(username_send, username_to, mail.as_string())
    smtp.quit()

try:
    send_email('运行状态','云主机脚本开始运行')
    one = True
    while True:          #脚本主循环
        if one:          #如果one的值为True则爬取十页代理IP
            db = pymysql.connect('localhost', 'username', 'password', 'proxies')          #连接数据库
            cursor = db.cursor()
            sql = """select proxy,host from can_use"""          #读取当前库中所有代理IP
            cursor.execute(sql)
            can_use = cursor.fetchall()
            for i in range(1,10):
                url = 'https://www.xicidaili.com/wn' + '/' + str(i)
                response = requests.get(url=url, headers=headers).content.decode('utf-8')
                tree = etree.HTML(response)
                tr = tree.xpath('//tr')[1:]
                ips = []
                for one_tr in tr:
                    ip = one_tr.xpath('./td[2]/text()')[0]
                    host = one_tr.xpath('./td[3]/text()')[0]
                    ips.append((ip,host))
                for one_ip in ips:
                    if test_ip(one_ip[0],one_ip[1]) and one_ip not in can_use:          #如果该IP可用且数据库中没有则添加到数据库中
                        sql = """insert into can_use(types,proxy,host,times,weight)values ('https','{}','{}',{},0)""".format(one_ip[0], one_ip[1], int(time.time()))
                        try:
                            cursor.execute(sql)
                            db.commit()
                            print('{}:{}可用，加入数据库'.format(one_ip[0],one_ip[1]))
                        except:
                            db.rollback()
            db.close()
            one = False          #将one值设为False
        if int(time.time())%3600 < 60:          #整点时进行爬取
            db = pymysql.connect('localhost', 'username', 'password', 'proxies')          #连接数据库
            cursor = db.cursor()
            sql = """select proxy,host,weight from can_use"""          #查询当前库中所有代理IP
            cursor.execute(sql)
            can_use_ip = cursor.fetchall()
            for one_can_use in can_use_ip:          #验证当前库中所有代理IP的可用性
                if test_ip(one_can_use[0],one_can_use[1]):          #如果可用则此代理IP权重加一
                    weight = one_can_use[2]+1
                    if weight > 24:          #权重上限为24
                        weight = 24
                    sql = """update can_use set weight={} where (proxy='{}' and host='{}')""".format(weight,one_can_use[0],one_can_use[1])
                    try:
                        cursor.execute(sql)
                        db.commit()
                        print('{}:{}权重+1,当前权重{}'.format(one_can_use[0],one_can_use[1],one_can_use[2]+1))
                    except:
                        db.rollback()
                else:          #如果不可用则此代理IP权重减一
                    sql = """update can_use set weight={} where (proxy='{}' and host='{}')""".format(one_can_use[2] - 1,one_can_use[0],one_can_use[1])
                    try:
                        cursor.execute(sql)
                        db.commit()
                        print('{}:{}权重-1,当前权重{}'.format(one_can_use[0],one_can_use[1],one_can_use[2]-1))
                    except:
                        db.rollback()
            sql = """select proxy,host,weight from can_use"""
            cursor.execute(sql)
            can_use = cursor.fetchall()
            for one_can_use in can_use:
                if one_can_use[2] < -10:          #当代理IP的权重低于-10时从数据库中删除
                    sql = """delete from can_use where (proxy='{}' and host='{}')""".format(one_can_use[0], one_can_use[1])
                    try:
                        cursor.execute(sql)
                        db.commit()
                        print('已将{}:{}从数据库中删除'.format(one_can_use[0],one_can_use[1]))
                    except:
                        db.rollback()
            sql = """select proxy,host from can_use where weight >= 0"""
            cursor.execute(sql)
            can_use_pro = cursor.fetchall()
            if len(can_use_pro) < 5:          #当库中权重大于零的IP个数小于5个时，将one的值设为True
                one = True
            sql = """select proxy,host from can_use"""
            cursor.execute(sql)
            can_use = cursor.fetchall()
            url = 'https://www.xicidaili.com/wn/1'
            response = requests.get(url=url, headers=headers).content.decode('utf-8')
            tree = etree.HTML(response)
            tr = tree.xpath('//tr')[1:]
            ips = []
            for one_tr in tr:
                ip = one_tr.xpath('./td[2]/text()')[0]
                host = one_tr.xpath('./td[3]/text()')[0]
                ips.append((ip, host))
            for one_ip in ips:
                if test_ip(one_ip[0], one_ip[1]) and one_ip not in can_use:          #验证代理IP的可用性，如果可用且数据库中没有此IP则将其加入数据库
                    sql = """insert into can_use(types,proxy,host,times,weight)values ('https','{}','{}',{},0)""".format(one_ip[0],one_ip[1],int(time.time()))
                    try:
                        cursor.execute(sql)
                        db.commit()
                        print('{}:{}可用，加入数据库'.format(one_ip[0], one_ip[1]))
                    except:
                        db.rollback()
            db.close()
        time.sleep(10)          #循环间隔10秒
except:
    send_email('运行状态','云主机脚本已停止运行')
finally:
    time.sleep(1000)
    os.system('python3 /root/代理01.py')          #尝试重新运行脚本
