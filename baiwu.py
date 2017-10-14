#!/usr/bin/env python
#ecoding:utf-8

#编写人：温永鑫
#职位: 运维监控&运维开发主管
#编写用途：通过与zabbix的api结合能够自动的区分语音模板，可以实现短信、语音通告
#编写日期：2017-6-15


import sys
from tools.zabbix import zabbix_function
from telephone import send_message as phone_message
from message import send_message as note_message
from message_mail import to_mail
from multiprocessing import Process



class zabbix_api_expand(zabbix_function):

	@classmethod
    def get_application(cls, itemid):
        params = {"output":"applications", "itemids":itemid, "selectApplications":["name","applicationid"]}
        try:
            return cls.get_item(params)['result'][0]['applications'][0]['name']
        except:
            return 'other'

#如果发生无法发送报警则紧急默认邮件方式报警。每次执行循环10次
def Wnergency_Alarn(type, **kwargs):
	
	process = []
	for count in range(10):
		title = u'异常发现'
		process.append(Process(target=to_mail, args=(kwargs['email'], title, kwargs['content'])))

	for p in process:
		p.start()

	for p in process:
		p.join()

	#发送错误信息
	if type == 'phone'or type == 'message':
		error_message = kwargs['error']
		to_mail(kwargs['email'], error_message, error_message)


def main(phone, title, content):

	telephone = phone.split('@')[0]
	application_name = zabbix_api_expand.get_application(title)

	#如果发生错误则执行邮件报警方式
	send_phone = phone_message(telephone, application_name)
	if send_phone != 'ok':
		Wnergency_Alarn('phone', email=phone, title=title, content=content, error=send_phone)

	telphone_code = 'telphone_code:%s' %send_phone
	note_message(telephone, telphone_code)

	#如果成功则执行发送短信报警
	send_message = note_message(telephone, content)
	if send_message != 'ok':
		Wnergency_Alarn('message', email=phone, title=title, content=content, error=send_message)


if __name__=='__main__':
	main(sys.argv[1], sys.argv[2], sys.argv[3])
