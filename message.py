#!/usr/bin/env python
#ecoding:utf-8

#编写人：温永鑫
#职位: 运维监控&运维开发主管
#编写用途：通过与zabbix的api结合能够自动的区分语音模板，可以实现短信、语音通告
#编写日期：2017-6-15

import urllib, sys
reload(sys)
sys.setdefaultencoding('utf8')


url = 'http://sms.hbsmservice.com:8080/post_sms.do'

error_message = {
    '-10': u'余额不足',
    '-11': u'账号关闭',
    '-12': u'短信内容超过1000字（包括1000字）或为空',
    '-13': u'手机号码超过200个或合法的手机号码为空，或者手机号码与通道代码正则不匹配',
    '-14': u'msg_id超过50个字符或没有传msg_id字段',
    '-16': u'用户名不存在',
    '-18': u'访问ip错误',
    '-19': u'密码错误 或者业务代码错误 或者通道关闭 或者业务关闭',
    '-20': u'小号错误',
    '9': u'访问地址不存在'
}

def send_message(phone, content):
    data = {
        'id':'test',
        'MD5_td_code':'fb566429f6d37082c046f8e88409b9a6aaa',
        'mobile':phone,
        'msg_content':content.encode('gbk')
    }
    try:
        result = urllib.urlopen(url, urllib.urlencode(data)).read()
        if result == '0#1':
            return 'ok'
        else:
            return error_message[result]
    except:
        return u'短信接口访问异常'
