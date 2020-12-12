'''
Author: JFor
Date: 2020-11-22 16:13:12
LastEditors: JFor
LastEditTime: 2020-12-06 22:49:59
Description: ECG波形的标记类，标定 P-Q-R-S-T 点
'''
from WaveFilter import WaveFilter


class ECGMarker():
    '''
    description: ECG波形的标记类，标定 P-Q-R-S-T 点
    param {*}
    return {*}
    '''    
    
    
    def __init__(self):
        '''
        description: 
        param {*}
        return {*}
        '''        
        pass

    #------------------------------------------------ Tools ------------------------------------------------#  
    def _recordSort_Pack(self,list):
        '''
        description: 记录排序前的准备，将元素变成元组，元组中记录了排序前的顺序
        param {*}
        return {*}
        '''        
        tmplst = []
        for i in range(len(list)):
            tup = (list[i], i) # 元组，tup[1]保存排序前的顺序
            tmplst.append(tup)
        return tmplst # 返回以供排序
    
    def _recordSort_Unpack(self,tmplst):
        '''
        description: 对排序后的tmplst进行解析，解析出一个当前排序对应到原来排序的序号
        param {*}
        return {*}
        '''
        sortResults = []        
        records = []
        for e in tmplst:
            sortResults.append(e[0])
            records.append(e[1])
        return (sortResults, records)
    
    
    def _getMaxKeyValues(self, lst, n=1):
        '''
        description: 得到前n个最大的值,有初始序号
        param {*}
        return {*}
        '''
        tmplst = self._recordSort_Pack(lst)
        tmplst.sort(key =lambda tup:tup[0], reverse=True)
        results, records = self._recordSort_Unpack(tmplst)
        
        return tmplst[:n]
    

    #------------------------------------------------ P-Q-R-S-T MARKER ------------------------------------------------# 
    def _R_Marker(self, samples, localMaxRange=10):
        '''
        description: 找R点, 额外筛选条件是局部localMaxRange范围内最大, 选出三个最可能是R的点
        param {*}
        return {*}
        '''       
        waveFilter = WaveFilter()
        samplePoints =  waveFilter._packWithRank(samples) # 打包，将序号信息放在第二位
        samplePoints = waveFilter.filter(samplePoints=samplePoints,key_x=lambda tup:tup[1], key_y=lambda tup:tup[0],mountainShape=True) # 筛选A形点
        samplePoints = waveFilter.filter(samplePoints=samplePoints,key_x=lambda tup:tup[1], key_y=lambda tup:tup[0],localMax=True,localMaxRange=10) # 指定范围筛选局部最大值
        samplePoints.sort(key=lambda tup:tup[0], reverse = True) # 根据y值大小 从大到小进行排序
        samplePoints = samplePoints[0:3] # y最大的前三个最有可能是R点
        samplePoints.sort(key=lambda tup:tup[1]) # 根据x排序

        return samplePoints

    def _Q_Marker(self, samples, R_localMaxRange=10):
        '''
        description: 找Q点，在R点的左边第一个最低的V点
        param {*}
        return {*}
        ''' 
        waveFilter = WaveFilter()
        samplePoints =  waveFilter._packWithRank(samples) # 打包，将序号信息放在第二位

        samplePoints = waveFilter.filter(samplePoints=samplePoints,key_x=lambda tup:tup[1], key_y=lambda tup:tup[0],valleyShape=True) # 筛选V形点
        samplePoints = waveFilter.filter(samplePoints=samplePoints,key_x=lambda tup:tup[1], key_y=lambda tup:tup[0],localMin=True,localMinRange=5) # 保留局部5点范围内的最低点，不然可能会得到R的左边最近的V点而不是Q点
        R_points = self._R_Marker(samples, R_localMaxRange) # 先得到R点 
        samplePoints = waveFilter._getNearestPoints(samplePoints, R_points, key_x=lambda tup:tup[1], leftNearest=True) #得到R点左边最近的V点
        
        return samplePoints

    def _P_Marker(self, samples, R_localMaxRange=10):
        '''
        description: 找P点，在Q点的左边第一个A点
        param {*}
        return {*}
        '''        
        
        waveFilter = WaveFilter()
        samplePoints = waveFilter._packWithRank(samples)

        Q_points = self._Q_Marker(samples, R_localMaxRange) # 先得到Q点
        samplePoints = waveFilter.filter(samplePoints=samplePoints,key_x=lambda tup:tup[1], key_y=lambda tup:tup[0],mountainShape=True) # 筛选A形点
        samplePoints = waveFilter.filter(samplePoints=samplePoints,key_x=lambda tup:tup[1], key_y=lambda tup:tup[0],localMax=True,localMaxRange=15) # 指定范围筛选局部最大值,包括了R及P点
        samplePoints = waveFilter._getNearestPoints(samplePoints,Q_points,key_x=lambda tup:tup[1], leftNearest=True) #得到Q点左边最近的V点

        return samplePoints

    def _S_Marker(self, samples, R_localMaxRange=10):
        '''
        description: 找S点，在R点的右边第一个最低的V点
        param {*}
        return {*}
        '''        
        waveFilter = WaveFilter()
        samplePoints =  waveFilter._packWithRank(samples) # 打包，将序号信息放在第二位

        samplePoints = waveFilter.filter(samplePoints=samplePoints,key_x=lambda tup:tup[1], key_y=lambda tup:tup[0],valleyShape=True) # 筛选V形点
        samplePoints = waveFilter.filter(samplePoints=samplePoints,key_x=lambda tup:tup[1], key_y=lambda tup:tup[0],localMin=True,localMinRange=8) # 保留局部5点范围内的最低点，不然可能会得到R的左边最近的V点而不是Q点
        R_points = self._R_Marker(samples, R_localMaxRange) # 先得到R点
        
        samplePoints = waveFilter._getNearestPoints(samplePoints, R_points, key_x=lambda tup:tup[1], leftNearest=False) #得到R点右边最近的V点
        
        return samplePoints

    def _T_Marker(self, samples, R_localMaxRange=10):
        '''
        description: 找T点，在R点的右边第一个最高的A点
        param {*}
        return {*}
        '''        
        waveFilter = WaveFilter()
        samplePoints = waveFilter._packWithRank(samples)

        S_points = self._S_Marker(samples, R_localMaxRange) # 先得到S点
        # print(S_points)
        samplePoints = waveFilter.filter(samplePoints=samplePoints,key_x=lambda tup:tup[1], key_y=lambda tup:tup[0],mountainShape=True) # 筛选A形点
        samplePoints = waveFilter.filter(samplePoints=samplePoints,key_x=lambda tup:tup[1], key_y=lambda tup:tup[0],localMax=True,localMaxRange=30) # 指定范围筛选局部最大值,包括了R及T点
        # print(samplePoints)
        samplePoints = waveFilter._getNearestPoints(samplePoints,S_points,key_x=lambda tup:tup[1], leftNearest=False) #得到S点右边最近的A点

        return samplePoints

    def mark(self, samples, R=True, Q=True, P=True, S=True, T=True, R_localMaxRange=10):
        '''
        description: 找P-Q-R-S-T点
        param {*}
        return {返回一个字典，保存了所有找到的PQRST点信息}
        '''
        marks = {}        
        if R:
            marks['R'] = self._R_Marker(samples, R_localMaxRange)
        if Q:
            marks['Q'] = self._Q_Marker(samples, R_localMaxRange)
        if P:
            marks['P'] = self._P_Marker(samples, R_localMaxRange)
        if S:
            marks['S'] = self._S_Marker(samples, R_localMaxRange)
        if T:
            marks['T'] = self._T_Marker(samples, R_localMaxRange)
        return marks


