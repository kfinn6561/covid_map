'''
Created on 31 May 2020

@author: kieran
'''
from app import db, app, login, border_status_fname
from app.email import send_email
from flask_login import UserMixin
from hashlib import md5
from flask import url_for
from scraper import query_api,fco_base
from general_tools import pload,pdump
from bs4 import BeautifulSoup
import datetime
import re
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
from lxml.html.diff import htmldiff

from werkzeug.security import generate_password_hash, check_password_hash

cmap = matplotlib.colors.LinearSegmentedColormap.from_list("", ["green","yellow","red"])

#cblind_cmap=matplotlib.colors.Colormap('inferno_r')
cblind_cmap=plt.get_cmap('inferno_r')

#cblind_cmap=cmap

status_colours={0:'#a1a1a1'}
cblind_colours={0:'#0000ff'}
for i in range(10):
    status_colours[i+1]=matplotlib.colors.to_hex(cmap(np.linspace(0,1,10)[i]))#This is quite inefficient, but it's such a small piece of code that I don't think it's worth fussing over
    cblind_colours[i+1]=matplotlib.colors.to_hex(cblind_cmap(np.linspace(0,1,10)[i]))



description_dict={
    1:"No restrictions",
    2:"No restrictions or simple temperature check if travelling from the UK, but may be restrictions if travelling from other countries",
    3:"Must supply a negative Covid test or take one on arrival",
    4:"Must take two tests and potentially undergo a short (less than 5 days) quarantine",
    5:"Must quarantine on arrival for up to 14 days",
    6:"Must quarantine on arrival for more than 14 days or with other restrictions",
    7:"Difficult to get into the country from the UK, but may be possible from another country",
    8:"All but impossible to get into the country from the UK. May be possible from other countries but very difficult",
    9:"All but impossible to get into the country unless you are a resident. Possible exemptions for essential workers/students etc",
    10:"All but impossible to get into the country unless you are a resident."
    }



#status_dict={0:'unknown',1:'closed',2:'restrictions',3:'fully_open'}


def srcrepl(match):
    "Return the file contents with paths replaced"
    absolutePath ='https://www.gov.uk/' #update the URL to be prefixed here.
    #print("<" + match.group(1) + match.group(2) + "=" + "\"" + absolutePath + match.group(3) + match.group(4) + "\"" + ">")
    return "<" + match.group(1) + match.group(2) + "=" + "\"" + absolutePath + match.group(3) + match.group(4) + "\"" + ">"

def make_links_absolute(html):
    p = re.compile(r"<(.*?)(src|href)=\"(?!http)(.*?)\"(.*?)>")
    return p.sub(srcrepl, html)



