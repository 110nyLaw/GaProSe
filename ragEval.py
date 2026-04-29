#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@author: nylaaa.
Scoring RAG output and human verified output
change current working directory to this file before running
"""

'''
import 
'''
import subprocess
import sys

def install(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

for i in ['torchmetrics', 'pandas', 'numpy']:
    install(i)
    
from   torchmetrics.text.bert import BERTScore
import pandas as pd 
import time
import os
import math
import numpy as np


'''
clean data to prepare for analysis

@PARAMS
    humanFile: file path to human verified cases
    ragFile:   file path to rag output cases
    
@RETURN
    a cleaned version of the human and rag file as a free hand tuple
'''
def cleanData(humanFile, ragFile):
    human = pd.read_csv(humanFile, index_col = False)
    human = human.set_index("file name") #sets index to file name
    human = human.sort_values(by = "file name")
    human = human.fillna(".")

    #rag output cases
    ragged = pd.read_csv(ragFile, index_col = False)
    ragged = ragged.rename(columns = {"Unnamed: 0" : "file name"})

    ragged = ragged.fillna(".") #turns all na to .
    ragged = ragged.set_index("file name")
    ragged = ragged.sort_values(by = "file name")
    
    return human, ragged
    

'''
convert float(nan)s to 0 in place
@PARAMS
    scoredTensor: tensor list object of P,R,F1 values
    length: length of tensor
'''
def nanToZero(scoredTensor, length):
    for i in range(0, length):
        if math.isnan(scoredTensor['precision'][i]):
            scoredTensor['precision'][i] = 0;
        if math.isnan(scoredTensor['recall'][i]):
            scoredTensor['recall'][i] = 0;
        if math.isnan(scoredTensor['f1'][i]):
            scoredTensor['f1'][i] = 0;
            


''' 
evaluates the precision, retrieval, and f1 for each case and 
simultaneously adds to the case by case dataframe called composite

@PARAMS
    human: human verified cases csv of all cases
    ragged: rag output csv of all cases
    
'''
def caseEval(human, ragged):
    bertscore = BERTScore(model_name_or_path = "deepset/bert-base-cased-squad2", num_layers = 12, verbose = False, lang = "en", idf = True)
    global composite
    for i in human.index: #rows, by case
        caseEval = []
        
        #compare across row by case
        ragPred = ragged.loc[[i]].values.flatten().tolist()
        humPred = human.loc[[i]].values.flatten().tolist()
        
        #score full rows
        scorer = bertscore(preds = ragPred, target = humPred)
        nanToZero(scorer, len(humPred))
        
        precision = scorer['precision'].tolist() #tensor to list
        recall = scorer['recall'].tolist()
        f1 = scorer['f1'].tolist()
        
        #convert and store p, r, and f1, still a tensor obj
        prMean = float(str(scorer['precision'].mean().tolist()))
        reMean = float(str(scorer['recall'].mean().tolist()))
        f1Mean = float(str(scorer['f1'].mean().tolist()))
        
        #build case and total sums for p, r, and f1, over each variable
        for x in range(0, len(scorer['precision'])):
            caseEval.append((precision[x], recall[x], f1[x]))
            varTypes[x][1] += precision[x]
            varTypes[x][2] += recall[x]
            varTypes[x][3] += f1[x]
            
        #add the means to end of the dataset
        caseEval.append(["avg", prMean, reMean, f1Mean]) 
        
        #add the full case to the final df
        composite[i] = caseEval




'''
evaluates the precision, retrieval and f1 for the whole system

@PARAMS
    numCases: number of cases to compare
    numVars: number of variables per case

@RETURN
    string representation of list with the [p, r, and f1] of the full model
'''
def systemEval(numCases, numVars):
    overall = [0,0,0] #p, r, and f1
    for i in range(numVars):
        varTypes[i] = varTypes[i][1:4]  
        
        # finds the mean of each variable divided by instances of something happening
        varTypes[i][0] = varTypes[i][0]/numCases
        varTypes[i][1] = varTypes[i][1]/numCases
        varTypes[i][2] = varTypes[i][2]/numCases
        
        #adds the given means to the overall calculation
        overall[0] += varTypes[i][0]
        overall[1] += varTypes[i][1]
        overall[2] += varTypes[i][2]
    
    #finds the mean of the mean of cases for the full system evaluation
    overall[0] = overall[0]/numVars
    overall[1] = overall[1]/numVars
    overall[2] = overall[2]/numVars
    
    #add average to composite data frame
    composite["avg"] = varTypes + [overall]
    return str(overall)



'''
uses current working directory to save transposed data frame locally
saves to current workign directory
'''
def saveLocally():
    global composite
    compositePd = pd.DataFrame(composite).T
    compositePd.index.name = "Location"
    compositePd = compositePd.set_axis(['Case Number', 'Case Name', 'Court', 
                                        'Judicial Officer', 'Date Filed', 'Case Type', 
                                        'Case Status', 'Plaintiff', 'Petitioner', 
                                        'Defendent', 'Serve Date', 'Compensation', 
                                        'Pro Se Filer', 'Mean'], axis = 1)
    compositePd.to_csv(os.getcwd() + '/scoredRagCases.csv', index=True)    
     




'''
running code, print computation time, and saves CSV locally
'''
varTypes = [["Case Number", 0,0,0], ["case name", 0,0,0], ["court", 0,0,0] , ["judicial officer", 0,0,0] , 
            ["file date", 0,0,0], ["case type",0,0,0], ["case status",0,0,0], ["plaintiff", 0,0,0],
            ["petitioner", 0,0,0], ["defendant", 0,0,0], ["Serve date", 0,0,0], ["compensation", 0,0,0], ["Pro se filer", 0,0,0]]

composite = {}
startTime = time.time()
human, ragged = cleanData(os.path.abspath('CSVs/humanVerifiedCases.csv'), os.path.abspath("CSVs/outputRagCases.csv"))
caseEval(human, ragged)
print("Overall P, R, F1: " + systemEval(len(human), len(varTypes)))
compositePd = saveLocally()

print("total time elapsed to compute RAG evaluation: " + str(time.time()-startTime))


