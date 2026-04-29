#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@author: nylaaa.
Must provide your own API Key from serpapi.com
"""

'''
load packages
'''
import subprocess
import sys

def install(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

for i in ['serpapi', 'pandas']:
    install(i)
    
from serpapi import GoogleSearch
import pandas as pd
import time
import random
import os


'''
inititalize variables
'''
startTime = time.time()
start = 0 #for pagination
NUMPERPAGE = 20 #number of results to return per search
api_key = 
params = {
  "engine": "google_scholar",
  "q": "georgia civil pro se",
  "gl": "us",
  "hl": "en",
  "as_sdt": "4,11",
  "num": NUMPERPAGE,
  "start": start,
  "api_key": api_key
}


search =  GoogleSearch(params) 
results = search.get_dict()
d2 = {}
tempUrl = "https://scholar.google.com"



'''
given a base results object and starting point, recursively adds cases to a dataframe

@PARAMS 
    results: dictinary, result object of first search
    start: integer, paginated starting point 
'''
def pullAndWait(results, start):
    #results from each page 
    for i in results['organic_results']:
        #casename and case link
        try:
            d2[i["title"]] = [i["link"], i]
        except KeyError: # in cases where the link is not in the JSON
            d2[i["title"]] = [".", i]
        except: #something else is wrong
            d2[i] = [".", "invalidated"]
        
    # if there is another page to paginate, reset 
    if 'next' in results.get("serpapi_pagination", {}):
        time.sleep(random.randint(1,30)) #not to overload serpapi
        start += 10 #pagination is +10 for serpAPI
        
        params = { #reset params with new start
          "engine": "google_scholar",
          "q": "georgia civil pro se",
          "gl": "us",
          "hl": "en",
          "as_sdt": "4,11",
          "num": NUMPERPAGE,
          "start": start,
          "api_key": api_key
          }
        
        search =  GoogleSearch(params) 
        newRes = search.get_dict()
        
        pullAndWait(newRes, start) 
    #end of method 
        


'''
run search from base page, print run time, and save as local CSV
'''
pullAndWait(results, start)

print("total time elapsed to compute google scholar: " + str(time.time() - startTime))

scholarDf = pd.DataFrame(d2) 
scholarDf = scholarDf.set_axis(["Location", "JSON"])
scholarDf = scholarDf.T
scholarDf = scholarDf.rename_axis("Case Name")
scholarDf.to_csv(os.getcwd()+"/googleScholarCases.csv", index = True) 


