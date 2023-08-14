import torch
import torch.nn as nn
import torch.nn.functional as F
import pandas as pd
import math
import random
import re
import time
from db import db
from threading import Thread
from torch.utils import data


from db import db
class nodeGen(object):
    """description of class"""
    def __init__(self):
        self.device=torch.device('cuda' if torch.cuda.is_available() else "cpu")
        self.weights=[]
        self.bias=[]
        self.model=self.makeModel()

        

    def makeModel(self):
        data=Dataset(426,self.device)
        model=Network(self.device)
        model.to(self.device)
        model.train()
        lossFunction = torch.nn.BCELoss()
        optimizer = torch.optim.SGD(model.parameters(), lr=1.5e-3)
     
        blockSize=1
        for i in range(0,data.__len__(),blockSize):
            block=None
            isWin=None
            try:
                #print(f"come on {dataTrain[i:blockSize*(i+1),:,0]} {i} {i+1}")
                blockSize=blockSize+1
                block=data.__getitem__(blockSize)
                print(block[0][0])
            except Exception as e:   
                if bool(re.search("CUDA out of memory",str(e))):
                    blockSize=blockSize-10
                    block=data.__getitem__(blockSize)
                    print(block)
                else:
                    print(e)

            if torch.cuda.is_available() and self.device is torch.device('cuda'):
                block = block.cuda(non_blocking=True)
            
            isWinePrediction=model(block)

            isWin= torch.reshape(isWin, isWinePrediction.size())
            
            loss = lossFunction(isWinePrediction, isWin)
   
            optimizer.zero_grad()
   
            loss.backward()
   
            optimizer.step()

            model.forward(block)
            if(i%100000==0):
                acc=self.findAccuracy(isWinePrediction,dataTrain,.4999)
                print(f" {dataTrain[0][0]}")
                print("\n")
                print(f"{isWin[0]}")
                print(f"{isWinePrediction[0]}")
                print(f"win: {acc[0]} lose: {acc[1]}")
        dataTest=dataTest.type(torch.FloatTensor).to(self.device)
        model.train(mode=False)
        isWinePrediction= model(dataTest)

        accuracy=self.findAccuracy(isWinePrediction,dataTest,.10)
        print(f"Finle: Win {accuracy[0]} lose {accuracy[0]}")
        
        return model
    def findAccuracy(self,isWinPrediction,data,devashion):
        isWin=data[:,:, -1:]
        isWin=isWin.type(torch.FloatTensor).to(self.device)
        isWin= torch.reshape(isWin, isWinPrediction.size())
        test1=torch.where(isWinPrediction > isWin-devashion,1,0)
        test2=torch.where(isWinPrediction < isWin+devashion,1,0)
        isCondishions=torch.where(test1==test2,1,0).type(torch.FloatTensor)
        mid=int((len(data))/2)
        isConWin=isCondishions[:mid]
        isConLose=isCondishions[mid:]

        winAvg=torch.mean(isConWin)
        loseAvg=torch.mean(isConLose)
        out = (winAvg,loseAvg)
        return out

    def scrambler(self, winLose,data):
        if(bool(random.randint(0,1))):
            winLose= torch.flip(winLose,dims=[1])
            data=torch.flip(data,dims=[1])
        return data,winLose
        
    def analyzeGame(self, data):
        dataT =torch.tensor(data,device=self.device)
        dataT =torch.unsqueeze(dataT, dim=0)
        dataT=dataT.type(torch.FloatTensor).to(self.device)
        winLose=self.model(dataT)
        winLoseList=winLose.tolist()[0]
        return winLoseList
    def testCuda(self):
        print(torch.cuda.is_available())
        print(torch.cuda.device_count())
        print(torch.cuda.current_device())
        print(torch.cuda.device(0))
        print(torch.cuda.get_device_name(0))

class Network(nn.Module):
    def __init__(self, device=torch.device("cpu"), hiddenNodes=120):
        size1=12
        self.device=device
        super(Network, self).__init__()
        self.layer1=nn.Sequential(
            nn.Linear(117, hiddenNodes),
            nn.Sigmoid()
            ).to(device)
        self.layerMid=nn.Sequential(
            nn.Linear(hiddenNodes, hiddenNodes),
            nn.Sigmoid()
            ).to(device)
        self.outLayer1=nn.Sequential(
            nn.Linear(hiddenNodes,10),
            nn.Sigmoid()
            ).to(device)
       # self.base=nn.Sequential(
        #F.relu(nn.Linear(10, size1)),
        #F.relu(nn.Linear(size1 , size1)),
        #nn.Linear(size1, 2),
        #    )

    def forward(self, x):
        x=x[:,:-1]
        out=x.reshape(x.size(0), -1).to(self.device)
        
        out = self.layer1(out)
        for i in range(0,20):
            out = self.layerMid(out)
        out = self.outLayer1(out)
        return out   
    def countParameters(self):
        return sum(p.numel() for p in self.parameters() if p.requires_grad) 
    




