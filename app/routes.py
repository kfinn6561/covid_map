from flask import render_template, flash, redirect,url_for,request,jsonify,send_from_directory, Markup
from app.models import Country,Territory,User,daily_update,status_colours,cblind_colours,description_dict
from app.email import send_email
from werkzeug.urls import url_parse
from general_tools import pload,pdump
from app import app, db, border_status_fname, vaccine_status_fname
from flask_login import current_user,login_user,logout_user,login_required
from app.forms import LoginForm
import datetime
import os






@app.route('/')
@app.route('/index')
@app.route('/map')
def index():    
    svg=open('app/static/BlankMap-World.svg').read()
    
    exempt_only=request.args.get('exempt_only') not in [None, 'false', 'False']
    cblind=request.args.get('colourblind') not in [None, 'false', 'False']
    vaccinated=request.args.get('vaccinated') not in [None, 'false', 'False']
    
    if exempt_only:
        '''
        countries=Country.query.filter_by(dependent=False,exempt=True).all()
        dependents=Country.query.filter_by(dependent=True,exempt=True).all()
        territories=Territory.query.join(Territory.host_country,aliased=True).filter_by(exempt=True).all()
        '''
        countries=Country.query.filter_by(dependent=False,travel_corridor=True).all()
        dependents=Country.query.filter_by(dependent=True,travel_corridor=True).all()
        territories=Territory.query.join(Territory.host_country,aliased=True).filter_by(travel_corridor=True).all()
    else:
        countries=Country.query.filter_by(dependent=False).all()
        dependents=Country.query.filter_by(dependent=True).all()
        territories=Territory.query.all()
    
    country_dicts=[]
    for country in countries:
        country_dicts.append(country.get_dict(cblind,vaccinated))
    for territory in territories:
        country_dicts.append(territory.get_dict(cblind,vaccinated))
    for dependent in dependents:
        country_dicts.append(dependent.get_dict(cblind,vaccinated))
        
    if cblind:
        colour_dict=cblind_colours
    else:
        colour_dict=status_colours
        
    return render_template('map.html',svg=Markup(svg),countries=country_dicts,exempt_only=exempt_only,cblind=cblind,vaccinated=vaccinated,colour_dict=colour_dict,description_dict=description_dict,year=datetime.datetime.now().year)


@app.route('/get_summary')
def get_summary():
    country=Country.query.filter_by(id=request.args.get('id')).first_or_404()
    return country.get_summary_html()


@app.route('/login',methods=['GET','POST'])
def login():
    form=LoginForm()
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if form.validate_on_submit():
        user=User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user)
        next_page=request.args.get('next')
        if not next_page or url_parse(next_page).netloc!='':
            next_page=url_for('index')
        return redirect(next_page)
    return render_template('login.html',title='Sign In', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Succesfully logged out')
    return redirect(url_for('index'))




@app.route('/set_border_status')
@login_required
def set_border_status():
    country=Country.query.filter_by(slug=request.args.get('slug')).first_or_404()
    country.border_status=int(request.args.get('status'))
    country.needs_updating=False
    country.old_content=country.content
    db.session.commit()
    return 'successfully changed border status of %s to %d' %(country.name,country.border_status)

@app.route('/set_vaccine_status')
@login_required
def set_vaccine_status():
    country=Country.query.filter_by(slug=request.args.get('slug')).first_or_404()
    country.vaccine_border_status=int(request.args.get('status'))
    db.session.commit()
    return 'successfully changed vaccine border status of %s to %d' %(country.name,country.vaccine_border_status)



@app.route('/load')
@login_required
def load_border_status(update=True):
    try:
        border_statuses=pload(border_status_fname)
    except IOError:
        border_statuses={}
        
    try:
        vaccine_statuses=pload(vaccine_status_fname)
    except IOError:
        vaccine_statuses={}
        
    if  update in ['false','False','f','0']:
        update=False
        out='Keeping needs_updating data'
    else:
        update=True
        out='Updating needs_updating data'  
    out+='<br//>'
    
    slug=request.args.get('slug')
    if slug in border_statuses.keys():
        countries=[Country.query.filter_by(slug=slug).first_or_404()]
    else:        
        countries=Country.query.all()
    out+='Updated border status for the following countries:'
    for country in countries:
        if country.slug in border_statuses.keys():
            country.border_status=border_statuses[country.slug]
            try:
                country.vaccine_border_status=vaccine_statuses[country.slug]
            except KeyError:
                pass
            if update:
                country.needs_updating=False
                country.old_content=country.content
            out+='<br//>'
            out+=country.name+' '+str(country.border_status)+' (%d)'%country.vaccine_border_status
    db.session.commit()
    return out


@app.route('/save')
@login_required
def save_border_status():
    try:
        border_statuses=pload(border_status_fname)
    except IOError:
        border_statuses={}
        
    try:
        vaccine_statuses=pload(vaccine_status_fname)
    except IOError:
        vaccine_statuses={}
        
    slug=request.args.get('slug')
    if slug:
        countries=[Country.query.filter_by(slug=slug).first_or_404()]
    else:        
        countries=Country.query.all()
    out='Saved border status for the following countries:'
    for country in countries:
        border_statuses[country.slug]=country.border_status
        vaccine_statuses[country.slug]=country.vaccine_border_status
        out+='<br//>'
        out+=country.name+' '+str(country.border_status)+' (%d)'%country.vaccine_border_status
    pdump(border_statuses,border_status_fname)
    pdump(vaccine_statuses,vaccine_status_fname)
    return out

@app.route('/send_email')
@login_required
def send_test_email():
    send_email('Test Email',
               sender=app.config['ADMINS'][0],
               recipients=[current_user.email],
               text_body='covid test body',
               html_body='covid test html')
    return redirect(url_for('index'))

@app.route('/update')
@login_required
def send_daily_update():
    flash("%d countries need updating" %daily_update())
    return redirect(url_for('index'))


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')
