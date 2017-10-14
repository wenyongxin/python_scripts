#!/usr/bin/env python
#ecoding:utf-8

#编写人：温永鑫
#职位: 运维监控&运维开发主管
#用途：通过亚马逊api获取rds的cpu、内存、磁盘等信息。
#编写日期：2016-4-12



import boto
import boto.rds
import datetime
import boto.ec2.cloudwatch
import json, sys, os, re

reload(sys)
sys.setdefaultencoding('utf8')



aws_area = sys.argv[2]
aws_host = sys.argv[3]
now = datetime.datetime.utcnow()

zabbix_sender = r'/usr/bin/zabbix_sender'

zabbix_agentd = r'/etc/zabbix/zabbix_agentd.conf'

metrics = {'status': 'RDS availability','load': 'CPUUtilization','memory': 'FreeableMemory','storage': 'FreeStorageSpace','network_in':'NetworkReceiveThroughput','network_out':'NetworkTransmitThroughput'}

db_classes = {'db.t1.micro': 0.615, 'db.m1.small': 1.7, 'db.m1.medium': 3.75, 'db.m1.large': 7.5, 'db.m1.xlarge': 15,
                'db.m4.large': 8, 'db.m4.xlarge': 16, 'db.m4.2xlarge': 32, 'db.m4.4xlarge': 64, 'db.m4.10xlarge': 160,
                'db.r3.large': 15, 'db.r3.xlarge': 30.5, 'db.r3.2xlarge': 61, 'db.r3.4xlarge': 122, 'db.r3.8xlarge': 244,
                'db.t2.micro': 1, 'db.t2.small': 2, 'db.t2.medium': 4, 'db.t2.large': 8, 'db.m3.medium': 3.75, 'db.m3.large': 7.5,
                'db.m3.xlarge': 15, 'db.m3.2xlarge': 30, 'db.m2.xlarge': 17.1, 'db.m2.2xlarge': 34.2, 'db.m2.4xlarge': 68.4,
                'db.cr1.8xlarge': 244,}

keys = {
	'ap-southeast-1':{'aws_key_id':亚马逊aws_key_id,'aws_secret_key':亚马逊aws_secret_key}
	}



'''连接aws rds'''
def conn_rds():
	return boto.rds.connect_to_region(aws_area, aws_access_key_id=keys[aws_area]['aws_key_id'] ,aws_secret_access_key=keys[aws_area]['aws_secret_key'])


'''获取rds数据实例'''
def get_list(rds):
	return [ i.DBName for i in rds.get_all_dbinstances()]


'''将传入的字符串转换成字典'''
def to_dict(data):
	dict = {}
	for d in data.split('-'):
		dict[d.split('=')[0]] = d.split('=')[1]
	return dict



'''将数据库名称返回json格式,用于zabbix中自动发现'''
def return_json():
	rds = conn_rds()
	rds_all = []
	dict = to_dict(sys.argv[4])
	for i in get_list(rds):
		host = '%s.%s.%s.rds.amazonaws.com' %(i,aws_host,aws_area)
		c_name = ''.join(re.findall('\D', i))
		rds_all += [{ '{#RAS_NAME}' : i, '{#AWS_ZONE}' : aws_area, '{#RDS_HOST}':  host, '{#AWS_HEAD}': aws_host, '{#AWS_CN}':dict.get(c_name, '未命名')}]
	print json.dumps({'data' : rds_all }, sort_keys=True, indent=7, ensure_ascii=False, separators=(',',':'))

'''通过ec2获取rds的性能信息'''
def get_metric(metric, start_time, end_time, step, identifier):
	ec2_conn = boto.ec2.cloudwatch.connect_to_region(aws_area, aws_access_key_id=keys[aws_area]['aws_key_id'] ,aws_secret_access_key=keys[aws_area]['aws_secret_key'])
	result = ec2_conn.get_metric_statistics(step, start_time, end_time, metric, 'AWS/RDS', 'Average', dimensions={'DBInstanceIdentifier': [identifier]})

	if result:
		if len(result) > 1:
			result = sorted(result, key=lambda k: k['Timestamp'])
			result.reverse()
		result = float('%.2f' % result[0]['Average'])

	return result




'''获取cpu负载'''
def get_cpu_load(i, identifier):
	load = get_metric(metrics['load'], now - datetime.timedelta(seconds=i * 60), now, i * 60, identifier)
	if not load:
		return 0
	else:
		return '%.2f' %float(load)


'''获取内存磁盘信息'''
def get_storage(metric, identifier):
	rds = conn_rds()
	info = rds.get_all_dbinstances(identifier)[0]
	free = get_metric(metrics[metric], now - datetime.timedelta(seconds=5 * 60),now, 1 * 60, identifier)
	return (free, info)


'''数值转换'''
def changes(free, storage):
	f = '%.2f' %(free / 1024 ** 3)
        return '%.2f' % (float(f) / storage * 100)


'''获取内存剩余'''
def get_memory(identifier):
	all = get_storage('memory', identifier)
	storage = db_classes[all[1].instance_class]
	return changes(all[0], storage)


'''获取磁盘容量'''
def get_disk(identifier):
	all = get_storage('storage', identifier)
	storage = float(all[1].allocated_storage)
	return changes(all[0], storage)

'''获取网卡流量'''
def get_network(abc, identifier):
	all = get_storage(abc, identifier)
	return '%.2f' %(all[0] / 1024 ** 3)



'''邮件通知'''
def mail_to():
	cmd = 'echo %s | '


'''将数据主动发送发送给zabbix'''
def send_active(datas):
	for name,value in datas.items():
		key = 'aws.rds[%s,%s]' %(sys.argv[4], name)
		zabbix_active_cmd = r"%s -c %s -k %s -o '%s'" %(zabbix_sender, zabbix_agentd, key, value)
	        zabbix_active = os.popen(zabbix_active_cmd).read()
		if zabbix_active:
			print 0
#			print key,value
		else:
			print 1


def main():
	if sys.argv[1] == 'json':
		return_json()
	elif sys.argv[1] == 'value':
		datas = {}
		identifier = sys.argv[4]
		for i in [1, 5, 15]:
			try:
				datas['load%s' %i] = get_cpu_load(i, identifier)
			except:
				pass
		try:
			datas['memory'] = get_memory(identifier)
		except:
			pass
		try:
			datas['disk'] = get_disk(identifier)
		except:
			pass
#		datas['input'] = get_network('network_in', identifier)
#		datas['output'] = get_network('network_out', identifier)
		send_active(datas)

		
if __name__=='__main__':
	main()

