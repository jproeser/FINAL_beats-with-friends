from importing_modules import *

# Configure base directory of app
basedir = os.path.abspath(os.path.dirname(__file__))

# Application configurations
app = Flask(__name__)
app.debug = True
app.static_folder = 'static'
app.config['SECRET_KEY'] = 'hardtoguessstring'

#########HEROKU########
# https://paper.dropbox.com/doc/SI-364-Deploy-Flask-App-on-Heroku-gZyg3VeOIFvNgP41k0FFF

app.config['HEROKU_ON'] = os.environ.get('HEROKU')
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get('DATABASE_URL') or "postgresql://localhost/lb9"



# app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get('DATABASE_URL') or "postgresql://localhost/lb9"  
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


zips_and_accounts = db.Table('zips_and_accounts',db.Column('zipcode_id', db.Integer, db.ForeignKey('zipcodes.id')),db.Column('account_id',db.Integer, db.ForeignKey('scaccounts.id')))


class SCaccount(db.Model):
    __tablename__ = "scaccounts"
    id = db.Column(db.Integer, primary_key=True)
    sc_url = db.Column(db.String(256), unique=True)
    # zipcodes = db.relationship('Zipcode',secondary=zips_and_accounts,backref=db.backref('scaccounts',lazy='dynamic'),lazy='dynamic')
    sc_username = db.Column(db.String(128)) #is this ok even if regex

class Zipcode(db.Model):
    __tablename__ = "zipcodes"
    id = db.Column(db.Integer, primary_key=True)
    sc_zip = db.Column(db.Integer)
    zip_users = db.relationship('SCaccount',secondary=zips_and_accounts,backref=db.backref('zipcodes',lazy='dynamic'),lazy='dynamic')

class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    # username = db.Column(db.String(255), unique=True, index=True)
    email = db.Column(db.String(64), unique=True, index=True)
    sc_zip_id = db.Column(db.Integer, db.ForeignKey("zipcodes.id"))
    sc_username_id = db.Column(db.Integer, db.ForeignKey("scaccounts.id"))
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


##################################################################

class RegistrationForm(FlaskForm):
    email = StringField('Email:', validators=[Required(),Length(1,64),Email()])

    #username = StringField('Username:',validators=[Required(),Length(1,64),Regexp('^[A-Za-z][A-Za-z0-9_.]*$',0,'Usernames must have only letters, numbers, dots or underscores')])
    soundcloud = StringField('<h4>SoundCloud<i> URL</h4></i>', [Required(message="required"),validators.Regexp('^https://soundcloud.com/', message="Please enter a valid account")])
    zipcode = StringField('<h4>Zipcode<br/></h4>', [Required()])

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
    soundcloud = StringField('<h2>SoundCloud<i> URL</i></h2>', validators=[Required()])#, Regexp('^https://soundcloud.com/','Please enter a valid URL')])
    def validate_soundcloud(self,field):
        soundcloud=field.data
        x = re.match('^https://soundcloud.com/',soundcloud)
        if x is None:
            print('aaaaaaa')  

            raise ValidationError('Please enter a valid SoundCloud URL, beginning with https://soundcloud.com/')
            flash ('Please enter a valid SoundCloud URL, beginning with https://soundcloud.com/')
    zipcode = StringField('<h2>Zipcode</h2>', validators=[Required()])
    def validate_zipcode(self,field):
        zipcode=field.data
        search = ZipcodeSearchEngine()
        lookupzip = search.by_zipcode(zipcode)
        city = lookupzip.City        

        if soundcloud is "":
            print('xxxxxx')  
            flash ('Please enter your SoundCloud URL!')

            raise ValidationError('Please enter your SoundCloud URL!')
        
        if city == None:
            print('xxxxxx')  
            raise ValidationError('Please enter a valid 5-digit zip code') 
            flash ('Please enter a valid 5-digit zip code') 
    submit = SubmitField('Add User')

class ZipSearchForm(FlaskForm):
    searchzip = StringField('<h4>Zipcode</h4>', [Required()])
    
    def validate_searchzip(self,field):
        searchzip = field.data

        search = ZipcodeSearchEngine()
        lookupzip = search.by_zipcode(searchzip)
        city = lookupzip.City
        lat = lookupzip.Latitude
        longi = lookupzip.Longitude
        if searchzip is "":
            raise ValidationError('Please enter the zip code for the area you would like to search')
        if city == None:
            raise ValidationError('Please enter a valid 5-digit zip code')
   
    searchradius = StringField('<h4>Search Mile Radius</h4>', [Required()])
    
    def validate_searchradius(self,field):
        searchradius = field.data
        validradius = searchradius.isdigit()
        if searchradius is "":
            raise ValidationError('Please enter a the mile radius you would like to search around this zip code')
        if validradius == False:
            raise ValidationError('Please enter a valid search radius (only type a number)')
        if searchradius is "0":
            raise ValidationError('Please enter a number larger than 1')
    
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

