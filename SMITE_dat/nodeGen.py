import torch
import torch.nn as nn
import torch.nn.functional as F
import math
import random
import re
from threading import Thread
import time

from db import db
class nodeGen(object):
    """description of class"""
    def __init__(self):
        self.device=torch.device('cuda' if torch.cuda.is_available() else "cpu")
        self.weights=[]
        self.bias=[]
        self.model=self.makeModel()

        
    def makeTensor(self,queueId:int):
        sql="select matchInfo.ID, matchInfo.GodId, matchInfo.ItemId1, matchInfo.ItemId2, matchInfo.ItemId3, matchInfo.ItemId4, matchInfo.ItemId5, matchInfo.ItemId6, matchInfo.ActiveId1, matchInfo.ActiveId2, matchInfo.ActiveId3, matchInfo.ActiveId4, matchInfo.Win_Status from matchInfo inner join matchIds on matchIds.ID=matchInfo.ID  where matchIds.queueID="+str(queueId)+" order by matchInfo.ID desc;"
        matchInfo=db.get(sql)
        #print(matchInfo[0])

        tenInfoTemp =torch.tensor(matchInfo,device=self.device)
        
        idxs, vals= torch.unique(tenInfoTemp[:,0],return_counts=True)                       #https://twitter.com/jeremyphoward/status/1185062637341593600/photo/1
        matchInfoGroup=torch.empty((1,vals[0],13),device=self.device)

        #matchInfoGroup=torch.cat(torch.split_with_sizes(tenInfoTemp[:,0:len(matchInfo[0])],tuple(vals)),1)
        matchInfoGroupTuple=torch.split_with_sizes(tenInfoTemp[:,0:len(matchInfo[0])],tuple(vals))
        matchInfoGroup=torch.stack(matchInfoGroupTuple)
        return matchInfoGroup.to(self.device)
    def makeModel(self):
        data=self.makeTensor(426)
        
        data=self.expandData(data)

        mid=int(((len(data))/2)*1.5)
        dataTrain=data[:mid]
        dataTest=data[mid:]

        model=Network(self.device)
        model.to(self.device)
        model.train()
        lossFunction = torch.nn.BCELoss()
        optimizer = torch.optim.SGD(model.parameters(), lr=1.5e-3)
        
        
        isWin=dataTrain[:,:, -1:]
        dataTrain=dataTrain.type(torch.FloatTensor)
        isWin=isWin.type(torch.FloatTensor)

     
        blockSize=1
        for i in range(0,dataTrain.size()[0],blockSize):
            block=None
            try:
                #print(f"come on {dataTrain[i:blockSize*(i+1),:,0]} {i} {i+1}")
                blockSize=block+10
                block=dataTrain[i:blockSize*(i+1),:,:]
                print(block)
            except Exception as e:   
                if bool(re.search("CUDA out of memory",str(e))):
                    blockSize=blockSize-10
                    block=dataTrain[i:blockSize*(i+1),:,:]
            block=dataTrain[i:blockSize*(i+1),:,:]
            block=block.to(self.device)       
                        

            if torch.cuda.is_available():
                dataTrain = dataTrain.cuda(non_blocking=True)
            dataTrain, isWin =self.scrambler(isWin,dataTrain)
            isWinePrediction=model(dataTrain)

            isWin= torch.reshape(isWin, isWinePrediction.size())
            
            loss = lossFunction(isWinePrediction, isWin)
   
            optimizer.zero_grad()
   
            loss.backward()
   
            optimizer.step()

            model.forward(dataTrain)
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
    def expandData(self, data):
        mid=int(data.size()[1]/2)
        fact=math.factorial(mid)
        factData=self.expandDataIterate(data,layerMax=mid)
        print("Data expanded")
        return factData

           
                                     
    def expandDataIterate(self,data,layerMax,layer=0):
        layer=layer+1
        factData=None
        if layer<layerMax+1:
            
            for i in range(0,int(data.size()[1]/2)):
                firstVal=data[:,0,:]
                
                data[:,0,:]=data[:,i,:]
                data[:,i,:]=firstVal
                #print(data.size())
                
                if not factData is None:
                    #print(f"{factData.size()}")
                    try:
                        factData= torch.cat((self.expandDataIterate(data,layerMax,layer), factData,), dim=0)
                    except Exception as e:
                       
                       if bool(re.search("CUDA out of memory",str(e))):
                           factData=torch.cat((self.expandDataIterate(data,layerMax,layer).to("cpu"), factData.to("cpu"),), dim=0)
                else:factData= self.expandDataIterate(data,layerMax,layer)
        else:
            #print(f"data {data.size()}")
            out=data.view(torch.int64)
            return out 
        out=factData.view(torch.int64)
        return factData

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
        for i in range(0,40):
            out = self.layerMid(out)
        out = self.outLayer1(out)
        
        return out     
    
    def countParameters(self):
        return sum(p.numel() for p in self.parameters() if p.requires_grad) 
        