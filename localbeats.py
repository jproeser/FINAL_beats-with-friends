from importing_modules import *

# Configure base directory of app
basedir = os.path.abspath(os.path.dirname(__file__))

# Application configurations
app = Flask(__name__)
app.debug = True
app.static_folder = 'static'
app.config['SECRET_KEY'] = 'hardtoguessstring'

app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get('DATABASE_URL') or "postgresql://localhost/lb3"  # TODO: decide what your new database name will be, and create it in postgresql, before running this new application
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Seting up email
app.config['MAIL_SERVER'] = 'smtp.googlemail.com'
app.config['MAIL_PORT'] = 587 #default
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME') 
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['MAIL_SUBJECT_PREFIX'] = '[Songs App]'
app.config['MAIL_SENDER'] = 'Admin <>' # TODO fill in email
app.config['ADMIN'] = os.environ.get('ADMIN')

# Seting up Flask debuggers
manager = Manager(app)
db = SQLAlchemy(app) # For database use
migrate = Migrate(app, db) # For database use/updating
manager.add_command('db', MigrateCommand) 
mail = Mail(app) # For email sending

# Login configurations setup
login_manager = LoginManager()
login_manager.session_protection = 'strong'
login_manager.login_view = 'login'
login_manager.init_app(app) 

client = soundcloud.Client(client_id='6d3KZ6G4o4U0GLCiznHCjbQrT2Ee90cn')
CLIENTID = '6d3KZ6G4o4U0GLCiznHCjbQrT2Ee90cn'

def make_shell_context():
    return dict(app=app, db=db)
manager.add_command("shell", Shell(make_context=make_shell_context))


###################################################################################################

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
zips_and_accounts = db.Table('zips_and_accounts',db.Column('zipcode_id', db.Integer, db.ForeignKey('zipcodes.id')),db.Column('account_id',db.Integer, db.ForeignKey('scaccounts.id')))


####???collections = 


class SCaccount(db.Model):
    __tablename__ = "scaccounts"
    id = db.Column(db.Integer, primary_key=True)
    sc_url = db.Column(db.String(64), unique=True)
    zipcodes = db.relationship('Zipcode',secondary=zips_and_accounts,backref=db.backref('scaccounts',lazy='dynamic'),lazy='dynamic')
    sc_username = db.Column(db.String(64), unique=True) #is this ok even if regex

class Zipcode(db.Model):
    __tablename__ = "zipcodes"
    id = db.Column(db.Integer, primary_key=True)
    sc_zip = db.Column(db.Integer, db.ForeignKey("scaccounts.id"))

class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    # username = db.Column(db.String(255), unique=True, index=True)
    ###How to make email the username?
    email = db.Column(db.String(64), unique=True, index=True)
    # collection = db.relationship('PersonalCollection', backref='User')
    password_hash = db.Column(db.String(128))
    account_ids = db.Column(db.Integer, db.ForeignKey("scaccounts.id")) ##or db.relationship('SCaccount', backref='User')





    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def is_authenticated(self):
        return True

    @property
    def is_active(self):
        return True



@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id)) # returns User object or None

################################# CLASS NOTES ##########################
# songs on many playlists, playlists can have many songs
# relationshi = on playlists
# association table - need two diff tables that represnt each entity. Need to setup each relationship and an associaiton table
# secondary = name of association table that you're going to setup (on_playlist)
# need to build association table 

# in either of the models you need a =db.relationship line
# db.Column for each of the unique aspects for each table

# association table only necessary for many to many relationships. if one to many relationship, the many tables need an id from the one table. so for user you do playlists = db.relationship('Playlist', backref='User'). relationship with a playlist table that references the user table. relationship in the one that's one and a foreign key in the one that's many.


# on_playlist = db.Table('on_playlist', db.Column('user_id', db.Integer, db. ForeignKey('songs.id')), db.Column('playlist_id', db.Integer))

# class Song,
# class Playlist(db.Model)
#     __tablename__ = "playlists"
#     id = ...
#     name = ....
#     user_id = .....
#     songs = db. relationship('Song', secondary=on_playlist, backref=db.backref('playlists', lazy='dynamic'), lazy='dynamc')
        



##################################################################

