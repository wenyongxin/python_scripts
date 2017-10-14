#!/usr/bin/env python
#ecoding:utf-8

#开发人员：温永鑫
#用途：用于做tomcat的性能监控
#职位: 运维监控&运维开发主管
#编写日期：2017-7-12

'''
Free memory:空闲内存大小。
Total memory:总内存大小。
Max memory:最大内存大小。
Max threads:最大线程数。
Current thread count:最近运行的线程数。
Max processing time:最大CPU时间。
Processing time:CPU消耗总时间。
Request count:请求总数。
Error count:错误的请求数。
Bytes received:接收字节数。
Bytes sent:发送字节数。
'''


import urllib2, json, sys
import xml.etree.ElementTree as ET


#返回编码
status = {'ok':1, 'error':0}

#获取tomcat的状态
class tomcat():

    __url = 'http://127.0.0.1:8080/manager/status?XML=true'
    __password = 'admin'
    __username = 'admin'

    #读取tomcat的status页面信息
    @classmethod
    def read_page(cls):
        try:
            password_mgr = urllib2.HTTPPasswordMgrWithDefaultRealm()
            password_mgr.add_password(None,cls.__url,cls.__username,cls.__password)
            handler = urllib2.HTTPBasicAuthHandler(password_mgr)
            opener=urllib2.build_opener(handler)
            urllib2.install_opener(opener)
            req = urllib2.Request(cls.__url)
            handle = urllib2.urlopen(req, None)
            page = handle.read()
            return page
        except:
            return False

    #将tomcat页面语言转换成xml
    @classmethod
    def to_xml(cls):
        root = cls.read_page()
        if root:
            return ET.fromstring(root)
        else:
            return root

    #返回tomcat的状态
    @classmethod
    def get_status(cls):
        if cls.to_xml().tag == 'status':
            return status['ok']
        else:
            return status['error']

    #返回tomcat的内存信息
    @classmethod
    def get_mem(cls):
        memory = cls.to_xml().find('.//memory')
        #Free memory:空闲内存大小。
        free_memory = float(memory.get('free'))
        #Total memory:总内存大小。
        total_memory = float(memory.get('total'))
        #Max memory:最大内存大小。
        max_memory = float(memory.get('max'))
        return free_memory,total_memory, max_memory

    #返回内存总容量
    @classmethod
    def get_men_total(cls):
        free_memory,total_memory, max_memory = cls.get_mem()
        return total_memory

    #返回内存的可用容量
    @classmethod
    def get_mem_free(cls):
        free_memory,total_memory, max_memory = cls.get_mem()
        return free_memory

    #返回使用容量
    @classmethod
    def get_mem_used(cls):
        free_memory,total_memory, max_memory = cls.get_mem()
        return total_memory - free_memory

    #放回内存的使用率
    @classmethod
    def get_mem_used_percent(cls):
        free_memory,total_memory, max_memory = cls.get_mem()
        return float(cls.get_mem_used()/ total_memory * 100)

    #返回tomcat线程状况
    @classmethod
    def get_thread(cls):
        tomcat_thread_infos = {}
        for connector in cls.to_xml().findall('./connector'):
            connector_name = str(connector.get('name')).replace('"','')
            #用于返回线程信息
            thread = connector.find('./threadInfo')
            #Max threads:最大线程数。
            max_thread = float(thread.get('maxThreads'))
            #Current thread busy: 繁忙线程数
            busy_thread = float(thread.get('currentThreadsBusy'))
            #Current thread count:最近运行的线程数。
            current_thread = float(thread.get('currentThreadCount'))

            #用于返回返回信息
            thread_time = connector.find('./requestInfo')
            #Max processing time:最大CPU时间。
            max_processing = thread_time.get('maxTime')
            #Processing time:CPU消耗总时间。
            processing_time = thread_time.get('processingTime')
            #Request count:请求总数
            request_count = thread_time.get('requestCount')
            #Error count:错误的请求数。
            error_count = thread_time.get('errorCount')
            #Bytes received:接收字节数。
            bytesReceived = thread_time.get('bytesReceived')
            #Bytes sent:发送字节数。
            bytesSent = thread_time.get('bytesSent')

            datas = {
                'max_thread':max_thread, 'busy_thread':busy_thread, 'current_thread':current_thread,
                'max_processing':max_processing, 'processing_time':processing_time, 'request_count':request_count,
                'error_count':error_count,'bytesReceived':bytesReceived, 'bytesSent':bytesSent
            }

            tomcat_thread_infos[connector_name] = datas
        return tomcat_thread_infos

    @classmethod
    def thread_project_discovery(cls):
        datas = []
        for key in cls.get_thread().keys():
            datas += [{"{#TOMCAT_NAME}":key}]
        return json.dumps({'data': datas},sort_keys=True,indent=7,separators=(',',':'))

    @classmethod
    def get_thread_val(cls, project, key):
        return cls.get_thread()[project][key]


def main():
    #返回项目名称
    try:
        if sys.argv[1] == 'json':
            print tomcat.thread_project_discovery()
        elif sys.argv[1] == 'value':
            if sys.argv[2] in tomcat.get_thread().keys():
                print tomcat.get_thread_val(sys.argv[2], sys.argv[3])
            elif sys.argv[2] == 'used':
                print tomcat.get_mem_used()
            elif sys.argv[2] == 'total':
                print tomcat.get_men_total()
            elif sys.argv[2] == 'free':
                print tomcat.get_mem_free()
            elif sys.argv[2] == 'pused':
                print tomcat.get_mem_used_percent()
    except:
        message = u'''
        使用方法：
        各项目的现成通过自动发现来区分
        python tomcat_info.py json  方式返回自动发现工程
        工程调用线程状况
        python tomcat_info.py value 项目名称 max_thread/busy_thread
        max_thread          最大线程数
        busy_thread         繁忙线程数
        current_thread      最近运行的线程数
        max_processing      最大CPU时间
        processing_time     CPU消耗总时间
        request_count       请求总数
        error_count         错误的请求数
        bytesReceived       接收字节数
        bytesSent           发送字节数
        返回内存信息:
        python tomcat_info.py value used   内存使用容量
        python tomcat_info.py value total  总内存容量
        python tomcat_info.py value free   内存剩余容量
        python tomcat_info.py value pused  内存使用率

        zabbix key名称：efun.tomcat[]
        '''
        print message

if __name__=='__main__':
    main()