def get_or_create_zipcode(db_session,sc_zip, sc):
    zipcode = db_session.query(Zipcode).filter_by(sc_zip=sc_zip).first()
    if zipcode:

        zipcode.zip_users.append(sc)        
        db_session.add(zipcode)
        db_session.commit()
        ##HOW to flash message, prompt continue or register button????
        return zipcode
    else:
        zipcode = Zipcode(sc_zip=sc_zip)
        zipcode.zip_users.append(sc)
        db_session.add(zipcode)
        db_session.commit()
        return zipcode

####How to get it to search for matching zip and account???
def get_or_create_scaccount(db_session,sc_url, sc_zip, sc_username):
    sc = db_session.query(SCaccount).filter_by(sc_url=sc_url).first()
    if sc:
        # x = []
        # SCaccount.query.filter_by(sc_url=sc_url)
        
        #######z = get_or_create_zipcode(db_session, sc_zip, sc)

        # #### WILL THIS BE IN THE FORMAT OF A LIST?
        # zipcodes = []
        # zipcodes.append(db_session.query(Zipcode).filter_by(sc_zip=sc_zip).first())
        # numzips = len(zipcodes)
        # if numzips > 3:
        #     return sc
        # if numzips <= 3:
        #     ##### will this append it????
        #     sc.zipcodes.append(get_or_create_zipcode (sc_zip=sc_zip))
        # HOW to flash message, prompt continue or register button????

        cities = []
        a = Zipcode.query.all()
        print('\nSC', sc, sc.sc_username)
        for dbzip in a:
            for user in dbzip.zip_users:
                if str(user.sc_username) == str(sc.sc_username):
                    zipcode = dbzip.sc_zip
                    search = ZipcodeSearchEngine()
                    lookupzip = search.by_zipcode(zipcode)
                    city = lookupzip.City
                    x = (city)
                    cities.append(x)
        if len(cities) < 3:
            get_or_create_zipcode(db_session, sc_zip, sc)

        # print('\n\n\n\n\n\nGet or create - cities', cities)
        # print('\n\nlen', len(cities))

        return sc
    else:
        sc = SCaccount(sc_url=sc_url, sc_username=sc_username)
        #zipcodes = get_or_create_zipcode(db_session, sc_zip)
        z = get_or_create_zipcode(db_session, sc_zip, sc)
        print('sc---------', sc.sc_username)
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
            return redirect(request.args.get('next') or url_for('useraccount'))
        flash('Invalid username or password.')
    return render_template('login.html',form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out')
    return redirect(url_for('useraccount'))

@app.route('/register',methods=["GET","POST"])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(email=form.email.data,soundcloud = form.soundcloud.data, zipcode = form.zipcode.data, password=form.password.data)
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
        #print ('resolved url------', resolved_profile_uri)
        return resolved_profile_uri

def resolve_profile(username):
    r = requests.get(
        'http://api.soundcloud.com/resolve.json?url=http://soundcloud.com/{}&client_id={}'.format(username, CLIENTID), allow_redirects=False)
    if 'errors' in json.loads(r.text):
        print ("Cannot find the specified user.")
    else:
        accountinfo = json.loads(r.text)['location']
        #print ('resolved url------', resolved_profile_uri)
        #print('\n soc LINKS', x)
        return accountinfo   

def resolve_social_links(username):
    r = requests.get('https://api.soundcloud.com/users/{}/web-profiles.json?client_id={}'.format(username, CLIENTID), allow_redirects=False)
    if 'errors' in json.loads(r.text):
        print ("Cannot find the specified user.")
    else:
        web_profiles = json.loads(r.text)#['location']
        #print ('resolved url------', resolved_profile_uri)
        #print('\n soc LINKS', x)
        #print('\n WEBPROFILES--------------\n', web_profiles)
        return web_profiles   

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

def get_profile_tracks(tracks_url):
    r = requests.get(tracks_url)
    return json.loads(r.text)

def get_stream_link(stream_url):
    unique_id = stream_url[21:][:-6]
    return 'http://media.soundcloud.com/stream/{}'.format(unique_id)

def get_actual_username(a):
    r = requests.get(a)
    return json.loads(r.text)

def get_web_profiles(a):
    r = requests.get(a)
    return json.loads(r.text)

def get_sc_id(username):
    sc_id = username
    return sc_id

def get_sc_account_id(username):
    a = resolve_profile(username)
    openurl = get_actual_username(a)
    sc_account_id = openurl['id']
    return sc_account_id

def get_sc_account_username(username):
    a = resolve_profile(username)
    openurl = get_actual_username(a)
    sc_account_username = openurl['username']
    return sc_account_username    

def get_sc_account_facebook(username):
    a = resolve_social_links(username)
    #print('\n\n\n\n\n\naaaaaaaa',a)
    for x in a:
        if x['service'] == 'facebook':
            return x['url']

def get_sc_account_twitter(username):
    a = resolve_social_links(username)
    #print('\n\n\n\n\n\naaaaaaaa',a)
    for x in a:
        if x['service'] == 'twitter':
            return x['url']

def get_sc_account_instagram(username):
    a = resolve_social_links(username)
    #print('\n\n\n\n\n\naaaaaaaa',a)
    for x in a:
        if x['service'] == 'instagram':
            return x['url']         

def get_sc_account_soundcloud(username):
    url = 'https://soundcloud.com/' + str(username)
    return url

def get_sc_account_cities(username):
    cities = []
    for dbzip in Zipcode.query.all():
        for user in dbzip.zip_users:
            if str(user.sc_username) == str(username):
                zipcode = dbzip.sc_zip
                search = ZipcodeSearchEngine()
                lookupzip = search.by_zipcode(zipcode)
                city = lookupzip.City
                state = lookupzip.State
                x = (city+', '+state)
                cities.append(x)
    x = ', '.join(cities)
    return x

########

def get_sc_account_songlinks(username):
    tracks_url = resolve_profile_tracks_url(username)
    track_listing = get_profile_tracks(tracks_url)
    #socials = get_social_links(username)
    songlinks=[]
    numsongs = 0
    for track in track_listing:
        stream_link = get_stream_link(track['stream_url'])
        numsongs +=1
        songlinks.append(re.findall('tracks/(\d+)', stream_link))
        #print('SONGLINKS..........', songlinks, user.sc_username)
        #return render_template('zipsearchresults.html', songlinks=songlinks)
    songlinks = list(chain.from_iterable(songlinks))

    # sc_account_id = get_sc_account_id(username)
    # sc_account_username = get_sc_account_username(username)
    # facebook = get_sc_account_facebook(username)
    # twitter = get_sc_account_twitter(username)
    # instagram = get_sc_account_instagram(username)
    # print('|||||||||||||         ',username,'num songs', numsongs, '|||||||| songlinks',songlinks)
    # print('\nID: ', sc_account_id, '\nActual Username: ',sc_account_username)
    # print('\n\nSOCIAL------', '\n',facebook, '\n',twitter, '\n',instagram)
    return songlinks

def get_all_usernames_in_radius(searchzip, searchradius):
    search = ZipcodeSearchEngine()
    lookupzip = search.by_zipcode(searchzip)
    city = lookupzip.City
    lat = lookupzip.Latitude
    longi = lookupzip.Longitude
    res = search.by_coordinate(lat, longi, radius=int(searchradius), returns=50)
    allzips = []
    for zipcode in res:
        allzips.append(zipcode.Zipcode)
    sc_zips_in_radius = []
    sc_users_in_radius = []
    for dbzip in Zipcode.query.all():
        for zipinradius in allzips:
            #print ('searchzip--', zipinradius)
            #print('dbzip----', dbzip.sc_zip)
            if str(zipinradius) == str(dbzip.sc_zip):
            #Matches searched zipcodes with zipcodes in database
                print('-------------------------------MATCH')
                for user in dbzip.zip_users:
                    print ('-------------------------------', user.sc_username)
                    #finds usernames for users in zip search
                    sc_users_in_radius.append(user.sc_username)
    print('\n SOUNDCLOUD USERS IN RADIUS-------\n', sc_users_in_radius) 

    return sc_users_in_radius

    # all_song_codes_in_radius = []
    # for username in sc_users_in_radius:
    #     x = get_all_user_data(username)
    #     all_song_codes_in_radius.append(x)

def create_user_dictionaries(username):
    dictionary_of_users = {}
    if get_sc_account_username(username) != None:
        dictionary_of_users['Username'] = get_sc_account_username(username)
    if get_sc_account_cities(username) != None:
        dictionary_of_users['Cities'] = get_sc_account_cities(username)
    if get_sc_account_soundcloud(username) != None:
        dictionary_of_users['Soundcloud'] = get_sc_account_soundcloud(username)        
    if get_sc_account_facebook(username) != None:
        dictionary_of_users['Facebook'] = get_sc_account_facebook(username)
    if get_sc_account_twitter(username) != None:
        dictionary_of_users['Twitter'] = get_sc_account_twitter(username)
    if get_sc_account_instagram(username) != None:
        dictionary_of_users['Instagram'] = get_sc_account_instagram(username) 
    if get_sc_account_songlinks(username) != None:
        dictionary_of_users['Songs'] = get_sc_account_songlinks(username)
    return dictionary_of_users
######################################################################################################################
######################################################################################################################
######################################################################################################################

@app.route('/',methods=['GET', 'POST'])
def zipsearch():
    lat = 0
    lng = 0
    search_form = ZipSearchForm()


    locations = []
    for dbzip in Zipcode.query.all():
        zipcode = dbzip.sc_zip
        search = ZipcodeSearchEngine()
        lookupzip = search.by_zipcode(zipcode)
        lat = str(lookupzip.Latitude)
        longi = str(lookupzip.Longitude)
        points = '{lat: '+lat+', lng: '+longi+'}'
        locations.append(points)
    locations = str(locations)
    locations = locations.replace('\'', '')
    locations = locations.replace('}, {', '},{')
    x = locations
    
    if search_form.validate_on_submit():
        searchzip = search_form.searchzip.data
        searchradius = search_form.searchradius.data
        return redirect(url_for('searchresults', searchzip = searchzip, searchradius=searchradius))

    return render_template('homepage.html', form=search_form, x=x)

@app.route('/searchresults/<searchzip>-<searchradius>', methods = ['GET', 'POST'])
def searchresults(searchzip, searchradius):    
    
    sc_users_in_radius = get_all_usernames_in_radius(searchzip, searchradius)
    all_song_codes_in_radius = []

    all_user_dictionaries=[]
    for username in sc_users_in_radius:
        user_songlinks = get_sc_account_songlinks(username)
        all_song_codes_in_radius.extend(user_songlinks)

        all_user_dictionaries.append(create_user_dictionaries(username))

    print('\n\n\n ALL USER DICTIONARIES', all_user_dictionaries)
    lenusers = (len(all_user_dictionaries))
    print (lenusers)
    search = ZipcodeSearchEngine()
    lookupzip = search.by_zipcode(searchzip)
    searchcity = lookupzip.City
    return render_template('zipsearchresults.html', sc_users_in_radius=sc_users_in_radius, all_song_codes_in_radius=all_song_codes_in_radius, all_user_dictionaries=all_user_dictionaries, lenusers=lenusers, searchradius=searchradius, searchcity=searchcity)

@app.route('/useraccount')
def useraccount():
    sc_username = 'yo'
    return render_template('useraccount.html', sc_username=sc_username)
#@app.route('/test')
#######https://github.com/ChainsawPolice/soundcloud-page-downloader/blob/master/soundcloud-downloader.py

########?????????????########
@app.route('/adduser',methods=['GET', 'POST'])
def adduser():
    form_adduser = AddSC()

    if form_adduser.validate_on_submit():

        sc = str(form_adduser.soundcloud.data)
        sc_username = sc.replace("https://soundcloud.com/", "")
        #print('**********************',sc_username)

        get_or_create_scaccount(db_session=db.session, sc_url = form_adduser.soundcloud.data ,sc_zip = form_adduser.zipcode.data, sc_username = sc_username)
        flash ('thanks! (delete this later)')
        return redirect(url_for('addanother', sc_username = sc_username))

    return render_template('addaccount.html', form=form_adduser) 


@app.route('/addanother/<sc_username>',methods=['GET', 'POST'])
def addanother(sc_username):
    #print('++++++++', sc_username)
    form_adduser = AddSC()
    
    if form_adduser.validate_on_submit():

        soundcloud=form_adduser.soundcloud.data
        sc = str(soundcloud)
        sc_username = sc.replace("https://soundcloud.com/", "")

        #print('1*********************',sc_username)

        get_or_create_scaccount(db_session=db.session, sc_url = form_adduser.soundcloud.data ,sc_zip = form_adduser.zipcode.data, sc_username = sc_username)
        
        #print('2********************',sc_username)
        
        return redirect(url_for('addanother', sc_username = sc_username))

    return render_template('addanother.html', form=form_adduser, sc_username = sc_username) 


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
