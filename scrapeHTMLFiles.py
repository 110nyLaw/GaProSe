#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@author: nylaaa.
Convert HTMLs to csv of file name: content 
"""

'''
import packages
'''
import pandas as pd
import os
from bs4 import BeautifulSoup
import time


'''
define variables
'''
dataHTML2 = dict()
startTime = time.time()
#os.chdir("") #change directory to folder with python files


#find and open every local html file and add to dataframe
for file in os.listdir(os.getcwd() + "/1/html"): #file gets the name of the file within, not the full path to the file
    with open(os.getcwd() + "/1/html/" + file, 'r', encoding = 'latin-1') as f:
        fileFormat = f.read() 
        soup2 = BeautifulSoup(fileFormat, 'html.parser')
        
        dataHTML2[file] = [soup2.text]


'''
print run time and export as CSV
'''
print("total time elapsed to compute HTML storage: " + str(time.time()-startTime))

#creates dataframes and exports as csv
dfHTML2 = pd.DataFrame(dataHTML2)
dfHTML2 = dfHTML2.T
dfHTML2.index.name = "File Name"
dfHTML2 = dfHTML2.set_axis(["Content"], axis = 1)
dfHTML2.to_csv(os.getcwd() + '/CSVs/localHTMLcases.csv', index=True)