class RegistrationForm(FlaskForm):
    email = StringField('Email:', validators=[Required(),Length(1,64),Email()])
    #username = StringField('Username:',validators=[Required(),Length(1,64),Regexp('^[A-Za-z][A-Za-z0-9_.]*$',0,'Usernames must have only letters, numbers, dots or underscores')])
    password = PasswordField('Password:',validators=[Required(),EqualTo('password2',message="Passwords must match")])
    password2 = PasswordField("Confirm Password:",validators=[Required()])
    submit = SubmitField('Register User')

    #Additional checking methods for the form
    def validate_email(self,field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('Email already registered.')

    # def validate_username(self,field):
    #     if User.query.filter_by(username=field.data).first():
    #         raise ValidationError('Username already taken')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[Required(), Length(1,64), Email()])
    password = PasswordField('Password', validators=[Required()])
    remember_me = BooleanField('Keep me logged in')
    submit = SubmitField('Log In')


class AddSC(FlaskForm):
    # name = StringField('<h4>What is your name?<br/></h4>', [Required()])
    soundcloud = StringField('<h4>SoundCloud<i> URL</h4></i><p></p><br/>', [Required(message="required"),validators.Regexp('^https://soundcloud.com/', message="Please enter a valid account")])
    zipcode = StringField('<h4>Zipcode<br/></h4>', [Required()])
    submit = SubmitField('Submit')

class ZipSearchForm(FlaskForm):
    searchzip = StringField('<h4>Zipcode</h4>', [Required()])
    searchradius = StringField('<h4>Search Mile Radius</h4>', [Required()])
    submit = SubmitField('Submit')

##################################################################

# def get_or_create_user(db_session,fullurl):
#     newuser = db_session.query(User).filter_by(email=email).first()
#     if sc:
#         ##HOW to flash message, prompt continue or register button????
#         return newuser
#     else:
#         sc = SCaccount(email=email)
#         db_session.add(newuser)
#         db_session.commit()
#         return newuser


def get_or_create_zipcode(db_session,sc_zip):
    zipcode = db_session.query(Zipcode).filter_by(sc_zip=sc_zip).first()
    if zipcode:
        ##HOW to flash message, prompt continue or register button????
        return zipcode
    else:
        zipcode = Zipcode(sc_zip=sc_zip)
        db_session.add(zipcode)
        db_session.commit()
        return zipcode

####How to get it to search for matching zip and account???
def get_or_create_scaccount(db_session,sc_url, sc_zip, sc_username):
    sc = db_session.query(SCaccount).filter_by(sc_url=sc_url).first()
    #zipcode = get_or_create_zipcode(db_session, sc_zip)
    if sc:# and zipcode:
        ###### WILL THIS BE IN THE FORMAT OF A LIST?
        # zipcodes = []
        # zipcodes.append(db_session.query(Zipcode).filter_by(sc_zip=sc_zip).first())
        # numzips = len(zipcodes)
        # if numzips > 3:
        #     return sc
        # if numzips <= 3:
        #     ##### will this append it????
        #     sc.zipcodes.append(get_or_create_zipcode (sc_zip=sc_zip))
        # ##HOW to flash message, prompt continue or register button????

        return sc
    else:
        sc = SCaccount(sc_url=sc_url)#, sc_username=sc_username)
        #zipcodes = get_or_create_zipcode(db_session, sc_zip)
        db_session.add(sc)
        db_session.commit()
        return sc




##### Set up Controllers (view functions) #####

## Login routes
@app.route('/login',methods=["GET","POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is not None and user.verify_password(form.password.data):
            login_user(user, form.remember_me.data)
            return redirect(request.args.get('next') or url_for('index'))
        flash('Invalid username or password.')
    return render_template('login.html',form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out')
    return redirect(url_for('index'))

@app.route('/register',methods=["GET","POST"])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(email=form.email.data,username=form.username.data,password=form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('You can now log in!')
        return redirect(url_for('login'))
    return render_template('register.html',form=form)

@app.route('/secret')
@login_required
def secret():
    return "Only authenticated users can do this! Try to log in or contact the site admin."


## Main route

def resolve_profile_tracks_url(username):
    r = requests.get(
        'http://api.soundcloud.com/resolve.json?url=http://soundcloud.com/{}/tracks&client_id={}'.format(username, CLIENTID), allow_redirects=False)

    if 'errors' in json.loads(r.text):
        print ("Cannot find the specified user.")
    else:
        resolved_profile_uri = json.loads(r.text)['location']
        print ('resolved url------', resolved_profile_uri)
        return resolved_profile_uri

def get_profile_tracks(tracks_url):
    r = requests.get(tracks_url)
    return json.loads(r.text)

def get_stream_link(stream_url):
    unique_id = stream_url[21:][:-6]
    return 'http://media.soundcloud.com/stream/{}'.format(unique_id)

@app.route('/')

# def plotpoints():

#     #return pass

# def get_info_for_map():
#     zipcodes = Zipcode.query.all()
#     search = ZipcodeSearchEngine()
#     x = 0
#     y = 0
#     for zipcode in zipcodes:
#         lookupzip = search.by_zipcode(zipcode)
#         lat = lookupzip.Latitude
#         longi = lookupzip.Longitude
#         return ()     


def zipsearch():
    lat = 0
    lng = 0
    simpleForm = ZipSearchForm()
    x = '[{lat: 42.105579399999996, lng: -87.74680710000001},{lat: 42.08057429999999, lng: -87.7320368},{lat: 42.060010999999996, lng: -87.6926257},{lat: 42.0480869, lng: -87.7147986},{lat: 42.0105286, lng: -87.6926257},{lat: 42.0085328, lng: -87.84515270000001},{lat: 41.971106799999994, lng: -87.70248169999998},{lat: 42.2660881, lng: -83.7146001},{lat: 42.2129167, lng: -83.7305392},{lat: 42.2728525, lng: -83.57096399999998},{lat: 42.2253803, lng: -83.3415334},{lat: 39.8086537, lng: -104.8337879},{lat: 39.6999073, lng: -104.93304479999999},{lat: 40.75368539999999, lng: -73.9991637},{lat: 40.7750791, lng: -73.9932872},{lat: 33.96978970000001, lng: -118.24681480000001}]'
    #x = str(x)
    print(x)
    # plotpoints=[]
    # x = '-31.563910'
    # y = '147.154312'
    # plotpoints = [
    #   ]
    labels = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'

    ###ACCESS USER ZIPS

    alllabels = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    allgeo = ['42.105579399999996','-87.74680710000001']

    search = make_response(render_template('zipform.html', form=simpleForm, labels=labels, alllabels=alllabels, allgeo=allgeo, x=x))
    form = ZipSearchForm(request.form)



    return search

#@app.route('/test')
#######https://github.com/ChainsawPolice/soundcloud-page-downloader/blob/master/soundcloud-downloader.py
def my_stream_codes(soundcloud):
    #name = session.get('name')
    username = soundcloud
    tracks_url = resolve_profile_tracks_url(username)
    track_listing = get_profile_tracks(tracks_url)
    songlinks=[]
    for track in track_listing:
        stream_link = get_stream_link(track['stream_url'])
        songlinks.append(re.findall('tracks/(\d+)', stream_link))
    songlinks = list(chain.from_iterable(songlinks))
    print('songlinks----', songlinks)
    return render_template('sclinks.html', songlinks=songlinks) #name=name)

########?????????????########
@app.route('/adduser',methods=['GET', 'POST'])
def adduser():
    form_adduser = AddSC()
        # sc_account = SCaccount(sc_url = soundcloud ,sc_username=sc_username, zipcodes=zipcode)
        # db.session.add(sc_account)
        # db.session.commit()
    #form = AddSC(request.form)



    # soundcloud = simpleForm.soundcloud.data
    # zipcode = simpleForm.zipcode.data

    # search = ZipcodeSearchEngine()
    # lookupzip = search.by_zipcode(zipcode)
    # city = lookupzip.City

    # x = re.match('^https://soundcloud.com/',soundcloud)    

    # if x is None and zipcode is "":
    #     flash('Please fill out the form before submitting!')    
    #     return redirect(url_for('adduser'))
    # elif soundcloud is "":
    #     flash('Please enter your SoundCloud URL!')   
    #     return redirect(url_for('adduser'))        
    # # elif name is "":
    # #     flash('Please enter your name!')   
    # #     return redirect(url_for('adduser'))
    # elif city == None:
    #     flash('Please enter a valid 5-digit zip code')
    #     return redirect(url_for('adduser'))
    # elif x is None:
    #     flash('Please enter a valid SoundCloud URL, beginning with https://soundcloud.com/')
    #     return redirect(url_for('adduser'))


    if form_adduser.validate_on_submit():
        # session['soundcloud'] = form_adduser.soundcloud.data
        # soundcloud=session.get('soundcloud')
        # session['zipcode'] = form_adduser.zipcode.data
        # zipcode=session.get('zipcode')
        sc = str(soundcloud)
        sc_username = sc.replace("https://soundcloud.com/", "")

        get_or_create_scaccount(db_session=db.session, sc_url = form_adduser.soundcloud.data ,sc_zip = form_adduser.zipcode.data, sc_username = sc_username)
        
        return redirect(url_for('addanother', sc_username = sc_username))

    return render_template('addaccount.html', form=form_adduser) 

##??? how to send the username to the next form
@app.route('/addanother',methods=['GET', 'POST'])
def addanother():
    sc_username = 'winandwoo'
    form_adduser = AddSC()
    
    # soundcloud=session.get('soundcloud')
    # sc = str(soundcloud)
    # sc_username = sc.replace("https://soundcloud.com/", "")

    if form_adduser.validate_on_submit():

        # #soundcloud=session.get('soundcloud')
        # sc = str(soundcloud)
        # sc_username = sc.replace("https://soundcloud.com/", "")

        get_or_create_scaccount(db_session=db.session, sc_url = form_adduser.soundcloud.data ,sc_zip = form_adduser.zipcode.data, sc_username = sc_username)
        
        return redirect(url_for('addanother', sc_username = sc_username))

    return render_template('addanother.html', form=form_adduser, sc_username = sc_username) 




#db_session,sc_url, sc_zip, sc_username

########## ????? HOW TO APPEND ZIP CODE IF LESS THAN 3 ON THIS URL?????? #####


##ERRORS
        # sc_account = SCaccount(sc_url = soundcloud ,sc_username=sc_username, zipcodes=zipcode)
        # db.session.add(sc_account)
        # db.session.commit()

        # flash('user added')

        #return render_template('welcome.html', soundcloud = soundcloud, sc_username = sc_username, zipcode=zipcode)





        #get_or_create_scaccount
    
    #return render_template('addaccount.html', form=simpleForm)



        # session['soundcloud'] = form.soundcloud.data
        # soundcloud=session.get('soundcloud')
        
        # # db.session.add(user)

        # session['zipcode'] = form.zipcode.data
        # zipcode=session.get('zipcode')

        # sc = str(soundcloud)
        # sc_username = sc.replace("https://soundcloud.com/", "")
##### ??? FIX SO THAT IT FLASHES ONLY IF THERE ARE MORE THAN 3 ZIP CODES FOR THAT ACCOUNT
    # if simpleForm.validate_on_submit():
    #     sc_account = SCaccount(sc_url = soundcloud ,sc_username=sc_username, zipcodes=zipcode)
    #     db.session.add(sc_account)
    #     db.session.commit()
    #     flash('user added')

        # if db.session.query(SCaccount).filter_by(sc_url=form.soundcloud.data).first(): # If there's already a song with that title, though...nvm. Gotta add something like "(covered by..)"
        #     flash("That SoundCloud user has already been addede")
        # get_or_create_scaccount(db.session,form.soundcloud.data, form.zipcode.data, form.album.data)


    # newuser = make_response(render_template('addaccount.html', form=simpleForm))

    # #     #form = AddSC()
    # #     # form = AddSC(request.form)    
    # return newuser

@app.route('/searchresults', methods = ['GET', 'POST'])
def searchresults():    
    form = ZipSearchForm(request.form)

    searchzip = form.searchzip.data
    searchradius = form.searchradius.data

    search = ZipcodeSearchEngine()
    lookupzip = search.by_zipcode(searchzip)
    city = lookupzip.City
    lat = lookupzip.Latitude
    longi = lookupzip.Longitude

    validradius = searchradius.isdigit()

    if searchzip is "" and searchradius is "":
        flash('Please fill out the form before submitting!') 
        return redirect(url_for('zipsearch'))
    elif searchzip is "":
        flash('Please enter the zip code for the area you would like to search') 
        return redirect(url_for('zipsearch'))
    elif city == None:
        flash('Please enter a valid 5-digit zip code')
        return redirect(url_for('zipsearch'))
    elif searchradius is "":
        flash('Please enter a the mile radius you would like to search around this zip code')
        return redirect(url_for('zipsearch'))
    elif validradius == False:
        flash('Please enter a valid search radius (only type a number)')
        return redirect(url_for('zipsearch')) 
    elif searchradius is "0":
        flash('Please enter a number larger than 1')
        return redirect(url_for('zipsearch'))

    if request.method == 'POST' and form.validate_on_submit():

        session['searchzip'] = form.searchzip.data
        searchzip=session.get('searchzip')

        session['searchradius'] = form.searchradius.data
        searchradius=session.get('searchradius')

        res = search.by_coordinate(lat, longi, radius=int(searchradius), returns=50)

        allzips = []
        for zipcode in res:
            allzips.append(zipcode.Zipcode)
            allzips.append(zipcode.City)
            allzips.append(zipcode.Latitude)
            allzips.append(zipcode.Longitude)            

        return render_template('searchresults.html', searchzip = searchzip, searchradius = searchradius, city = city, allzips = allzips)

# @app.route('/welcome', methods = ['GET', 'POST'])
# def welcome():
#     form = AddSC(request.form)

#     #name = form.name.data
#     soundcloud = form.soundcloud.data
#     zipcode = form.zipcode.data

#     search = ZipcodeSearchEngine()
#     lookupzip = search.by_zipcode(zipcode)
#     city = lookupzip.City

#     x = re.match('^https://soundcloud.com/',soundcloud)    

#     if x is None and zipcode is "":
#         flash('Please fill out the form before submitting!')    
#         return redirect(url_for('signin'))
#     elif soundcloud is "":
#         flash('Please enter your SoundCloud URL!')   
#         return redirect(url_for('signin'))        
#     # elif name is "":
#     #     flash('Please enter your name!')   
#     #     return redirect(url_for('signin'))
#     elif city == None:
#         flash('Please enter a valid 5-digit zip code')
#         return redirect(url_for('signin'))
#     elif x is None:
#         flash('Please enter a valid SoundCloud URL, beginning with https://soundcloud.com/')
#         return redirect(url_for('signin'))


#     if form.validate_on_submit():
#         # name = form.name.data
#         # soundcloud = form.soundcloud.data
#         # session['name'] = form.name.data
#         # name=session.get('name')
#         ## old

#         session['soundcloud'] = form.soundcloud.data
#         soundcloud=session.get('soundcloud')
        
#         # db.session.add(user)


#         session['zipcode'] = form.zipcode.data
#         zipcode=session.get('zipcode')

#         sc = str(soundcloud)
#         sc_username = sc.replace("https://soundcloud.com/", "")

#         return render_template('welcome.html', soundcloud = soundcloud, sc_username = sc_username, zipcode=zipcode)

########## ????? HOW TO APPEND ZIP CODE IF LESS THAN 3 ON THIS URL?????? #####


##ERRORS
        # sc_account = SCaccount(sc_url = soundcloud ,sc_username=sc_username, zipcodes=zipcode)
        # db.session.add(sc_account)
        # db.session.commit()

        # flash('user added')



def codes_for_all_users(searchzip, searchradius):

    search = ZipcodeSearchEngine()
    lookupzip = search.by_zipcode(searchzip)
    city = lookupzip.City
    lat = lookupzip.Latitude
    longi = lookupzip.Longitude

    res = search.by_coordinate(lat, longi, radius=int(searchradius), returns=50)

    allzips = []
    for zipcode in res:
        allzips.append(zipcode.Zipcode)
    
    # allusers = []
    # for x in          

    songs = Song.query.all()

   # my_stream_codes(sc)






@app.route('/myaccount/<sc>')
def myaccount(sc):
    # name = session.get('name')
    # x = sc
    print('sc-----', sc)
    return my_stream_codes(sc)
    #return parseSoundcloud(x)

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
