from datetime import date
import os
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
import torch.optim as optim

               #Ok lets go with a LSTM RNNs struchure    
from db import db
class nodeGen(object):
    """description of class"""
    def __init__(self):
        self.device=torch.device('cuda' if torch.cuda.is_available() else "cpu") 
        #self.device=torch.device("cpu") 
        self.testCuda()
        self.weights=[]
        self.bias=[]
        self.model=self.loadModel( 'SMITE_LSTM.pth')
        self.model.to(self.device)


        
    def loadModel(self,path):
        # Check if the model file exists
        model_path = 'model_params.pth'
        model=None
        if os.path.exists(model_path):
            # Load the model parameters
            model.load_state_dict(torch.load(model_path))
            print("Model loaded from", model_path)
        else:
            input_size = 120
            hidden_size = 200
            num_layers = 50
            output_size = 10
            model = LSTMModel()
            model = model.to(self.device)
            print("New model created")
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


        
    def analyzeGame(self, data):                                                       #fasd
        dataManager =Dataset(426,self.device)                                        
        indexMax =dataManager.__len__()
        dataT, win =dataManager.__getitem__(dataManager.__len__())                                                     #Gets data
        dataT = dataT[:,:, 0:12]
        learning_rate = 0.001                                                          #Leaning rate basiclay how much change is in the wheights
        criterion = nn.MSELoss()
        optimizer = optim.Adam(self.model.parameters(), lr=learning_rate)
        num_epochs = 100
        print(type(dataT))
        print(dataT.size())
        dataT = dataT.to(self.device)
        print(dataT.size())
        for epoch in range(num_epochs):
            #flattened_dataT = dataT.reshape(dataT.size(0), -1)  # Reshape to [1,120]
            win = win.reshape(win.size(0), -1).to(self.device)  # Reshape to [1, 10]
            #print(flattened_dataT.size())
            # Forward pass
            outputs = self.model(dataT)
            #print(f"output {outputs.size()}, win {win.size()}")
            loss = criterion(outputs, win)

            # Backward pass and optimization
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

            # Print loss every 10 epochs
            if (epoch+1) % 10 == 0:
                print(f'Epoch [{epoch+1}/{num_epochs}], Loss: {loss.item():.4f}')
        
    

    def testCuda(self):
        print(torch.cuda.is_available())
        print(torch.cuda.device_count())
        print(torch.cuda.current_device())
        print(torch.cuda.device(0))
        print(torch.cuda.get_device_name(0))

class LSTMModel(nn.Module):
    def __init__(self):
        super(LSTMModel, self).__init__()
        
        # Hard-coded values
        input_size = 12
        hidden_size = 10
        num_layers = 50
        output_size = 1
        
        self.lstm = nn.LSTM(input_size, hidden_size, num_layers, batch_first=True)
        self.fc = nn.Linear(hidden_size, output_size)
        self.sigmoid = nn.Sigmoid()

    def forward(self, x):
        # LSTM output
        
        out, _ = self.lstm(x)
        #print(out.shape)
        
        # Fully connected layer
        out = self.fc(out)
        
        # Sigmoid activation
        out = self.sigmoid(out)
        
        # Flatten the output
        out = out.squeeze(-1)
        
        return out

class Dataset(data.Dataset):
    def __init__(self, queueId:int,device):
        self.queueId=queueId
        self.device=device
        self.limit= False
        sql="SELECT ID FROM matchIds WHERE queueID="+str(self.queueId)+" ORDER BY ID DESC LIMIT 1;"
        self.startI=db.get(sql)[0][0]

    def makeTensor(self,queueId:int,index:int):
        col = """
            matchInfo.ID, matchInfo.GodId, matchInfo.ItemId1, matchInfo.ItemId2, 
            matchInfo.ItemId3, matchInfo.ItemId4, matchInfo.ItemId5, matchInfo.ItemId6, 
            matchInfo.ActiveId1, matchInfo.ActiveId2, matchInfo.ActiveId3, matchInfo.ActiveId4, 
            matchInfo.Win_Status
            """
        sql = f"""
            SELECT {col}
            FROM matchInfo
            INNER JOIN matchIds ON matchIds.ID = matchInfo.ID
            WHERE matchIds.queueID = {queueId}
            AND matchInfo.ID IN (
                SELECT matchInfo.ID
                FROM matchInfo
                GROUP BY matchInfo.ID
                HAVING COUNT(*) = 10
            )
            ORDER BY matchInfo.ID DESC
            LIMIT {index * 10};
            """
        matchInfo=db.get(sql)
        print(sql)
        #print(matchInfo)
        
        #self.startI=matchInfo[-1,0]
        tenInfoTemp =torch.tensor(matchInfo,device=self.device)
        #print(tenInfoTemp) 
        #print(tenInfoTemp.size())
        idxs, vals= torch.unique(tenInfoTemp[:,0],return_counts=True)                       #https://twitter.com/jeremyphoward/status/1185062637341593600/photo/1
        matchInfoGroup=torch.empty((1,vals[0],13),device=self.device)
        
        #matchInfoGroup=torch.cat(torch.split_with_sizes(tenInfoTemp[:,0:len(matchInfo[0])],tuple(vals)),1)
        matchInfoGroupTuple=torch.split_with_sizes(tenInfoTemp[:,0:len(matchInfo[0])],tuple(vals))
        matchInfoGroup=torch.stack(matchInfoGroupTuple)                                                         # Their can be bad data here when players leave the match or a bot takes their place
        #time.sleep(10)
        return matchInfoGroup.to(self.device)
    
    def __len__(self):
        sql="SELECT COUNT(ID) FROM matchIds WHERE queueID="+str(self.queueId)+";"
        
        out= db.get(sql)
        return int(out[0][0])

    def __getitem__(self, index:int):
        data=self.makeTensor(self.queueId,index)
        data = self.flipData(data)                                                              #Flips data randomly as I can and returns it
        #data=self.expandData(dataRaw)
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
    #This class basicaly flips data based off the data in the tensor and it also flips data based off a random number.
    #This should stop the AI from breaking the random number ganrators agrithom by also mixing in some data that is case sensitve to each entray kinda like a key.
    #I should also flip data based off time but we will see how it goes
    def flipData(self, tensor):
        # Sum values in the first half of the second dimension
        first_half_sum = torch.sum(tensor[:, :5, :], dim=(1,2))

        # Sum values in the second half of the second dimension
        second_half_sum = torch.sum(tensor[:, 5:, :], dim=(1,2))

        print(tensor.shape)
        print(first_half_sum.shape)  # Should print torch.Size([n])
        print(second_half_sum.shape)  # Should print torch.Size([n])
        print(first_half_sum)
        print(second_half_sum)
        are_equal = torch.equal(first_half_sum, second_half_sum)
        print(f"Both halves are equal: {are_equal}")
        # Check if the sum is odd or even
        is_odd = (first_half_sum + second_half_sum) % 2 == 1
        print(is_odd)
        # Based on the result, flip the order of the first and second halves
        flipped_tensor = torch.where(is_odd.view(-1, 1, 1), 
                                     torch.cat((tensor[:, 5:, :], tensor[:, :5, :]), dim=1), 
                                     tensor)
        
        random_binary = torch.randint(0, 2, (tensor.size(0),)).bool().to(self.device)                    #A buntch or random number to scramble the data
        final_tensor = torch.where(random_binary[:, None, None], 
                               torch.cat((flipped_tensor[:, 5:, :], flipped_tensor[:, :5, :]), dim=1), 
                               flipped_tensor)

        return final_tensor

'''

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
'''