class Country(db.Model):
    id =db.Column(db.Integer,primary_key=True)
    slug=db.Column(db.String(64),index=True)
    code=db.Column(db.String(2),index=True)
    name=db.Column(db.String(64))
    api_url=db.Column(db.String(256))
    web_url=db.Column(db.String(256))
    content=db.Column(db.Text)
    old_content=db.Column(db.Text)
    exempt=db.Column(db.Boolean)
    dependent=db.Column(db.Boolean)
    travel_corridor=db.Column(db.Boolean)
    border_status=db.Column(db.Integer)
    vaccine_border_status=db.Column(db.Integer)
    last_updated=db.Column(db.DateTime)
    needs_updating=db.Column(db.Boolean)
    territories=db.relationship('Territory',backref='host_country',lazy='dynamic')
    
    def __repr__(self):
        return '<Country {}>'.format(self.name)
    
    def update(self):
        data=query_api(self.api_url)
        update_time=datetime.datetime.strptime(data['public_updated_at'],"%Y-%m-%dT%H:%M:%S.%f%z")
        if update_time>self.last_updated.replace(tzinfo=datetime.timezone.utc):
            self.last_updated=update_time.astimezone(tz=datetime.timezone.utc)
            new_content=get_content(data)
            if ''.join(new_content.split())!=''.join(self.content.split()):#no need to update if only differ by whitespace
                self.needs_updating=True
            self.content=new_content
            db.session.commit()
        return self.needs_updating
        
    def get_update_html(self):
        out='<h1>FCO advice for %s</h1>' %self.name
        out+='\n\n<br>\n<br>\n\n'
        out+=htmldiff(self.old_content,self.content)
        out+='\n\n<br>\n<br>\n\n'
        out+='<h1>Change status for %s?</h1>\n'%self.name
        out+='<a href="%s" target="_blank">keep status as %d</a>' %(url_for('set_border_status',slug=self.slug,status=self.border_status,_external=True),self.border_status)
        out+='\n<br>\n'
        for i in range(1,11):
            out+='<a href="%s" target="_blank">set status to %d</a>' %(url_for('set_border_status',slug=self.slug,status=i,_external=True),i)#This will have to change when uploaded
            out+='\t\t\t'
        out+='\n\n<br>\n\n'
        out+='<h1>Is it different if vaccinated?</h1>\n'
        out+='<a href="%s" target="_blank">no</a>' %(url_for('set_vaccine_status',slug=self.slug,status=-1,_external=True))
        out+='\n<br>\n'
        for i in range(1,11):
            out+='<a href="%s" target="_blank">set status to %d</a>' %(url_for('set_vaccine_status',slug=self.slug,status=i,_external=True),i)#This will have to change when uploaded
            out+='\t\t\t'
        out+='\n\n<br>\n<br>\n\n'
        
        return out
    
    def get_summary_html(self):
        out='Last updated '
        out+=self.last_updated.strftime("%d %B, %Y")
        out+='\n<br>\n<br>\n\n'
        out+=self.content
        return out
        
    def get_vaccine_status(self):
        if self.vaccine_border_status==-1:
            return self.border_status
        else:
            return self.vaccine_border_status
    
    def save_border_status(self):
        try:
            border_statuses=pload(border_status_fname)
        except IOError:
            border_statuses={}
        border_statuses[self.slug]=self.border_status
        pdump(border_statuses, border_status_fname)
        return True
        
    def load_border_status(self):
        try:
            border_statuses=pload(border_status_fname)
        except IOError:
            return False
        if self.slug in border_statuses.keys():
            self.border_status=border_statuses[self.slug]
            db.session.commit()
            return True
        else:
            return False
        
    def get_dict(self,cblind=False,vaccine=False):
        if vaccine:
            out_border_status=self.get_vaccine_status()
        else:
            out_border_status=self.border_status
        if cblind:
            out_colour=cblind_colours[out_border_status]
        else:
            out_colour=status_colours[out_border_status]
        return {'id':self.id,
                'name':self.name,
                'slug':self.slug,
                'code':self.code.lower(),
                'exempt':self.exempt,
                'border_status':out_border_status,
                'status_colour':out_colour,
                'url':self.web_url}
        
 

class Territory(db.Model):
    id =db.Column(db.Integer,primary_key=True)
    code=db.Column(db.String(2),index=True)
    name=db.Column(db.String(64))
    country_id=db.Column(db.Integer,db.ForeignKey('country.id'))
    
    def __repr__(self):
        return '<Territory {}>'.format(self.name)
    
    def get_dict(self,cblind=False,vaccine=False):
        out=self.host_country.get_dict(cblind,vaccine)
        out['name']=self.name
        out['code']=self.code.lower()
        return out


class User(UserMixin,db.Model):
    id =db.Column(db.Integer,primary_key=True)
    username=db.Column(db.String(64),index=True,unique=True)
    email=db.Column(db.String(120),index=True,unique=True)
    password_hash=db.Column(db.String(128))
    
    def __repr__(self):
        return '<User {}>'.format(self.username)
    
    def set_password(self,password):
        self.password_hash=generate_password_hash(password)
        
    def check_password(self,password):
        return check_password_hash(self.password_hash, password)
    
    def avatar(self, size):
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        return 'https://www.gravatar.com/avatar/{}?d=identicon&s={}'.format(
            digest, size)
    
    
@login.user_loader
def load_user(uid):
    return User.query.get(int(uid))




