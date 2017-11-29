# An application about recording favorite songs & info
import os
from flask import Flask, render_template, session, redirect, url_for, flash
from flask_script import Manager, Shell
from flask import make_response
# from flask_moment import Moment # requires pip/pip3 install flask_moment
from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, SubmitField, Form, BooleanField, PasswordField, validators
from wtforms.validators import Required
from wtforms import *
from flask import *
from flask_sqlalchemy import SQLAlchemy
import random
from flask_migrate import Migrate, MigrateCommand # needs: pip/pip3 install flask-migrate
from flask_mail import Mail, Message
from threading import Thread
from werkzeug import secure_filename
import json
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import requests
import re
import nltk
import pyzipcode
#from pyzipcode import ZipCodeDatabase
#from pyzipcode import Pyzipcode as pz
from pyzipcode import *
import unittest
from uszipcode import ZipcodeSearchEngine
from bs4 import BeautifulSoup
from selenium import webdriver
from urllib.request import urlopen
from bs4 import BeautifulSoup
import random
import sqlite3
import webbrowser  
import soundcloud
import soundcloud as SC
from soundcloud import *
from soundcloud.client import Client



# Configure base directory of app
basedir = os.path.abspath(os.path.dirname(__file__))

# Application configurations
app = Flask(__name__)
app.debug = True
app.static_folder = 'static'
app.config['SECRET_KEY'] = 'hardtoguessstringfromsi364thisisnotsupersecurebutitsok'
# app.config['SQLALCHEMY_DATABASE_URI'] =\
    # 'sqlite:///' + os.path.join(basedir, 'data.sqlite') # Determining where your database file will be stored, and what it will be called
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://localhost/songs_data" # TODO: decide what your new database name will be, and create it in postgresql, before running this new application (it's similar to an old one, but has some more to it)
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Set up email config stuff
app.config['MAIL_SERVER'] = 'smtp.googlemail.com'
app.config['MAIL_PORT'] = 587 #default
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME') # TODO export to your environs -- may want a new account just for this. It's expecting gmail, not umich
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['MAIL_SUBJECT_PREFIX'] = '[Songs App]'
app.config['MAIL_SENDER'] = 'Admin <>' # TODO fill in email
app.config['ADMIN'] = os.environ.get('ADMIN')

# Set up Flask debug stuff
manager = Manager(app)
# moment = Moment(app) # For time # Later
db = SQLAlchemy(app) # For database use
migrate = Migrate(app, db) # For database use/updating
manager.add_command('db', MigrateCommand) # Add migrate command to manager
mail = Mail(app) # For email sending


# SC.initialize({
#       client_id: "6d3KZ6G4o4U0GLCiznHCjbQrT2Ee90cn",
#       redirect_uri: "www.jamesroeser.com",
#   });

## Set up Shell context so it's easy to use the shell to debug
# Define function
def make_shell_context():
    return dict(app=app, db=db)
# Add function use to manager
manager.add_command("shell", Shell(make_context=make_shell_context))


#########
######### Everything above this line is important/useful setup, not problem-solving.
#########

##### Functions to send email #####

def send_async_email(app, msg):
    with app.app_context():
        mail.send(msg)

def send_email(to, subject, template, **kwargs): # kwargs = 'keyword arguments', this syntax means to unpack any keyword arguments into the function in the invocation...
    msg = Message(app.config['MAIL_SUBJECT_PREFIX'] + ' ' + subject,
                  sender=app.config['MAIL_SENDER'], recipients=[to])
    msg.body = render_template(template + '.txt', **kwargs)
    msg.html = render_template(template + '.html', **kwargs)
    thr = Thread(target=send_async_email, args=[app, msg]) # using the async email to make sure the email sending doesn't take up all the "app energy" -- the main thread -- at once
    thr.start()
    return thr # The thread being returned
    # However, if your app sends a LOT of email, it'll be better to set up some additional "queuing" software libraries to handle it. But we don't need to do that yet. Not quite enough users!




##### Set up Models #####

# Set up association Table between artists and albums
#collections = db.Table()


class Name(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))

class URL(db.Model):
    __tablename__ = "accounturls"
    id = db.Column(db.Integer, primary_key=True, unique=True)
    accounturl = db.Column(db.String(64))

class URL(db.Model):
    __tablename__ = "songurls"
    id = db.Column(db.Integer, primary_key=True, unique=True)
    songurl = db.Column(db.String(64))

class Zipcode(db.Model):
    __tablename__ = "zipcodes"
    id = db.Column(db.Integer, primary_key=True)
    zipcode = db.Column(db.Integer) 

######################
class NameForm(FlaskForm):
    name = StringField('<h4>What is your name?<br/></h4>', [Required()])
    soundcloud = StringField('<h4>What is the URL to your soundcloud accout?</h4><p><i><i/></p><br/>', [Required(message="required"),validators.Regexp('^https://soundcloud.com/', message="Please enter a valid account")])
    zipcode = StringField('<h4>What is your zipcode?<br/></h4>', [Required()])
    submit = SubmitField('Submit')


