'''
Author: JFor
Date: 2020-11-06 16:34:41
LastEditors: JFor
LastEditTime: 2020-12-07 10:27:19
Description: 串口模拟类
'''

import csv
import time
import threading
import inspect
import ctypes
import math
import serial
import scipy.io as scio



def _async_raise(tid, exctype):
  """raises the exception, performs cleanup if needed"""
  tid = ctypes.c_long(tid)
  if not inspect.isclass(exctype):
    exctype = type(exctype)
  res = ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, ctypes.py_object(exctype))
  if res == 0:
    raise ValueError("invalid thread id")
  elif res != 1:
    # """if it returns a number greater than one, you're in trouble,
    # and you should call it again with exc=NULL to revert the effect"""
    ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, None)
    raise SystemError("PyThreadState_SetAsyncExc failed")

def stop_thread(thread):
  '''
  description: 停止线程
  param {*}
  return {*}
  '''  
  _async_raise(thread.ident, SystemExit)

  

class SerialPortSimulator:
    '''
    description: 
    param {*}
    return {*}
    '''    
    
    _sendFreq  = 100 # 类变量，数据发送频率


    def __init__(self):
        '''
        description: 
        param {*}
        return {*}
        '''        
        self._socket = 0 #串口中正在传输的套接字
        self._threads = [] #保存所有线程
    
    def SetUpperMachine(self, UpperMachine):
        '''
        description: 设置此串口的上位机，使用此函数连接串口和上位机
        param {*}
        return {*}
        '''        
        self._UpperMachine = UpperMachine
        UpperMachine._SetSerialPort(self)
        # SerialPortSimulator._sendFreq = self._UpperMachine._sendFreq
    
    def SetSendFreq(self, sendFreq):
        '''
        description: 设置此串口的发送频率，上位机可以使用
        param {*}
        return {*}
        '''     
        SerialPortSimulator._sendFreq = sendFreq
        # self._UpperMachine.RefreshSendFreq(sendFreq)


    # ----------------------------- Sample data from CSV file function -----------------------------
    def ReadFromCSVfileThread(self, path, repeat, sendFreq = _sendFreq,key="sample"):
        '''
        description: 读取csv文本文件，线程
        param { path csv文件路径; frequency 采样频率}
        return {*}
        '''
        self.SetSendFreq(sendFreq)
        
        thread = threading.Thread(target = self._ReadFromCSVfile, args = (path, repeat,key))
        thread.start()
        self._threads.append(thread)


    def _ReadFromCSVfile(self, *args):
        path = args[0]
        repeat = args[1]
        key = args[2]
        with open(path,encoding='utf-8') as f:
            reader = csv.DictReader(f)
            while True:
                for row in reader:
                    socket_data = row[key] # 一个采样数据
                    self._socket = socket_data
                    self._UpperMachine._ReadFromSerialPort() # 采用“中断”的方式通知上位机接收数据
                    time.sleep(1/SerialPortSimulator._sendFreq) #　延迟模拟真实数据传输情况

                if not repeat:
                    break   
    
    # ----------------------------- Sample data from .mat file -----------------------------    
    def ReadFromMatfileThread(self, path, repeat, sendFreq = _sendFreq):
        '''
        description: 读取csv文本文件，线程
        param { path csv文件路径; frequency 采样频率}
        return {*}
        '''
        self.SetSendFreq(sendFreq)
        
        thread = threading.Thread(target = self._ReadFromMatfile, args = (path, repeat))
        thread.start()
        self._threads.append(thread)


    def _ReadFromMatfile(self, *args):
        path = args[0]
        repeat = args[1]
        # with open(path,encoding='utf-8') as f:
        matdata = scio.loadmat(path)
        while True:
            # print(matdata)
            # print(type(matdata))
            for sample in matdata['val'][0]:
                socket_data = sample # 一个采样数据
                self._socket = socket_data
                self._UpperMachine._ReadFromSerialPort() # 采用“中断”的方式通知上位机接收数据
                time.sleep(1/SerialPortSimulator._sendFreq) #　延迟模拟真实数据传输情况

            if not repeat:
                break   


    # ----------------------------- Sample data from sin function -----------------------------
    def ReadFromSinThread(self, amplitute, w, shift, sampleFreq, sendFreq = _sendFreq):
        '''
        description: 采样正弦函数点，线程
        param {sampleFreq 一个周期内的采样数量, sendFreq 发送数据的频率}
        return {*}
        '''        
        self.SetSendFreq(sendFreq)
        
        thread = threading.Thread(target=self._ReadFromSin, args=(amplitute, w, shift, sampleFreq))
        self._threads.append(thread)
        thread.start()
    
    
    def _ReadFromSin(self, *args):
        '''
        description: 生成正弦函数采样点
        param {amplitute 振幅;T 周期; shift 偏移; frequency 采样频率 单位长度内采样数量}
        return {*}
        '''        
        amplitute = args[0]
        w = args[1]
        shift = args[2]
        sampleFreq = args[3]
        x = 0
        while True:
            socket_data =  amplitute * math.sin(w * x+shift)
            # print("socket_data========================="+str(socket_data))
            self._socket = socket_data
            self._UpperMachine._ReadFromSerialPort() # 采用“中断”的方式通知上位机接收数据
            x = x + (2*math.pi/w)/sampleFreq
            time.sleep(1/SerialPortSimulator._sendFreq) # 
            


    
    # ----------------------------- Sample data from port function -----------------------------
    def _ReadFromSerialPort(self, *args):
        '''
        description: 真正从串口读数据
        param {*}
        return {*}
        '''        
        port = args[0]
        freq = str(args[1])
        serials = serial.Serial(port,freq)
        if serials.isOpen():
            print('串口打开成功！\n')
            # f = open('./test.txt','w') 
            #pass
        else :
            print('串口打开失败！\n')

        try:
            getBytes=b''
            while True:
                count = serials.inWaiting()
                if count > 0:
                    data = serials.read(count)
                    if data != getBytes:
                        # print(data)
                        socket_data = data # 一个采样数据
                        self._socket = socket_data
                        self._UpperMachine._ReadFromSerialPort() # 采用“中断”的方式通知上位机接收数据
                        # f.write(data.decode('utf-8'))
                        # f.write('\n')
                        getBytes=data

        except KeyboardInterrupt:
            if serial != None:
                f.close()
                serial.close()

    def ReadFromSerialPortThread(self, port='COM5', freq=9600):
        '''
        description: 从串口读数据线程
        param {*}
        return {*}
        '''        
        thread = threading.Thread(target=self._ReadFromSerialPort, args=(port,freq))
        self._threads.append(thread)
        thread.start()


    def StopThreads(self):
        '''
        description: 停止所有正在运行以及注册过的的串口线程
        param {*}
        return {*}
        '''        
        for thread in self._threads:
            stop_thread(thread)
