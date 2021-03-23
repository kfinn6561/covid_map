'''
Created on 14 Jan 2013

simple functions for things like progress bars and saving data to pickle files

@author: Kieran Finn
'''
import pickle

def pload(fname):
    f=open(fname,'rb')
    try:
        out=pickle.load(f)
    except:
        f.close()
        f=open(fname,'r')
        out=pickle.load(f)
    f.close()
    return out

def pdump(obj,fname):
    f=open(fname,'wb')
    pickle.dump(obj,f)
    f.close()
  
def read_file(fname):
    f=open(fname,'r')
    out=f.read()
    f.close()
    return out