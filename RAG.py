#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@author: Nyla Lawrence
compute rag output of baseline questions for given html case documents
"""


'''
load packages
'''
import subprocess
import sys

def install(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

for i in ['transformers', 'pandas', 'torch']:
    install(i)


from transformers import AutoTokenizer, AutoModelForQuestionAnswering
import pandas as pd
import torch
import time
import os

'''
set up model and initialize variables
'''
startTime = time.time()

# https://huggingface.co/deepset/bert-base-cased-squad2
# encoder only transformer
tokenizer = AutoTokenizer.from_pretrained("deepset/bert-base-cased-squad2")#'nlpaueb/legal-bert-base-uncased') #identify what type of tokenizer it is 
model = AutoModelForQuestionAnswering.from_pretrained("deepset/bert-base-cased-squad2")#'nlpaueb/legal-bert-base-uncased')

model.eval()
torch.set_grad_enabled(False) #turns gradient off, no training 

dfRagHtml = pd.read_csv(os.path.abspath('LocalHTMLcases.csv')) 

questions = [
    "What is the case number?", 
    "What is the case name?", 
    "Which court is the case filed under?",
    "Who is the judicial officer of the case?",
    "When was the case filed?",
    "What is the case type?",
    "What is the status of the case?",
    "Who is the plaintiff?",
    "Who is the petitioner?",
    "Who is the defendant?",
    "When was a party served?",
    "How much was compensation?",
    "Who is the pro se filer?"]
dfRagResult = {}



'''
loop over all cases in dataset
'''
for i in range(len(dfRagHtml['Content'])):
    perDocInfo = []
    docName = dfRagHtml["File Name"][i]
    
    #iterate over all the questions and compute
    for quest in questions:
        inputs = tokenizer(text = quest, #question
                           text_pair = dfRagHtml['Content'][i], #context
                           truncation = "only_second", #only the second option aka the context
                           padding = "max_length",
                           max_length = 384,
                           stride = 128, 
                           return_overflowing_tokens = True,
                           return_tensors="pt")
                    
        modelInputs = { "input_ids": inputs["input_ids"],
                   "attention_mask": inputs["attention_mask"]}
        
        #if multiple chunks
        if "token_type_ids" in inputs:
            modelInputs["token_type_ids"] = inputs["token_type_ids"]
            
        with torch.no_grad():
            outputs = model(**modelInputs)
        
        #start and end of tokenization
        startScores = outputs.start_logits
        endScores = outputs.end_logits
        
        # define what argmax does
        startIndex = torch.argmax(startScores, dim = 1)
        endIndex = torch.argmax(endScores, dim = 1)
        
        #identify, score, and return best of chunks
        chunkScores = []
        for i in range(len(startIndex)):
            score = startScores[i][startIndex[i]] + endScores[i][endIndex[i]]
            chunkScores.append(score)
        bestChunk = torch.argmax(torch.tensor(chunkScores))
        startBest = startIndex[bestChunk]
        endBest = endIndex[bestChunk]
        
        #swap if indexes mixed
        if startBest > endBest:
            endBest = startBest
        
        #retrive answer
        answer_tokens = inputs["input_ids"][bestChunk][startBest : endBest + 1]
        answer = tokenizer.decode(answer_tokens, skip_special_tokens = True)
        
        perDocInfo.append(answer)
        
    #add document to dataframe
    print(perDocInfo)
    print("\n\n\n\n\n")
    dfRagResult[docName] = perDocInfo





'''
transform data and save to current working directory
'''
#create, rename, and export data as csv
ragPd = pd.DataFrame(dfRagResult).T
ragPd = ragPd.set_axis(['Case Number', 'Case Name', 'Court', 'Judicial Officer', 
                        'Date Filed', 'Case Type', 'Case Status', 'Plaintiff', 
                        'Petitioner', 'Defendent', 'Serve Date', 'Compensation', 
                        'Pro Se Filer'], axis = 1) #sets column names
ragPd.to_csv(os.getcwd() + 'outputRagCases.csv')
print("total time elapsed to compute RAG: ", time.time() - startTime)