class Dataset(data.Dataset):
    def __init__(self, queueId:int,device):
        self.queueId=queueId
        self.device=device
        self.limit= False
        sql="SELECT ID FROM matchIds WHERE queueID="+str(self.queueId)+" ORDER BY ID DESC LIMIT 1;"
        self.startI=db.get(sql)[0][0]

    def makeTensor(self,queueId:int,index:int):
        print("test2")
        col="matchInfo.ID, matchInfo.GodId, matchInfo.ItemId1, matchInfo.ItemId2, matchInfo.ItemId3, matchInfo.ItemId4, matchInfo.ItemId5, matchInfo.ItemId6, matchInfo.ActiveId1, matchInfo.ActiveId2, matchInfo.ActiveId3, matchInfo.ActiveId4, matchInfo.Win_Status from matchInfo inner join matchIds on matchIds.ID=matchInfo.ID"
        sql="SELECT "+col+" WHERE matchIds.queueID="+str(self.queueId)+" and matchIds.queueID < "+str(self.startI-1)+" ORDER BY matchInfo.ID desc limit "+str(index*10)+";"
        matchInfo=db.get(sql)
        #print(sql)
        print(matchInfo)
        
        #self.startI=matchInfo[-1,0]
        
        
        tenInfoTemp =torch.tensor(matchInfo,device=self.device)
         
        
        idxs, vals= torch.unique(tenInfoTemp[:,0],return_counts=True)                       #https://twitter.com/jeremyphoward/status/1185062637341593600/photo/1
        matchInfoGroup=torch.empty((1,vals[0],13),device=self.device)
        

        #matchInfoGroup=torch.cat(torch.split_with_sizes(tenInfoTemp[:,0:len(matchInfo[0])],tuple(vals)),1)
        matchInfoGroupTuple=torch.split_with_sizes(tenInfoTemp[:,0:len(matchInfo[0])],tuple(vals))
        matchInfoGroup=torch.stack(matchInfoGroupTuple)
        time.sleep(10)
        return matchInfoGroup.to(self.device)
    def __len__(self):
        sql="SELECT COUNT(ID) FROM matchIds WHERE queueID="+str(self.queueId)+";"
        
        out= db.get(sql)
        return int(out[0][0])

    def __getitem__(self, index:int):
        dataRaw=self.makeTensor(self.queueId,index)
        
        data=self.expandData(dataRaw)
        isWin=data[:,:, -1:]
        data=data.type(torch.FloatTensor)
        isWin=isWin.type(torch.FloatTensor)
        data=data.to(self.device)
        isWin=isWin.to(self.device)
        return data, isWin
    def expandData(self, data):
        mid=int(data.size()[1]/2)
        fact=math.factorial(mid)
        factData=self.expandDataPermutation(data,layerMax=mid)                                  #Expand matchs by finding all the permutations of the data. In math turms x = data and y = data expanded Ex: x*5!=y  
        factData=torch.flip(factData,dims=[1])                                                  #Flips the expanded data (factData)
        factData=self.expandDataPermutation(factData,layerMax=mid)                              #Now that the data has been fliped it finds all the permutations of the other team. In math turms x = factData and y = data expanded Ex: x*5!=y
        factData=torch.flip(factData,dims=[1])                                                  #Fliped data back
        print("Data expanded")
        return factData                                                                         #data is returned (x*5!)^2=len(data) larger. Note this will be very high in ram usage and should be replaced in a update to the AI modual.
    
    def expandDataPermutation(self,data,layerMax,layer=0):
        layer=layer+1
        factData=None
        if layer<layerMax+1:
            for i in range(0,int(data.size()[1]/2)):
                firstVal=data[:,0,:]
                data[:,0,:]=data[:,i,:]
                data[:,i,:]=firstVal
                if not factData is None:
                    factData= torch.cat((self.expandDataPermutation(data,layerMax,layer), factData,), dim=0)
                else:
                    factData= self.expandDataPermutation(data,layerMax,layer)
        else:
            out=data.view(torch.int64)
            return out 
        out=factData.view(torch.int64)
        return factData

    def getGPURam(self):
        t = torch.cuda.get_device_properties(0).total_memory
        r = torch.cuda.memory_reserved(0)
        a = torch.cuda.memory_allocated(0)
        f = r-a
        return f