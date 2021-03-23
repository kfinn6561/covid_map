'''
Created on 2 Aug 2020

@author: kieran
'''
import urllib
import json
import time
import os
import webbrowser




gov_base="https://www.gov.uk/api/content"
fco_base=gov_base+'/foreign-travel-advice'



def query_api(url,max_attempts=5):
    attempt=1
    while True:
        f=urllib.request.urlopen(url)
        if f.getcode()==200:
            out=f.read()
            f.close()
            return json.loads(out)
        else:
            f.close()
            print('Attempt %d to read %s failed' %(attempt,url))
            attempt+=1
            if attempt>max_attempts:
                print("Reached maximum number of attempts")
                return False
            time.sleep(2)
            print('Trying to read %s. Attempt %d' %(url,attempt))


def get_fco_advice(country):
    return query_api(fco_base+'/'+country,max_attempts=1)
    
  
def open_html(html,fname='test.html'):
    f=open(fname,'w')
    f.write(html)
    f.close()
    
    #Change path to reflect file location
    filename = 'file:///'+os.getcwd()+'/' + fname
    webbrowser.open_new_tab(filename)

