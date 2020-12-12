'''
Author: JFor
Date: 2020-11-06 20:20:23
LastEditors: JFor
LastEditTime: 2020-12-07 13:05:50
Description: 
'''
from SerialPortSimulator import SerialPortSimulator
from ECG_Processor import ECGProcessor
import threading


def main():
    serialPortSimulator = SerialPortSimulator() # 串口
    ECGprocessor = ECGProcessor() # 上位机
    serialPortSimulator.SetUpperMachine(ECGprocessor) #　连接串口与上位机

    # ECGprocessor.SetBufferSize(1000) # 
    # ECGprocessor.SetFrequency(sampleFreq=200, curveFreq=10) # 
    # csvPath = r"F:\VS\Python\医学仪器\电子仪上位机\Data\heartbeats.csv" # 
    # serialPortSimulator.ReadFromCSVfileThread(path=csvPath,sendFreq=100,repeat=True) # 串口线程开始工作，有数据时会通知到上位机读取
    
    # ECGprocessor.SetBufferSize(1000)
    # ECGprocessor.SetFrequency(sampleFreq=200,curveFreq=100)
    # serialPortSimulator.ReadFromSinThread(amplitute=10,w=1,shift=0,sampleFreq=200,sendFreq=100) # 每个周期采样10个，每秒发送100个采样数据，1s收到10个周期

    # ECGprocessor.SetBufferSize(2400)
    # ECGprocessor.SetFrequency(sampleFreq=9600,curveFreq=2)
    # serialPortSimulator.ReadFromSerialPortThread(port='COM5', freq=9600)

    # ECGprocessor.SetBufferSize(1000)
    # ECGprocessor.SetFrequency(sampleFreq=500, curveFreq=15)
    # matpath = r"F:\VS\Python\医学仪器\电子仪上位机\Data\101m.mat"  
    # serialPortSimulator.ReadFromMatfileThread(path=matpath,repeat=True,sendFreq=500)    
    # ECGprocessor.SetMarkOff()
    



    # ECGprocessor.SetBufferSize(1000) # 
    # ECGprocessor.SetFrequency(sampleFreq=200, curveFreq=10) # 
    # csvPath = r"F:\VS\Python\医学仪器\电子仪上位机\Data\Spo2orgData2020-10-20-09-43-26.csv" # 
    # serialPortSimulator.ReadFromCSVfileThread(path=csvPath,sendFreq=100,repeat=True,'PulseWave') # 串口线程开始工作，有数据时会通知到上位机读取
        
    ECGprocessor.SetBufferSize(1000)
    ECGprocessor.SetFrequency(sampleFreq=500, curveFreq=15)
    matpath = r"F:\VS\Python\医学仪器\电子仪上位机\Data\xxSpo2orgData2020-10-20-09-43-26.mat"  
    serialPortSimulator.ReadFromMatfileThread(path=matpath,repeat=True,sendFreq=500)
    ECGprocessor.SetMarkOff()

    # ECGprocessor.SetBufferSize(1000)
    # ECGprocessor.SetFrequency(sampleFreq=500, curveFreq=15)
    # matpath = r"F:\VS\Python\医学仪器\电子仪上位机\Data\data2.mat"  
    # serialPortSimulator.ReadFromMatfileThread(path=matpath,repeat=True,sendFreq=500)


    

    # ECGprocessor.SetDefaultTheme(pltTheme='dark_background')
    # ECGprocessor.SetDefaultTheme(sgTheme='DarkBrown3',pltTheme='seaborn-darkgrid')
    # ECGprocessor.SetDefaultTheme(sgTheme='DarkBlue12',pltTheme='seaborn-whitegrid')
    # ECGprocessor.SetDefaultTheme(sgTheme='DarkBrown3',pltTheme='seaborn-whitegrid')
    # ECGprocessor.SetDefaultTheme(sgTheme='DarkBrown3',pltTheme='Solarize_Light2')
    ECGprocessor.SetDefaultTheme(sgTheme='DarkBrown3',pltTheme='selfmade1')
    ECGprocessor.DrawGraphic() # 

if __name__ == '__main__':
    main()