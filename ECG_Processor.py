'''
Author: JFor
Date: 2020-11-02 20:04:22
LastEditors: JFor
LastEditTime: 2020-12-07 11:49:48
Description: 心电数据处理类
'''
# import pyqtgraph as pg
import numpy as np
import array
from multiprocessing import Queue
import copy
import collections
import matplotlib.pyplot as plt
import matplotlib.figure
from matplotlib.backends.backend_tkagg import FigureCanvasAgg
import io
import PySimpleGUI as sg
import threading
import time
import inspect
import ctypes
from ECG_Marker import ECGMarker


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

#============================================ Upper Machine Class ============================================#

class ECGProcessor:
    '''
    description: 上位机
    param {*}
    return {*}
    '''    
    def __init__(self):
        '''
        description: 
        param {*}
        return {*}
        '''    
        self._buffer = collections.deque() # 数据缓存区，保存一部分采样点数据
        self._bufferSize = 1250 # 默认最大数据缓存大小为125个数据    
        self._frequency = 125 # 默认上位机采样频率为每秒125个
        self._threads = [] # 保存所有线程
        self._refreshFreq = 2 # 上位机曲线的刷新频率，默认每0.5s刷新一次
        self._panelRefreshFreq = 10 # 上位机面板数值刷新频率，默认每0.1s刷新一次
        # self._sendFreq = self._frequency # 串口的发送频率，默认保持与采样频率一致

        # for i in range(10):
        #     self._buffer.append(i)
        self._minMarkSize = 500 # 可以计算PQRST点的最少样本量
        # self._aspect = 1/100 # 图形横纵单位长度比值
        self._figsize_x = 1 #图形长度
        self._figsize_y = 4 #图形高度
        self._markOn = True # 是否标记特征点


    def _SetSerialPort(self, SerialPort):#　名称已定，不要更改，被串口调用
        '''
        description: 设置此上位机连接的串口,暴露给串口使用的函数
        param {*}
        return {*}
        '''        
        self._SerialPort = SerialPort
    
    def SetFrequency(self, sampleFreq = 125, curveFreq=2, panelFreq=10):
        self._frequency = sampleFreq # 默认上位机采样频率为每秒125个
        # self._SerialPort.SetSendFreq(self._frequency)
        self._refreshFreq = curveFreq # 上位机曲线的刷新频率，默认每0.5s刷新一次
        self._panelRefreshFreq = panelFreq # 上位机面板数值刷新频率，默认每0.1s刷新一次

    def SetBufferSize(self,size):
        '''
        description: 设置上位机数据缓存的大小
        param {*}
        return {*}
        '''        
        self._bufferSize = size
    
    # def RefreshSendFreq(self, sendFreq):
    #     '''
    #     description: 由串口调用，告知上位机其发送频率
    #     param {*}
    #     return {*}
    #     '''
    #     self._sendFreq = sendFreq       

    def SetDefaultTheme(self, sgTheme=None, pltTheme=None):
        '''
        description: 设置默认的样式，
        param {sgTheme：PySimpleGui的样式，pltTheme：matplotlib的样式}
        return {*}
        ''' 
        self._defaultTheme={
            'sgTheme': sgTheme,
            'pltTheme': pltTheme,
        }       
        sg.theme(sgTheme)
        plt.style.use(pltTheme)
    
    def SetMarkOn(self):
        self._markOn = True
    
    def SetMarkOff(self):
        self._markOn = False

    def _ReadFromSerialPort(self): #　名称已定，不要更改，被串口调用
        '''
        description: 从串口读取一个socket数据，暴露给串口使用的通知函数
        param {*}
        return {*}
        '''        
        socket = self._SerialPort._socket
        self._AddToBuffer(socket) 

    def _AddToBuffer(self,data):
        '''
        description: 添加数据到缓存区，超过设定大小会挤走队列前面的数据
        param {*}
        return {*}
        '''
        remain = self._bufferSize - len(self._buffer)
        if remain<=0:
            for _ in range(-remain+1):
                self._buffer.popleft()
        self._buffer.append(data)
        # self._printBuffer()

    def _printBuffer(self):
        buffer = self._buffer.copy()
        for _ in range(len(self._buffer)):
            data = buffer.popleft()
            print(data)
        print("==========================")

    # -------------------------------- Thread management function --------------------------------
    def StopThreads(self):
        '''
        description: 停止所有正在运行以及注册过的的串口线程
        param {*}
        return {*}
        '''        
        for thread in self._threads:
            stop_thread(thread) # 停止上位机的所有线程
        self._threads=[]
        
        # self._SerialPort.StopThreads() # 停止串口的所有线程

    # -------------------------------- P-Q-R-S-T Points Mark Thread--------------------------------
    def _drawPoints(self, axes, point, key_x=lambda tup:tup[0], key_y=lambda tup:tup[1], color='blue', s=10, annotate = True, text='', shift=(1,1), fontsize=10):
        '''
        description: 在指定点画点和做注释
        param {
            color：点颜色，
            s:点大小
            annotate：是否有注释
            text: 注释字
            shift: 点注释的相对于点的偏移,使用的x,y与点的x,y对应
            fontsize:点注释的字大小
        }
        return {*}
        '''
        x, sihft_x = key_x(point)*(1/self._frequency), key_x(shift)*(1/self._frequency)
        y, sihft_y = key_y(point), key_y(shift)
        axes.scatter(x, y, s=s, c=color) 
        axes.annotate(s=text,xy=(x+sihft_x, y+sihft_y),fontsize=fontsize)# 设置字体大小为 16
              
        # return plt
    
    def _packDrawPointParams(self,color='blue', s=10,annotate = True,text='R', shift=(1,1), fontsize=15):
        '''
        description: 将点的绘制参数打包成dict
        param {*}
        return {*}
        '''        
        paramDic = {               
            'color':color, # 点颜色
            's':s, # 点大小
            'annotate': annotate, # 是否需要注释
            'text':text, # 注释文本
            'shift':shift, # 注释相对于点的偏移
            'fontsize':fontsize, # 注释字体大小
        }
        return paramDic

    def _markAndDrawPoints(self, axes, paramDics, R_localMaxRange=10):
        '''
        description: 算出指定点并指定到plt图形中
        param {
            绘制R点的参数用一个键值对来传递：
            'R': {
                'color':'blue', # 点颜色
                's':10, # 点大小
                'annotate': True, # 是否需要注释
                'text':'R', # 注释文本
                'shift':(1,1), # 注释相对于点的偏移
                'fontsize':15, # 注释字体大小
            }
        }
        return {*}
        '''        
        if len(self._buffer) <= self._minMarkSize:
            return None
        samples = copy.deepcopy(self._buffer)
        markPoints = self._ECGMarker.mark(samples,R_localMaxRange=R_localMaxRange) # 得到标记点字典,点都是第一个是y,每二个是x
        R_points = markPoints['R']
        Q_points = markPoints['Q']
        P_points = markPoints['P']
        S_points = markPoints['S']
        T_points = markPoints['T']
        for point in R_points:
            if point == None:
                break
            paramDic = paramDics['R']
            self._drawPoints(axes,point,key_x=lambda tup:tup[1], key_y=lambda tup:tup[0], color=paramDic['color'], s=paramDic['s'],annotate = paramDic['annotate'],text=paramDic['text'], shift=paramDic['shift'], fontsize=paramDic['fontsize'])
        for point in Q_points:
            if point == None:
                break
            paramDic = paramDics['Q']
            self._drawPoints(axes,point,key_x=lambda tup:tup[1], key_y=lambda tup:tup[0], color=paramDic['color'], s=paramDic['s'],annotate = paramDic['annotate'],text=paramDic['text'], shift=paramDic['shift'], fontsize=paramDic['fontsize'])
        for point in P_points:
            if point == None:
                break
            paramDic = paramDics['P']
            self._drawPoints(axes,point,key_x=lambda tup:tup[1], key_y=lambda tup:tup[0], color=paramDic['color'], s=paramDic['s'],annotate = paramDic['annotate'],text=paramDic['text'], shift=paramDic['shift'], fontsize=paramDic['fontsize'])
        for point in S_points:
            if point == None:
                break
            paramDic = paramDics['S']
            self._drawPoints(axes,point,key_x=lambda tup:tup[1], key_y=lambda tup:tup[0], color=paramDic['color'], s=paramDic['s'],annotate = paramDic['annotate'],text=paramDic['text'], shift=paramDic['shift'], fontsize=paramDic['fontsize'])
        for point in T_points:
            if point == None:
                break
            paramDic = paramDics['T']
            self._drawPoints(axes,point,key_x=lambda tup:tup[1], key_y=lambda tup:tup[0], color=paramDic['color'], s=paramDic['s'],annotate = paramDic['annotate'],text=paramDic['text'], shift=paramDic['shift'], fontsize=paramDic['fontsize'])
        
    # def _markPoints(self, *args):
    #     '''
    #     description: 标记PQRST点
    #     param {*}
    #     return {*}
    #     '''        
    #     R_localMaxRange = args[0]
        
    #     while True:
    #         self._markAndDrawPoints(R_localMaxRange)
    #         time.sleep(1/self._refreshFreq) # 刷新频率与figure保持一致，用self._refreshFreq
    
    # def _markPointsThread(self,R_localMaxRange=10):
    #     '''
    #     description: 标记PQRST点的线程
    #     param {*}
    #     return {*}
    #     '''        
    #     self._ECGMarker = ECGMarker()
    #     markThread = threading.Thread(target=self._markPoints, args=(R_localMaxRange))
    #     self._threads.append(markThread)
    #     markThread.start()



    # ----------------------------- The draw figure helpful function -----------------------------
    
    def _Get_Sin_Figure_From_Matplotlib(self):
        '''
        description: matplotlib对象生成，正弦函数图像, 测试用
        param {*}
        return {*}
        '''        
        fig = matplotlib.figure.Figure(figsize=(5, 4), dpi=100)
        t = np.arange(0, 3, .01)
        fig.add_subplot(111).plot(t, 2 * np.sin(2 * np.pi * t))
        
        return fig

    def _Get_ECG_Figure_From_Matplotlib(self):
        '''
        description: matplotlib对象生成，ECG图像
        param {*}
        return {*}
        '''        
        fig = matplotlib.figure.Figure(figsize=(self._figsize_x*len(self._buffer)/100, self._figsize_y), dpi=100)
        buffer = copy.deepcopy(self._buffer)
        t = np.linspace(0,(len(buffer)-1)*(1/self._frequency),len(buffer))
        axes_1 = fig.add_subplot(111)
        axes_1.plot(t,buffer) # TODO 曲线压缩问题，待解决
        # axes_1.set_aspect(self._aspect) # 设置横纵单位比
        if self._markOn:
            paramDics = {
                'R': self._packDrawPointParams(color='blue', s=20,annotate = True,text='R', shift=(1,1), fontsize=15),
                'Q': self._packDrawPointParams(color='blue', s=20,annotate = True,text='Q', shift=(1,1), fontsize=15),
                'P': self._packDrawPointParams(color='blue', s=20,annotate = True,text='P', shift=(1,1), fontsize=15),
                'S': self._packDrawPointParams(color='blue', s=20,annotate = True,text='S', shift=(1,1), fontsize=15),
                'T': self._packDrawPointParams(color='blue', s=20,annotate = True,text='T', shift=(1,1), fontsize=15)
            }
            self._markAndDrawPoints(axes_1, paramDics, R_localMaxRange=10)

        return fig

    def _ReplaceFigure_In_Pysimplegui_test(self, element, figure):
        plt.close('all')  # erases previously drawn plots
        canv = FigureCanvasAgg(figure)
        buf = io.BytesIO()
        canv.print_figure(buf, format='png')
        if buf is None:
            return None
        buf.seek(0)
        element.update(data=buf.read())

        return canv


    def _ReplaceFigure_In_Pysimplegui(self, *args):
        """
        Draws the previously created "figure" in the supplied Image Element

        :param element: an Image Element
        :param figure: a Matplotlib figure
        :return: The figure canvas
        """
        while True:
            element = args[0]
            GetFigure = args[1]

            plt.close('all')  # erases previously drawn plots
            canv = FigureCanvasAgg(GetFigure()) # 画图函数循环调用
            buf = io.BytesIO()
            canv.print_figure(buf, format='png')
            # if buf is None:
            #     return None
            buf.seek(0)
            element.update(data=buf.read())
            # return canv
            time.sleep(1/self._refreshFreq)

    
    
    def _RefreshFigureThread(self, element = None, GetFigure = None): 
        '''
        description: 创建线程刷新图形, element是一个Image控件，figure是一个matplotlib对象
        :param element: an Image Element
        :param figure: a Matplotlib figure
        '''        
        self._ECGMarker = ECGMarker()
        ECGfigureThread = threading.Thread(target=self._ReplaceFigure_In_Pysimplegui, args = (element,GetFigure))
        self._threads.append(ECGfigureThread)
        ECGfigureThread.start()
        
    # ----------------------------- The draw panel helpful function ----------------------------- 
    def _RefreshPanelOnce(self):
        '''
        description: 刷新一次面板左侧的数值
        param {*}
        return {*}
        '''        
        # print('NOS:' + str(len(self._buffer)))
        self._window['-NOS-'].update(value='NOS:' + str(len(self._buffer)))

    def _RefreshPanel(self, *args):
        '''
        description: 持续刷新面板数值
        param {*}
        return {*}
        '''    
        frequency = args[0]    
        
        while True:
            self._RefreshPanelOnce()
            time.sleep(1/frequency)

    def _RefreshPanelThread(self, frequency, placeholder=None):
        '''
        description: 面板数值刷新线程
        param {*}
        return {*}
        '''        
        panelThread = threading.Thread(target=self._RefreshPanel, args=(frequency,placeholder))
        self._threads.append(panelThread)
        panelThread.start()


    # ----------------------------- The GUI Section -----------------------------
    def _createWindow(self):
        """
        Defines the window's layout and creates the window object.
        This function is used so that the window's theme can be changed and the window "re-started".

        :return: The Window object
        :rtype: sg.Window
        """
        
        matplotlibStyles = [sg.T('Matplotlib Styles'), sg.Combo(plt.style.available, default_value=self._defaultTheme['pltTheme'], size=(15, 10), key='-STYLE-')]
        pysimpleguiThemes = [sg.T('PySimpleGUI Themes'), sg.Combo(sg.theme_list(), default_value=self._defaultTheme['sgTheme'], size=(15, 10), key='-THEME-')]
        top_bar = matplotlibStyles + pysimpleguiThemes
        
        # print(str(self._bufferSize)+ " " + str(self._frequency) + " " + str(self._SerialPort._sendFreq))

        left_bar = [
            [sg.T(text='NOS:', key='-NOS-', size=(8,1))], # Number Of Samples
            [sg.T('BuS:'), sg.Slider(range=(1,2000), key='BuS', orientation='h', enable_events=True, default_value=self._bufferSize, resolution=1)],  # 最大显示的采样个数 # TODO 滑动事件
            [sg.T('SaF:'), sg.Slider(range=(1,1000), key='SaF', orientation='h', enable_events=True, default_value=self._frequency, resolution=1)], # 采样频率
            [sg.T('SeF:'), sg.Slider(range=(1,1000), key='SeF', orientation='h', enable_events=True, default_value=self._SerialPort._sendFreq, resolution=1)], # 发送频率
            # [sg.T('Asp:'), sg.Slider(range=(1,500), key='aspect', orientation='h', enable_events=True, default_value=1/self._aspect, resolution=1)], # 图形横纵单位长度比
            [sg.T('FSX:'), sg.Slider(range=(1,50), key='FSX', orientation='h', enable_events=True, default_value=self._figsize_x, resolution=1)], # 图形区域长度
            [sg.T('FSY:'), sg.Slider(range=(1,50), key='FSY', orientation='h', enable_events=True, default_value=self._figsize_y, resolution=1)], # 图形区域高度

        ]
        layout = [
            [sg.T('ECG Analyser-----by ZZK', font='Any 20')],
            top_bar,
            [sg.Col(left_bar), sg.Image(key='-IMAGE-')],
            [sg.B('Draw'), sg.B('Exit'), sg.B('Print')]
        ]
        
        window = sg.Window('Matplotlib Embedded Template', layout, finalize=True)
        
        return window


    def DrawGraphic(self):
        '''
        description:
        param {*}
        return {*}
        '''
        self._window = self._createWindow()
        self._RefreshFigureThread(element=self._window['-IMAGE-'], GetFigure=self._Get_ECG_Figure_From_Matplotlib) # matplotlib图形数据替换图像
        self._RefreshPanelThread(self._panelRefreshFreq)
        # self._ReplaceFigure_In_Pysimplegui_test(self._window['-IMAGE-'], self._Get_ECG_Figure_From_Matplotlib())
        while True:
            event, values = self._window.read()
            if event == sg.WINDOW_CLOSED or event == 'Exit':
                self.StopThreads()
                self._SerialPort.StopThreads()
                break
            if event == 'Draw':
                # if values['-THEME-'] != sg.theme():  # pysimplegui的新主题需要重新生成窗口才能生效
                self.StopThreads()
                
                self._window.close()
                sg.theme(values['-THEME-'])
                self._defaultTheme['sgTheme'] = values['-THEME-']
                self._window = self._createWindow()

                self._RefreshFigureThread(element=self._window['-IMAGE-'], GetFigure=self._Get_ECG_Figure_From_Matplotlib)
                self._RefreshPanelThread(self._panelRefreshFreq)
                    
                if values['-STYLE-']: # 设置matplotlib样式
                    plt.style.use(values['-STYLE-'])
                    self._defaultTheme['pltTheme']=values['-STYLE-']
            if event == 'Print':
                print(self._buffer)

            if event == 'BuS':
                self._bufferSize = int(values['BuS'])
            elif event == 'SaF':
                self._frequency = int(values['SaF'])
            elif event == 'SeF':
                self._SerialPort.SetSendFreq(int(values['SeF']))
            # elif event == 'aspect':
            #     self._aspect = 1/values['aspect']
            elif event == 'FSX':
                self._figsize_x = values['FSX']
            elif event == 'FSY':
                self._figsize_y = values['FSY']
            
        
def main():
    ECGprocessor = ECGProcessor() # 上位机
    ECGprocessor.DrawGraphic()

if __name__ == '__main__':
    main()