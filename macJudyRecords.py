#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@author: nylaaa.
Configured for Apple OS
Scrape JudyRecords.com for Georgia Civil pro se cases
"""


'''
load packages
'''
import subprocess
import sys

def install(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

for i in ['requests', 'pandas', 'bs4', 'selenium']:
    install(i)

import requests
import os
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.safari.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time


'''
initialize variables. ensure initial connection
'''
url = "https://www.judyrecords.com"
startTime = time.time()


'''
capture initial connection request. Subsequent calls won't work unless this does
throws exception if tried 5 times and no successful connection 

@PARAMS
    response: requests response
'''
def timedInitialRequest(response):
    global timeOutLimit
    if response.status_code == 200: #successful code == 200
        print("Page Received")
        timeOutLimit = -1
    else:
        print("Error: " + response.text)
        if timeOutLimit >= 6:
            raise TimeoutError("Initial response is invalid. Examine errors")
        else:
            timeOutLimit += 1
            time.sleep(timeOutLimit  * 60)
            timedInitialRequest(response)




#set up
response = requests.get(url, timeout = (30, 30))
timeOutLimit = 7
timedInitialRequest(response)

data = {}

driver = webdriver.Safari()
driver.use_technology_preview = True #can be set to false if don't want to watch as runs




'''
adds the case to the current dataframe
@PARAMS
    case: list of case details, [0] is the case name
'''
def addCasetoDf(case):
    data[case[0]] = case[1:]
    


'''finds all tags before and after "events and hearings" 
#necessary for chronology and served
@PARAMS
    soup: beautifulSoup object of specific case page
    
@RETURN
    gives the p tags before and after and the p tags that are after the current class 
    as an unpacked tuple of 3
'''
def findBeforeAfter(soup):
    h1 = soup.find("h1", string = "Events and Hearings")
    beforeP = afterP = afterClass = []
    if h1 == None: 
        return [],[],[]
    else:
    #gets all the p tags before event hearings
        #returns [] if nothing found
        beforeP = list(reversed(h1.find_all_previous('p'))) 
        afterP = list(reversed(h1.find_all_next('p')))
        afterClass = h1.find_all_next(class_ = "portal-case-event")
        chronology = []           
        for i in afterClass: 
            chronology.append(i.get_text())
    return beforeP, afterP, afterClass



'''
parses out most of the information necessary to build a case
@PARAMS
    soup: BeautifulSoup object for the particular case 
    link: link to where the case can be found on the web
@RETURN
    returns list of cas specific details
'''
def getCaseCriticals(soup, link): 
    classicTags, actionPTags , actionClassTags = findBeforeAfter(soup)
    
    caseName = caseNum = caseCourt = caseJOfficer = caseFiled =  ""
    caseType = caseStatus = caseDefendent = casePlaintiff  = ""
    casePetitioner = caseCompensation = caseServeDate = ""
    
    for i in classicTags:
       text = i.get_text()
       match text:
           case t if " VS " in t:
               caseName = text.split(" | ")[1]
           case t if "Case Number" in t:
                caseNum = text.split(" | ")[0]
           case t if "Court" in t:  
               caseCourt = text 
           case t if "Judicial Officer" in t:
               caseJOfficer = text
           case t if "File Date" in t:
               caseFiled = text
           case t if "Case Type" in t:
               caseType = text 
           case t if "Case Status" in t: 
               caseStatus = text
           case t if "Defendant" in t: 
               caseDefendent = text
           case t if " Plaintiff " in t:
               casePlaintiff = text
           case t if "Petitioner" in t:
               casePetitioner = text
           case t if "Compensatory:" in t:
               caseCompensation = text
               
    #get if they had been served before           
    for i in actionPTags:
        text = i.get_text()
        match text:
            case t if "Served" in t:
                caseServeDate = t #serve method inside this    
       
    #groups all of chronology together
    chronology = []
    for i in actionClassTags: 
        chronology.append(i.get_text())
        
    return [caseNum, caseName, caseCourt, caseJOfficer, caseFiled, caseType, caseStatus, casePlaintiff, casePetitioner, caseDefendent, caseCompensation, caseServeDate, chronology, link]



'''
gets the URL and dynamically scrapes each one from the start page, with minor rate limiting
@PARAMS
    url: website link 
    css_selector:
    keys: search term
'''
def wait_and_scrape(url, css_selector, keys):
    driver.get(url)
    time.sleep(2)
    # Wait for the element to be present
    inputPage = driver.find_element(By.NAME, "search")
    inputPage.send_keys(keys + Keys.ENTER)
    
    # Get the page source and parse with BeautifulSoup
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    time.sleep(3)
    
    #returns a web element list
    parse = driver.find_elements(By.CLASS_NAME, "title") #using javascript and is reading source and not results
    tempUrl = "https://www.judyrecords.com"
    
    #gets the firts page 
    for i in parse:
        tempUrl = url + i.get_attribute("innerHTML").split('"')[1] ##without class title, easier to parse
        tempResponse = requests.get(tempUrl, timeout = (10, 30))
        tempSoup = BeautifulSoup(tempResponse.content, 'html.parser')
        addCasetoDf(getCaseCriticals(tempSoup, tempUrl))
    
    #paginate
    soup = BeautifulSoup(driver.page_source, 'html.parser')   
    aTags = soup.find(class_ ='goToNextPage buttonStyle1') #returns <a class="goToNextPage buttonStyle1" data-ref-page="2" href="/getSearchResults/?page=2" title="Go to next page.">Next<div class="arrow-right"></div></a>
    driver.get(url + aTags.get("href")) 
    time.sleep(2)
    justScrape(url + aTags.get("href"), driver) 
    
    
    
'''
gets the case details from a single case
@PARAMS
    url: website link to find case
    driver: selenium driver
'''
def justScrape(url, driver): 
    parse = driver.find_elements(By.CLASS_NAME, "title") 
    tempUrl = "https://www.judyrecords.com"
    
    for i in parse:
        tempUrl = url + i.get_attribute("innerHTML").split('"')[1]
        tempResponse = requests.get(tempUrl, timeout = (10, 30))
        tempSoup = BeautifulSoup(tempResponse.content, 'html.parser')
        addCasetoDf(getCaseCriticals(tempSoup, tempUrl))
        
    soup = BeautifulSoup(driver.page_source, 'html.parser') 
    aTags = soup.find(class_ ='goToNextPage buttonStyle1')
    
    if aTags != None:
        driver.get(url + aTags.get("href"))
        justScrape(url + aTags.get("href"), driver)
   
    

'''
search parameters, run full scrape, and save locally
'''
keys = ["georgia court civil pro se", "georgia civil pro se", "georgia civil pro se -statement of claim", 'divorce pro se "georgia court"', 'incarcerated georgia civil court "pro se"',
        '"pro per" "georgia court"', "georgia court civil pro per", "georgia civil pro per", "georgia civil pro per -statement of claim", 'divorce pro se "georgia court"', 'incarcerated georgia civil court "pro per"']

for i in keys:
    soup = wait_and_scrape(url, "input", i)

driver.close()


print("total time elapsed to compute JudyRecords: " + str(time.time()-startTime))


df = pd.DataFrame(data).T.reset_index()
df = df.set_axis(['Case Number', 'Case Name', 'Court', 'Judicial Officer', 'Date Filed', 
                  'Case Type', 'Case Status', 'Plaintiff', 'Petitioner', 'Defendent', 
                  'Compensation', 'Date Served', 'Chronology', 'Link'], axis = 1) #sets column names
df.to_csv(os.getcwd() + '/CSVs/judycases.csv')       


