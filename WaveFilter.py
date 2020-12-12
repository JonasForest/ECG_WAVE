'''
Author: JFor
Date: 2020-11-24 09:39:50
LastEditors: JFor
LastEditTime: 2020-11-25 15:13:28
Description: 波形采样点集合的过滤类
'''
import math

class WaveFilter():
    '''
    description: 波形采样点集合的过滤类
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
    
    #---------------------------------------------- Tools ----------------------------------------------#
    def _packWithRank(self,list):
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
    
    def _unpackWithRank(self,tmplst):
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

    def _deflectionAngle(self, p1, p2, p3, key_x=lambda tup:tup[0],key_y=lambda tup:tup[1]):
        '''
        description: 直线p1-p2顺时针旋转到p3-p2的偏转量，假定横坐标间隔为1，p1,p2,p3是连续的三个点，默认x=p[0],y=p[1]
        param {传入的点p1,p2,p3可以是元组，可以是列表等等格式，坐标值取决于后面的lambda表达式}
        return {
            返回正表示偏转超过180，呈A
            返回负值表示偏转小于180，呈V
            返回0表示偏转等于180，呈——，
            绝对值越大，变化越剧烈，形成的角越尖，
            }
        '''
        p1_x, p1_y = key_x(p1), key_y(p1)
        p2_x, p2_y = key_x(p2), key_y(p2)
        p3_x, p3_y = key_x(p3), key_y(p3)

        k12 = (p2_y-p1_y)/(p2_x-p1_x)
        k23 = (p3_y-p2_y)/(p3_x-p2_x)
        delta = k12-k23
        return delta

    def _isMountainShape(self, p1, p2, p3, key_x=lambda tup:tup[0],key_y=lambda tup:tup[1]):
        '''
        description: 判断p2点是否是A形点,默认x=p[0],y=p[1]
        param {*}
        return {*}
        '''        
        if self._deflectionAngle(p1,p2,p3,key_x,key_y) > 0:
            return True
        return False

    def _isValleyShape(self, p1, p2, p3, key_x=lambda tup:tup[0],key_y=lambda tup:tup[1]):
        '''
        description: 判断p2点是否是V形点,默认x=p[0],y=p[1]
        param {*}
        return {*}
        '''        
        if self._deflectionAngle(p1,p2,p3,key_x,key_y) < 0:
            return True
        return False

    def _dividePointsByRange(self, sourcePoints, leftPoint, rightPoint, key_x=lambda tup:tup[0]):
        '''
        description: 将一些按x顺序排列的点根据左右点leftPoint，rightPoint进行截取中间的所有点，如果端点相同不包括端点
        param {*}
        return {如果leftPint不在rightPint左边，或者两者间已经没有其他元素了，直接返回None}
        '''
        results = None

        if key_x(rightPoint) - key_x(leftPoint) <=1:
            return None

        left = 0
        right = len(sourcePoints)
        for i in range(len(sourcePoints)):
            if key_x(sourcePoints[i]) > key_x(leftPoint): #
                left = i
                break
        
        for i in range(len(sourcePoints), 0, -1):
            if key_x(sourcePoints[i-1]) < key_x(rightPoint): #
                right = i-1
                break
                
        if right-left <=1:
            return None
            
        results = sourcePoints[left:right+1]
        return results
                

    #------------------------------------------ Filter Modules ------------------------------------------#
    def _getMountainShapePoints(self, samplePoints, key_x=lambda tup:tup[0],key_y=lambda tup:tup[1]):
        '''
        description: 从samples中得到所有A形点,默认x=p[0],y=p[1]
        param {*}
        return {*}
        '''        
        results = []

        for i in range(len(samplePoints)-2):
            p1,p2,p3 = samplePoints[i], samplePoints[i+1], samplePoints[i+2] # 选取三点
            if self._isMountainShape(p1,p2,p3,key_x,key_y):
                results.append(p2)
                
        return results

    def _getValleyShapePoints(self, samplePoints, key_x=lambda tup:tup[0],key_y=lambda tup:tup[1]):
        '''
        description: 从samples中得到所有A形点,默认x=p[0],y=p[1]
        param {*}
        return {*}
        '''        
        results = []

        for i in range(len(samplePoints)-2):
            p1,p2,p3 = samplePoints[i], samplePoints[i+1], samplePoints[i+2] # 选取三点
            if self._isValleyShape(p1,p2,p3,key_x,key_y):
                results.append(p2)

        return results

    def _getLocalMaxPoints(self,samplePoints, key_x=lambda tup:tup[0],key_y=lambda tup:tup[1], localMaxRange=10):
        '''
        description: 保留x局部localMaxRange个范围内y最大的点
        param {*}
        return {*}
        '''        
        results = []

        # lastMaxPoint = None      
        # for i in range(len(samplePoints)-localMaxRange):
        #     nowMaxPoint = max(samplePoints[i:i+localMaxRange], key=key_y) # 选出从第i个到第i+localMaxRange个范围内的y最大的点
        #     if nowMaxPoint > lastMaxPoint and key_x(nowMaxPoint)-key_x(lastMaxPoint)>=localMaxRange:
        #         results.append(nowMaxPoint)
        #         lastMaxPoint = nowMaxPoint
        
        lastMaxPoint = samplePoints[0]
        for i in range(math.ceil(len(samplePoints)/localMaxRange)):

            if i == math.ceil(len(samplePoints)/localMaxRange)-1: # 到最后一组了
                # print(samplePoints[(i*localMaxRange):len(samplePoints)]) # TODO
                localMaxPoint = max(samplePoints[(i*localMaxRange):len(samplePoints)], key=key_y)
            else:
                # print(samplePoints[(i*localMaxRange):((i+1)*localMaxRange)])
                localMaxPoint = max(samplePoints[(i*localMaxRange):((i+1)*localMaxRange)], key=key_y) # TODO   # FIXED max为空，因为原来是max(samplePoints[(i*localMaxRange):(i+1)*localMaxRange], key=key_y)

            if (key_x(localMaxPoint)-key_x(lastMaxPoint)) < localMaxRange: # 如果在这一组的最小值点比上一组的最小值点相距不足localMaxRange
                if key_y(localMaxPoint) >= key_y(lastMaxPoint): # 如果这一组的最小值点的y值比上一组的最小值点的y值大
                    lastMaxPoint = localMaxPoint
            else: # 如果在这一组的最小值点比lastMaxPoint相距已经超过localMaxRange,则lastMaxPoint已经符合要求了
                results.append(lastMaxPoint)
                lastMaxPoint = localMaxPoint
                    
        return results

    def _getLocalMinPoints(self,samplePoints, key_x=lambda tup:tup[0],key_y=lambda tup:tup[1], localMaxRange=10):
        '''
        description: 保留x局部localMaxRange个范围内y最大的点
        param {*}
        return {*}
        '''        
        results = []
        
        lastMinPoint = samplePoints[0]
        for i in range(math.ceil(len(samplePoints)/localMaxRange)):
            if i == math.ceil(len(samplePoints)/localMaxRange)-1: # 到最后一组了 # FIXED ,最后一组samplePoints[(i*localMaxRange):len(samplePoints)为空
                localMinPoint = min(samplePoints[(i*localMaxRange):len(samplePoints)], key=key_y)
            else:
                # print(i)
                # print(localMaxRange)
                # print(len(samplePoints))
                # print(samplePoints[(i*localMaxRange):((i+1)*localMaxRange)])
                localMinPoint = min(samplePoints[(i*localMaxRange):((i+1)*localMaxRange)], key=key_y)   # TODO TODO TODO

            if (key_x(localMinPoint)-key_x(lastMinPoint)) < localMaxRange: # 如果在这一组的最小值点比上一组的最小值点相距不足localMaxRange
                if key_y(localMinPoint) <= key_y(lastMinPoint): # 如果这一组的最小值点的y值比上一组的最小值点的y值大
                    lastMinPoint = localMinPoint
            else: # 如果在这一组的最小值点比lastMinPoint相距已经超过localMaxRange,则lastMinPoint已经符合要求了
                results.append(lastMinPoint)
                lastMinPoint = localMinPoint
                    
        return results

    def _getNearestPoints(self, sourcePoints, targetPoints, key_x=lambda tup:tup[0],key_y=lambda tup:tup[1], leftNearest=True):
        '''
        description: 从sourcePoints中得到距targetPoints中点最近的一些点,默认是目标点的左边最近的点
        param {*}
        return {*}
        '''        
        results = []
        
        if leftNearest:
            leftPoint = sourcePoints[0]
            for targetPoint in targetPoints:
                if targetPoint == None: # 如果传入的targetPoint就是None,则此点对应的目标点也认为是None了
                    results.append(None)
                    continue

                points = self._dividePointsByRange(sourcePoints, leftPoint, targetPoint, key_x) # 得到点targetPoint左边到leftPoint之间的一段点
                
                if points == None:
                    results.append(None)
                else:
                    results.append(points[-1]) # pints的最右一个点就是离targetPoint最近的左边的点
                leftPoint = targetPoint
        else:
            rightPoint = sourcePoints[-1]
            for i in range(len(targetPoints), 0, -1):
                targetPoint = targetPoints[i-1]
                if targetPoint == None: # 如果传入的targetPoint就是None,则此点对应的目标点也认为是None了
                    results.append(None)
                    continue
                    
                points = self._dividePointsByRange(sourcePoints, targetPoint, rightPoint, key_x) # 得到点targetPoint左边到leftPoint之间的一段点
                if points == None:
                    results.append(None)
                else:
                    results.append(points[0]) # pints的最左一个点就是离targetPoint最近的右边的点
                rightPoint = targetPoint
            results.reverse()
        
        return results

    #---------------------------------------------- Filter ----------------------------------------------#
    def filter(self,samplePoints, key_x=lambda tup:tup[0],key_y=lambda tup:tup[1], mountainShape=False, valleyShape=False, localMax=False, localMaxRange=10, localMin=False, localMinRange=10):
        '''
        description: 筛选函数，可以组合添加各种筛选条件.,默认x=p[0],y=p[1].
        param {
            samplePoints: 连续的采样点集合
            mountainShape: 标志，筛选A形点
            valleyShape: 标志，筛选V形点
            localMax: 标志，附加条件，每个筛选点局部范围localMaxRange内最大
            }
        return { 一次只能使用一个过滤模组,同时使用多个只会返回第一个过滤模组的结果,一个都不使用则返回None}
        '''        
        results = []

        if mountainShape:
            results = self._getMountainShapePoints(samplePoints,key_x,key_y)
            return results

        if valleyShape:
            results = self._getValleyShapePoints(samplePoints,key_x,key_y)
            return results
            
        if localMax:
            results = self._getLocalMaxPoints(samplePoints,key_x,key_y,localMaxRange)
            return results
        
        if localMin:
            results = self._getLocalMinPoints(samplePoints,key_x,key_y,localMinRange)
            return results

        return results


def main():
   
    samples = [-73, -70, -70, -70, -68, -70, -70, -65, -64, -62, -62, -62, -61, -57, -54, -53, -53, -51, -48, -44, -42, -41, -38, -35, -35, -33, -31, -29, -26, -25, -27, -25, 
    -22, -18, -21, -24, -24, -24, -22, -22, -26, -32, -33, -34, -34, -36, -41, -45, -47, -49, -50, -51, -53, -55, -57, -59, -58, -61, -63, -66, -68, -65, -65, -63, -62, -67, -71, -71, -73, -69, -69, -66, -70, -71, -68, -69, -69, -70, -70, -70, -69, -66, -68, -70, -72, -70, -68, -66, -64, -65, -64, -65, -64, -63, -65, -69, -70, -66, -64, -61, -61, -60, -64, -65, -65, -61, -58, -61, -64, -65, -65, -62, -62, -62, -65, -62, -62, -63, -62, -64, -66, -64, -63, -63, -63, -68, -68, -65, -62, -61, -64, -64, -66, -66, -67, -64, -64, -66, -68, -69, -67, -64, -66, -65, -64, -65, -65, -63, -63, -64, -67, -67, -65, -64, -66, -68, -70, -66, -67, -65, -62, -68, -71, -67, -64, -61, -62, -63, -64, -70, -63, -64, -64, -64, -64, -64, -62, -62, -63, -63, -62, -59, -56, -56, -58, -59, -59, -57, -55, -48, -44, -43, -43, -35, -29, -28, -30, -37, -42, 
    -43, -43, -41, -42, -43, -47, -51, -50, -50, -48, -51, -54, -55, -60, -60, -65, -64, -65, -63, -61, -61, -63, -64, -71, -70, -70, -67, -64, -65, -68, -70, -65, -61, -62, -65, -72, -71, -72, -71, -72, -74, -54, -17, 27, 77, 138, 189, 204, 178, 121, 69, 23, -11, -28, -37, -47, -48, -50, -54, -60, -63, -68, -74, -76, -81, -79, -77, -75, -73, -75, -79, -83, -84, -81, -78, -82, -80, -82, -78, -79, -78, -79, -83, -85, -84, -79, -78, -80, -81, -81, -79, -77, -77, -77, -80, -81, -81, -80, -78, -77, -80, 
    -83, -81, -78, -75, -74, -77, -80, -77, -74, -72, -73, -73, -75, -76, -71, -68, -68, -67, -69, -67, -64, -63, -66, -63, -66, -63, -60, -55, -51, -48, -51, -49, -47, -44, -42, -42, -43, -41, -37, -34, -30, -28, -29, -28, -23, -24, -25, -23, -26, -24, -24, -25, -23, -26, -25, -25, -26, -28, -32, -34, -38, -39, -38, -36, -39, -45, -47, -48, -47, -47, -48, -54, -55, -56, -55, -55, -56, -60, -62, -62, -61, -59, -59, -62, -64, -61, -60, -59, -63, -63, -64, -61, -61, -59, -62, -61, -60, -61, -60, -62, -59, -59, -59, -58, -57, -56, -55, -55, -57, -58, -55, -56, -54, -57, -59, -59, -55, -54, -53, -53, -54, -53, -54, -52, -52, -53, -57, -57, -55, -52, -53, -56, -57, -56, -53, -53, -53, -53, -53, -54, -54, -51, -53, -56, -58, -56, -54, -54, -53, -53, -59, -56, -57, -53, -53, -56, -57, -57, -55, -55, -55, -55, -57, -57, -54, -53, -54, 
    -55, -57, -56, -53, -53, -55, -54, -55, -55, -55, -52, -53, -55, -57, -56, -56, -52, -54, -55, -56, -56, -54, -51, -45, -47, -49, -48, -44, -42, -43, -44, -45, -47, -46, -44, -38, -36, -37, -30, -23, -21, -20, -25, -30, -31, -30, -32, -35, -37, -40, -38, -38, -36, -39, -42, -45, -44, -45, -48, -48, -52, -58, -57, -56, -53, -55, -59, -61, -59, -58, -55, -57, -59, -61, -64, -61, -59, -60, -61, -61, -59, -57, -58, -62, -68, -74, -73, -58, -30, 13, 59, 108, 168, 217, 233, 208, 153, 96, 44, 3, -16, -23, -37, -47, -49, -47, -48, -52, -60, -69, -70, -73, -70, -73, -75, -78, -75, -74, -74, -75, -77, -78, -79, -80, -78, -78, -80, -80, -78, -77, -77, -77, -79, -82, -80, -78, -77, -79, -79, -81, -81, -78, -76, -76, -79, -80, -82, -78, -77, -75, -77, -79, -79, -78, -76, -77, -78, -79, -77, -75, -73, -73, -74, -74, -73, -70, -68, -69, -69, -72, -70, -64, -61, -58, -60, -58, -59, -56, -51, -47, -49, -49, -47, -45, -41, -36, -36, -38, -34, -31, -29, -28, -30, -28, -29, -27, -22, -26, -25, -26, -27, -24, -24, -24, -29, -33, -34, -35, -35, -38, -43, -45, -47, -50, -49, -53, -54, -59, -63, -61, -59, -60, -63, -65, -65, -65, -65, -66, -68, -71, -72, -70, -67, -71, -72, 
    -73, -73, -69, -70, -72, -72, -71, -70, -69, -67, -69, -73, -75, -73, -70, -71, -69, -70, -70, -71, -69, -66, -65, -66, -70, -70, -70, -68, -68, -70, -71, -69, -67, -66, -68, -68, -70, -68, -65, -65, -64, -68, -71, -72, -71, -69, -66, -67, -69, -69, -70, -66, -66, -69, -69, -70, -68, -69, -69, -69, -70, -69, -69, -67, -71, -72, -73, -73, -72, -70, -71, -71, -71, -70, -69, -68, -71, -74, -76, -76, -75, -73, -72, -71, -71, -73, -73, -69, -68, -72, -77, -76, -72, -69, -69, -73, -75, -77, -71, -70, -70, -72, -74, -74, -71, -70, -70, -73, -73, -72, -67, -65, -66, -65, -66, -63, -61, -62, -64, -65, -64, -62, -56, -53, -49, -48, -46, -46, -45, -44, -47, -50, -53, -55, -51, -52, -51, -54, -60, -63, -63, -64, -65, -67, -71, -73, -73, -76, -78, -80, -79, -76, -75, -77, -83, -84, -84, -85, -83, -81, -82, -85, -86, -82, -79, -80, -84, 
    -85, -87, -90, -91, -93, -90, -82, -53, -5, 41, 92, 143, 195, 219, 202, 151, 92, 38, -10, -37, -45, -50, -56, -65, -70, -71, -70, -73, -77, -85, -89, -89, -91, -90, -91, -96, -99, -97, -95, -94, -94, -96, -101, -100, -98, -96, -99, -100, -98, -98, -95, -93, -95, -95, -97, -98, -96, -95, -93, -95, -98, -95, -93, -95, -97, -97, -97, -95, -94, -93, -95, -95, -96, -94, -95, -92, -92, -93, -97, -95, -94, -91, -93, -91, -92, -92, -91, -87, -87, -86, -87, -87, -83, -82, -80, -79, -82, -80, -76, -71, -71, -75, -71, -69, -64, -61, -58, -58, -56, -55, -51, -47, -47, -47, -49, -48, -42, -39, -36, -38, -39, -38, -37, -35, -34, -36, -37, -35, -38, -38, -39]
    

    waveFilter = WaveFilter()
    samplePoints =  waveFilter._packWithRank(samples) # 打包，将序号信息放在第二位
    # samplePoints = waveFilter.filter(samplePoints=samplePoints,key_x=lambda tup:tup[1], key_y=lambda tup:tup[0],mountainShape=True) # 筛选A形点
    # samplePoints = waveFilter.filter(samplePoints=samplePoints,key_x=lambda tup:tup[1], key_y=lambda tup:tup[0],localMax=True,localMaxRange=10) # 指定范围筛选局部最大值
    # samplePoints.sort(key=lambda tup:tup[0], reverse = True) # 根据y值大小 从大到小进行排序
    samplePoints = waveFilter.filter(samplePoints=samplePoints,key_x=lambda tup:tup[1], key_y=lambda tup:tup[0],valleyShape=True) # 筛选V形点
    samplePoints = waveFilter.filter(samplePoints=samplePoints,key_x=lambda tup:tup[1], key_y=lambda tup:tup[0],localMin=True,localMinRange=10) # 指定范围筛选局部最大值
    samplePoints.sort(key=lambda tup:tup[0], reverse = False) # 根据y值大小 从大到小进行排序
    print(samplePoints)

if __name__ == '__main__':
    main()
