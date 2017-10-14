#!/usr/bin/env python
#ecoding:utf-8

#编写人：温永鑫
#职位: 运维监控&运维开发主管
#编写用途：通过与zabbix的api结合能够自动的区分语音模板，可以实现短信、语音通告
#编写日期：2017-6-15


import time, hashlib, urllib, json

#字符串转换成md5
def hash_strings(src):
    myMd5 = hashlib.md5()
    myMd5.update(src)
    return myMd5.hexdigest()

class efun_infos:
    #转换当前时间格式
    now_time = time.strftime('%Y%m%d%H%M%S', time.localtime(time.time()))
    #拨打电话接口
    url = 'http://voicode.baiwutong.com:9999/voicenotify/sendVoiceNotify.do'
    #回调状态接口
    result_url = 'http://voicode.baiwutong.com:8888/VoiceClient/getVoiceCodeReport.do'
    #用户名
    user = 'test'
    #密码
    passwd = 'test'
    #声音轮询播放次数
    playTimes = 8
    #加密时间戳
    signature = hash_strings('%s%s%s' %(user, hash_strings(passwd), now_time))

#模板选择信息
voice_templates = {
   "ICMP":"gzyhwl001",
    "monitor_game":"gzyhwl002",
    "monitor_online":"gzyhwl004",
    "Interface":"gzyhwl005",
    "other":"gzyhwl006"
}

#错误编码集
code_message = {
    '100001': u'账号为空',
    '100002': u'加密签名为空',
    '100003': u'模板编号为空',
    '100004': u'被叫号码为空或不合法',
    '100005': u'播放次数不合法，只能输入1-9',
    '100006': u'参数不合法，只允许输入英文字母与数字',
    '100007': u'时间戳过期',
    '999999': u'系统内部错误'
}


#判断返回码是否正常
def is_ok(data):
    result = json.loads(data)
    if result['respCode'] == '000000':
        return 'ok'
    else:
        return code_message[result['respCode']]



#电话报警发送函数
def send_message(phone, application_name):
    data = {
        'accountSid':efun_infos.user,
        'signature':efun_infos.signature,
        'fetchDate':efun_infos.now_time,
        'calledNumber':phone,
        'templateId':voice_templates.get(application_name, voice_templates['other']),
        'playTimes':efun_infos.playTimes
    }
    try:
        return is_ok(urllib.urlopen(efun_infos.url, urllib.urlencode(data)).read())
    except:
        return u'语音接口异常'

# #获取回调函数。用户判断是否拨打成功
# def result_message():
#     result_data = {
#         'accountSid':efun_infos.user,
#         'signature':efun_infos.signature,
#         'operaType':'voiceCode',
#         'fetchDate':efun_infos.now_time
#     }
#
#     result = urllib.urlopen(efun_infos.result_url, urllib.urlencode(result_data)).read()


if __name__=='__main__':
    phone = '13924169255'
    send_message(phone, 'monitor_game')
