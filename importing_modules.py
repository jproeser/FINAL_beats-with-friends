from importing_modules import *
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
from flask import json
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
from urllib.request import *
from bs4 import BeautifulSoup
import random
import sqlite3
import webbrowser  
import soundcloud
import soundcloud as SC
from soundcloud import *
from soundcloud.client import Client


import string
import requests
import json
import argparse
import sys
import urllib.request
import mutagen
import os
import platform
from mutagen.easyid3 import EasyID3


import time

from itertools import chain

import os
import requests
import json
from flask import Flask, render_template, session, redirect, request, url_for, flash
from flask_script import Manager, Shell
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, FileField, PasswordField, BooleanField, SelectMultipleField, ValidationError
from wtforms.validators import Required, Length, Email, Regexp, EqualTo
from flask_sqlalchemy import SQLAlchemy
import random
from flask_migrate import Migrate, MigrateCommand
from threading import Thread
from werkzeug import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash

# Imports for login management
from flask_login import LoginManager, login_required, logout_user, login_user, UserMixin, current_user
import gmplot
from gmplot import *
import googlemaps


import numpy as np
import codecs, json 