def remove_from_list(lst,to_remove):
    out=[]
    for item in lst:
        if item!=to_remove:
            out.append(item)
    return out
    



'''
ATTEMPT TO AUTOMATICALLY DETERMIN BORDER STATUS
 
def get_closed_phrases(name):
    return [name+' is closed',
            'cannot enter '+name,
            'cannot enter the '+name,
            ]
 
  

def determine_border_status(summary,entry,name):#0=undetermined, 1=closed, 2=open
    sum_soup=BeautifulSoup(summary)
    ent_soup=BeautifulSoup(entry)
    out=0
    
    summary_divs=sum_soup.find_all('div',class_='call-to-action')
    for div in summary_divs:
        lines=div.get_text().split('\n')
        lines=remove_from_list(lines,'')
        for line in lines:
            if  
'''
  


def get_entry_content(data):
    parts=data['details']['parts']
    for part in parts:
        if part['slug']=='entry-requirements':#this may be a bit temperamental if things change
            return make_links_absolute(part['body'])
    return ''
    
def get_summary(data):
    soup=BeautifulSoup(data['details']['summary'], features="html.parser")
    summary_divs=soup.find_all('div',class_='call-to-action')
    if len(summary_divs):
        return make_links_absolute(str(summary_divs[0]))
    else:
        return ''
    
def get_content(data):
    return get_summary(data)+'\n<br>\n<br>\n\n'+get_entry_content(data)
    
 
def get_entry_summary(url):
    data=query_api(url)
    return [get_entry_content(data),data['public_updated_at']]    
  
       
def update_all(write_to_file=True):
    print("Updating all countries")
    border_status_html='''
        <head>
        <style>
        ins{background:rgba(0,255,0,0.5)}
        del{background:rgba(255,0,0,0.5)}
        </style>
        </head>
        <body>
        Countries that need updating:<br>'''
    countries=Country.query.all()
    count=0
    end=''
    for country in countries:
        if country.update() or country.needs_updating:
            print("Updated %s" %country.name)
            count+=1
            border_status_html+=country.name+'<br>\n'
            end+=country.get_update_html()
    border_status_html+='<br>\n<br>\n\n'
    border_status_html+=end
    border_status_html+='</body>'
    if write_to_file:
        with open('border_status.html','w',encoding='utf-8') as f:
            try:
                f.write(border_status_html)
            except:
                print("Error saving to file")
    #update_exemptions()
    update_travel_corridors()
    db.session.commit()
    return (count,border_status_html)
    
def update_exemptions():
    print("updating exceptions")
    for country in Country.query.all():
        country.exempt=False
    
    url="https://www.gov.uk/api/content/guidance/coronavirus-covid-19-countries-and-territories-exempt-from-advice-against-all-but-essential-international-travel"
    data=query_api(url)
    soup=BeautifulSoup(data['details']['body'], features="html.parser")
    links=soup.find_all('a')    
    for link in links:
        slug=link.get("href").split('/')[-1]
        country=Country.query.filter_by(slug=slug).first()
        if country:
            country.exempt=True
    db.session.commit()
            
def update_travel_corridors():
    print("updating travel corridors")
    for country in Country.query.all():
        country.travel_corridor=False
    url="https://www.gov.uk/api/content/guidance/coronavirus-covid-19-travel-corridors"
    data=query_api(url)
    soup=BeautifulSoup(data['details']['body'], features="html.parser")
    links=soup.find_all('a')
    for link in links:
        slug=link.get("href").split('/')[-1]
        country=Country.query.filter_by(slug=slug).first()
        if country:
            country.travel_corridor=True
    db.session.commit()
            
            
        
def daily_update():
    users=User.query.all()
    count,html=update_all()
    
    send_email('Covid Map update for '+datetime.date.today().strftime("%A %d %B, %Y")+'. %d countries need updating' %count,
           sender=app.config['ADMINS'][0],
           recipients=[user.email for user in users],
           text_body='covid test body',
           html_body=html)
    return count
        
        
        
        
        
        
        