def main():
    
    samples = [-73, -70, -70, -70, -68, -70, -70, -65, -64, -62, -62, -62, -61, -57, -54, -53, -53, -51, -48, -44, -42, -41, -38, -35, -35, -33, -31, -29, -26, -25, -27, -25, 
    -22, -18, -21, -24, -24, -24, -22, -22, -26, -32, -33, -34, -34, -36, -41, -45, -47, -49, -50, -51, -53, -55, -57, -59, -58, -61, -63, -66, -68, -65, -65, -63, -62, -67, -71, -71, -73, -69, -69, -66, -70, -71, -68, -69, -69, -70, -70, -70, -69, -66, -68, -70, -72, -70, -68, -66, -64, -65, -64, -65, -64, -63, -65, -69, -70, -66, -64, -61, -61, -60, -64, -65, -65, -61, -58, -61, -64, -65, -65, -62, -62, -62, -65, -62, -62, -63, -62, -64, -66, -64, -63, -63, -63, -68, -68, -65, -62, -61, -64, -64, -66, -66, -67, -64, -64, -66, -68, -69, -67, -64, -66, -65, -64, -65, -65, -63, -63, -64, -67, -67, -65, -64, -66, -68, -70, -66, -67, -65, -62, -68, -71, -67, -64, -61, -62, -63, -64, -70, -63, -64, -64, -64, -64, -64, -62, -62, -63, -63, -62, -59, -56, -56, -58, -59, -59, -57, -55, -48, -44, -43, -43, -35, -29, -28, -30, -37, -42, 
    -43, -43, -41, -42, -43, -47, -51, -50, -50, -48, -51, -54, -55, -60, -60, -65, -64, -65, -63, -61, -61, -63, -64, -71, -70, -70, -67, -64, -65, -68, -70, -65, -61, -62, -65, -72, -71, -72, -71, -72, -74, -54, -17, 27, 77, 138, 189, 204, 178, 121, 69, 23, -11, -28, -37, -47, -48, -50, -54, -60, -63, -68, -74, -76, -81, -79, -77, -75, -73, -75, -79, -83, -84, -81, -78, -82, -80, -82, -78, -79, -78, -79, -83, -85, -84, -79, -78, -80, -81, -81, -79, -77, -77, -77, -80, -81, -81, -80, -78, -77, -80, 
    -83, -81, -78, -75, -74, -77, -80, -77, -74, -72, -73, -73, -75, -76, -71, -68, -68, -67, -69, -67, -64, -63, -66, -63, -66, -63, -60, -55, -51, -48, -51, -49, -47, -44, -42, -42, -43, -41, -37, -34, -30, -28, -29, -28, -23, -24, -25, -23, -26, -24, -24, -25, -23, -26, -25, -25, -26, -28, -32, -34, -38, -39, -38, -36, -39, -45, -47, -48, -47, -47, -48, -54, -55, -56, -55, -55, -56, -60, -62, -62, -61, -59, -59, -62, -64, -61, -60, -59, -63, -63, -64, -61, -61, -59, -62, -61, -60, -61, -60, -62, -59, -59, -59, -58, -57, -56, -55, -55, -57, -58, -55, -56, -54, -57, -59, -59, -55, -54, -53, -53, -54, -53, -54, -52, -52, -53, -57, -57, -55, -52, -53, -56, -57, -56, -53, -53, -53, -53, -53, -54, -54, -51, -53, -56, -58, -56, -54, -54, -53, -53, -59, -56, -57, -53, -53, -56, -57, -57, -55, -55, -55, -55, -57, -57, -54, -53, -54, 
    -55, -57, -56, -53, -53, -55, -54, -55, -55, -55, -52, -53, -55, -57, -56, -56, -52, -54, -55, -56, -56, -54, -51, -45, -47, -49, -48, -44, -42, -43, -44, -45, -47, -46, -44, -38, -36, -37, -30, -23, -21, -20, -25, -30, -31, -30, -32, -35, -37, -40, -38, -38, -36, -39, -42, -45, -44, -45, -48, -48, -52, -58, -57, -56, -53, -55, -59, -61, -59, -58, -55, -57, -59, -61, -64, -61, -59, -60, -61, -61, -59, -57, -58, -62, -68, -74, -73, -58, -30, 13, 59, 108, 168, 217, 233, 208, 153, 96, 44, 3, -16, -23, -37, -47, -49, -47, -48, -52, -60, -69, -70, -73, -70, -73, -75, -78, -75, -74, -74, -75, -77, -78, -79, -80, -78, -78, -80, -80, -78, -77, -77, -77, -79, -82, -80, -78, -77, -79, -79, -81, -81, -78, -76, -76, -79, -80, -82, -78, -77, -75, -77, -79, -79, -78, -76, -77, -78, -79, -77, -75, -73, -73, -74, -74, -73, -70, -68, -69, -69, -72, -70, -64, -61, -58, -60, -58, -59, -56, -51, -47, -49, -49, -47, -45, -41, -36, -36, -38, -34, -31, -29, -28, -30, -28, -29, -27, -22, -26, -25, -26, -27, -24, -24, -24, -29, -33, -34, -35, -35, -38, -43, -45, -47, -50, -49, -53, -54, -59, -63, -61, -59, -60, -63, -65, -65, -65, -65, -66, -68, -71, -72, -70, -67, -71, -72, 
    -73, -73, -69, -70, -72, -72, -71, -70, -69, -67, -69, -73, -75, -73, -70, -71, -69, -70, -70, -71, -69, -66, -65, -66, -70, -70, -70, -68, -68, -70, -71, -69, -67, -66, -68, -68, -70, -68, -65, -65, -64, -68, -71, -72, -71, -69, -66, -67, -69, -69, -70, -66, -66, -69, -69, -70, -68, -69, -69, -69, -70, -69, -69, -67, -71, -72, -73, -73, -72, -70, -71, -71, -71, -70, -69, -68, -71, -74, -76, -76, -75, -73, -72, -71, -71, -73, -73, -69, -68, -72, -77, -76, -72, -69, -69, -73, -75, -77, -71, -70, -70, -72, -74, -74, -71, -70, -70, -73, -73, -72, -67, -65, -66, -65, -66, -63, -61, -62, -64, -65, -64, -62, -56, -53, -49, -48, -46, -46, -45, -44, -47, -50, -53, -55, -51, -52, -51, -54, -60, -63, -63, -64, -65, -67, -71, -73, -73, -76, -78, -80, -79, -76, -75, -77, -83, -84, -84, -85, -83, -81, -82, -85, -86, -82, -79, -80, -84, 
    -85, -87, -90, -91, -93, -90, -82, -53, -5, 41, 92, 143, 195, 219, 202, 151, 92, 38, -10, -37, -45, -50, -56, -65, -70, -71, -70, -73, -77, -85, -89, -89, -91, -90, -91, -96, -99, -97, -95, -94, -94, -96, -101, -100, -98, -96, -99, -100, -98, -98, -95, -93, -95, -95, -97, -98, -96, -95, -93, -95, -98, -95, -93, -95, -97, -97, -97, -95, -94, -93, -95, -95, -96, -94, -95, -92, -92, -93, -97, -95, -94, -91, -93, -91, -92, -92, -91, -87, -87, -86, -87, -87, -83, -82, -80, -79, -82, -80, -76, -71, -71, -75, -71, -69, -64, -61, -58, -58, -56, -55, -51, -47, -47, -47, -49, -48, -42, -39, -36, -38, -39, -38, -37, -35, -34, -36, -37, -35, -38, -38, -39]

    marker = ECGMarker()
    # R_points = marker._R_Marker(samples) # Accurate
    # R_points = marker._Q_Marker(samples) # Accurate
    # R_points = marker._P_Marker(samples) # Accurate
    # R_points = marker._S_Marker(samples) # 较为Accurate
    R_points = marker._T_Marker(samples) # 较为Right,最后一个没有识别出来，原因待分析 # TODO
    print(R_points)
    



if __name__ == '__main__':
    main()