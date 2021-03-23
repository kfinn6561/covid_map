'''
Created on 2 Aug 2020

@author: kieran
'''
import datetime
from app import db
from general_tools import pload,pdump
from scraper import query_api,fco_base
from app.models import border_status_fname,Country,update_all,get_entry_summary,\
    update_exemptions, update_travel_corridors,Territory
import json


def populate_db():
    #clear database
    for country in Country.query.all():
        db.session.delete(country)
    
    data=query_api(fco_base)
    N=len(data['links']['children'])
    for i in range(N):
        cdata=data['links']['children'][i]
        
        slug=cdata['details']['country']['slug']
        name=cdata['details']['country']['name']
        
        print("Adding %s to the database\t\t\t\t\t(%d of %d)" %(name,i+1,N))
        
        
        content,updated_at=get_entry_summary(cdata['api_url'])
        
        
        country=Country(slug=slug,
                        name=name,
                        api_url=cdata['api_url'],
                        web_url=cdata['web_url'],
                        content=content,
                        old_content=content,
                        exempt=False,
                        dependent=False,
                        travel_corridor=False,
                        border_status=0,
                        needs_updating=False,
                        last_updated=datetime.datetime.strptime(updated_at,"%Y-%m-%dT%H:%M:%S.%f%z").astimezone(tz=datetime.timezone.utc)  #"%Y-%m-%dT%H:%M:%S.%fZ")#,"%Y-%m-%dT%H:%M:%SZ")
                        )
        db.session.add(country)
    db.session.commit()
    add_codes()
    update_exemptions()
    update_dependents()
    update_travel_corridors()
    fill_territory_table()
    update_all_border_statuses()
    
def update_all_border_statuses():
    countries=Country.query.all()
    out=''
    count=0
    for country in countries:
        if country.needs_updating or country.border_status==0:
            count+=1
            out+=country.get_update_html()
            out+='\n\n<br>\n<br>\n\n'
    f=open('update_border_status.html','w',encoding='utf-8')
    f.write(out)
    f.close()
    print("%d countries need updating" %count)





def lookup_name(name,keys):
    if name in keys:
        return name
    lower_keys={key.lower():key for key in keys}
    if name.lower() in lower_keys:
        return lower_keys[name.lower()]
    short_keys={key[:len(name)].lower():key for key in keys}
    if name.lower() in short_keys.keys():
        return short_keys[name.lower()]
    
    for key in lower_keys.keys():
        if name.lower() in key:
            return lower_keys[key]
        
    lookup_dict=pload('country_name_dict.pkl')
    if name in lookup_dict.keys():
        return lookup_dict[name]
        
    
    if 'St ' in name:
        return lookup_name(name.replace('St ', 'Saint '),keys)
    
    return False
    
    
extra_codes={'Kosovo':'XK'}

def add_codes():
    f=open('country_codes.json')
    code_json=json.loads(f.read())
    f.close()
    codes={}
    for country in code_json:
        codes[country['Name']]=country['Code']
    for country in extra_codes.keys():
        codes[country]=extra_codes[country]
        
    countries=Country.query.all()
    for country in countries:
        code=codes[lookup_name(country.name,codes.keys())]
        print('Setting code for %s to %s' %(country.name,code))
        country.code=code
        
    db.session.commit()

        
        
    
territories={'denmark':[('Greenland','gl'),('Faroe Islands','fo')],
             'usa':[('Guam','gu'),('Northern Mariana Islands','mp'),('Puerto Rico','pr'),('U.S. Virgin Islands','vi'),('American Samoa','as')],
             'cook-islands-tokelau-and-niue':[('Niue','nu'),('Tokelau','tk')],
             'italy':[('Vatican City','va')],
             'france':[('Saint Barthelemy','bl'),('French Southern Territories','tf')]}

    
def fill_territory_table():
    for territory in Territory.query.all():
        db.session.delete(territory)
        
    for slug in territories.keys():
        country=Country.query.filter_by(slug=slug).first()
        for name, code in territories[slug]: 
            territory=Territory(name=name,
                                code=code,
                                host_country=country)
            db.session.add(territory)
            print('Added %s to the database' %name)
    db.session.commit()
    
    
dependents=['mayotte',
            'reunion',
            'macao',
            'hong-kong',
            'bonaire-st-eustatius-saba',
            'western-sahara',
            'french-guiana']
    
def update_dependents():
    #clear
    countries= Country.query.all()
    for country in countries:
        country.dependent=False
    for slug in dependents:
        country=Country.query.filter_by(slug=slug).first()
        country.dependent=True
    db.session.commit()


def combine_content_summary():
    countries= Country.query.all()
    for country in countries:
        content=country.summary+'\n\n<br>\n<br>\n\n'+country.content
        country.content=content
        country.old_content=content
    db.session.commit()
    
    
    