class ZipSearchForm(FlaskForm):
    searchzip = IntegerField('<h4>Zipcode<br/></h4>', [Required()])
    searchradius = IntegerField('<h4>Search Mile Radius<br/></h4>', [Required()])
    submit = SubmitField('Submit')


##### Set up Controllers (view functions) #####

## Error handling routes
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500

## Main route

# @app.route('/')
# def home():
#     return render_template('home.html')
@app.route('/')
def zipsearch():
    simpleForm = ZipSearchForm()

    search = make_response(render_template('zipform.html', form=simpleForm))
    form = ZipSearchForm(request.form)

    return search

@app.route('/signin')
def signin():
    simpleForm = NameForm()

    newuser = make_response(render_template('addaccount.html', form=simpleForm))
    form = NameForm(request.form)

    return newuser

@app.route('/searchresults')
def searchresults():    
    print('hey')
    #return name



@app.route('/welcome', methods = ['GET', 'POST'])
def welcome():
    form = NameForm(request.form)


    name = form.name.data
    soundcloud = form.soundcloud.data
    zipcode = form.zipcode.data

    x = re.match('^https://soundcloud.com/',soundcloud)    

    if x is None and name is "":
        flash('Please fill out the form before submitting!')    
    elif name is "":
        flash('Please enter your name!')    
    
    elif x is None:
        flash('Please enter a valid SoundCloud URL, beginning with https://soundcloud.com/')


    if request.method == 'POST' and form.validate_on_submit():
        
        # name = form.name.data
        # soundcloud = form.soundcloud.data

        

        session['name'] = form.name.data
        name=session.get('name')

        session['soundcloud'] = form.soundcloud.data
        soundcloud=session.get('soundcloud')

        session['zipcode'] = form.zipcode.data
        zipcode=session.get('zipcode')

        sc = str(soundcloud)
        sc = sc.replace("https://soundcloud.com/", "")


        return render_template('welcome.html', name = name, soundcloud = soundcloud, sc = sc, zipcode=zipcode)

    return redirect(url_for('signin'))


def parseSoundcloud(x):
    name = session.get('name')
    soundcloud = session.get('soundcloud')
    sc = str(soundcloud)
    sc = sc.replace("https://soundcloud.com/", "")

    z = str(x)

    driver = webdriver.PhantomJS()
    driver.set_window_size(1120, 550)
    url = 'https://soundcloud.com/'+str(x)+'/tracks'
    #url = z
    driver.get(url)
    html = driver.page_source
    soup = BeautifulSoup(html, "html.parser")
    songlinks=[]

    scheight = .1
    while scheight < 9.9:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight/%s);" % scheight)
        scheight += .01
    #scrolls through the entire webpage so that all the songs are found, not just the first 10
    elem = driver.find_element_by_tag_name('a')
    for x in driver.find_elements_by_class_name('soundTitle__title'):
    #finds the link to each song of each user
        songlinks.append(x.get_attribute('href'))
    #stores this in a list
    driver.quit()
    return render_template('sclinks.html', songlinks=songlinks, name=name, sc=sc)

@app.route('/me')
def me():    
    name = session.get('name')
    return name

@app.route('/soundcloud', methods= ['POST','GET'])
def scform():
    return render_template('scform.html')


@app.route('/yoursc')
def yoursc():
    if request.method == 'GET':
        result = request.args
        x = result.get('sc')
        return parseSoundcloud(x)
 

@app.route('/my/<sc>')
def my(sc):
    name = session.get('name')


    x = sc
    return parseSoundcloud(x)

@app.route('/api')
def api():
    #client = soundcloud.Client(client_id='6d3KZ6G4o4U0GLCiznHCjbQrT2Ee90cn', client_secret='Wsx3mWNnRVSScuVBzwSiAb6HnbhcCsno', redirect_uri='http://www.jamesroeser.com')
    # client = soundcloud.Client(access_token='YOUR_ACCESS_TOKEN')
    # SC.get('/tracks/293', function(track) {SC.oEmbed(track.permalink_url, document.getElementById('player'));})
    #tracks_json = file_get_contents('http://api.soundcloud.com/isthatfree/tracks.json?client_id=6d3KZ6G4o4U0GLCiznHCjbQrT2Ee90cn');
    #sx = client.get('/users/isthatfree/tracks')
    #print client.get('/me').username
    #return (tracks_json)

    # api = "http://api.soundcloud.com/resolve.json?url=https://soundcloud.com/core-rex/tracks&client_id=6d3KZ6G4o4U0GLCiznHCjbQrT2Ee90cn"
    # r = requests.get(api)
    # print('afdsafda',r)
    # #return (sx)

    pass

@app.errorhandler(404)
def pageNotFound(error):
    # return 'sorry'
    return render_template('404error.html'), 404



@app.errorhandler(500)
def internal_error(error):
    return render_template('500error.html'), 500


if __name__ == '__main__':
    db.create_all()
    manager.run() # NEW: run with this: python main_app.py runserver
    # Also provides more tools for debugging
