from importing_modules import *

# Configure base directory of app
basedir = os.path.abspath(os.path.dirname(__file__))

# Application configurations
app = Flask(__name__)
app.debug = True
app.static_folder = 'static'
app.config['SECRET_KEY'] = 'hardtoguessstring'

app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get('DATABASE_URL') or "postgresql://localhost/localbeats1"  # TODO: decide what your new database name will be, and create it in postgresql, before running this new application
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
    searchzip = StringField('<h4>Zipcode</h4>', [Required()])
    searchradius = StringField('<h4>Search Mile Radius</h4>', [Required()])
    submit = SubmitField('Submit')


##### Set up Controllers (view functions) #####

## Main route
client = soundcloud.Client(client_id='6d3KZ6G4o4U0GLCiznHCjbQrT2Ee90cn')
CLIENTID = '6d3KZ6G4o4U0GLCiznHCjbQrT2Ee90cn'

def resolve_profile_tracks_url(username):
    r = requests.get(
        'http://api.soundcloud.com/resolve.json?url=http://soundcloud.com/{}/tracks&client_id={}'.format(username, CLIENTID), allow_redirects=False)

    if 'errors' in json.loads(r.text):
        print ("Cannot find the specified user.")
    else:
        resolved_profile_uri = json.loads(r.text)['location']
        return resolved_profile_uri

def get_profile_tracks(tracks_url):
    r = requests.get(tracks_url)
    return json.loads(r.text)

def get_stream_link(stream_url):
    unique_id = stream_url[21:][:-6]
    return 'http://media.soundcloud.com/stream/{}'.format(unique_id)

@app.route('/')
def zipsearch():
    simpleForm = ZipSearchForm()

    search = make_response(render_template('zipform.html', form=simpleForm))
    form = ZipSearchForm(request.form)

    return search

#@app.route('/test')
#######https://github.com/ChainsawPolice/soundcloud-page-downloader/blob/master/soundcloud-downloader.py
def my_stream_codes(soundcloud):
    name = session.get('name')
    username = soundcloud
    tracks_url = resolve_profile_tracks_url(username)
    track_listing = get_profile_tracks(tracks_url)
    songlinks=[]
    for track in track_listing:
        stream_link = get_stream_link(track['stream_url'])
        songlinks.append(re.findall('tracks/(\d+)', stream_link))
    songlinks = list(chain.from_iterable(songlinks))
    print('songlinks----', songlinks)
    return render_template('sclinks.html', songlinks=songlinks, name=name)


@app.route('/signin')
def signin():
    simpleForm = NameForm()

    newuser = make_response(render_template('addaccount.html', form=simpleForm))
    form = NameForm(request.form)

    return newuser

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

        return render_template('searchresults.html', searchzip = searchzip, searchradius = searchradius, city = city, allzips = allzips)

@app.route('/welcome', methods = ['GET', 'POST'])
def welcome():
    form = NameForm(request.form)

    name = form.name.data
    soundcloud = form.soundcloud.data
    zipcode = form.zipcode.data

    search = ZipcodeSearchEngine()
    lookupzip = search.by_zipcode(zipcode)
    city = lookupzip.City

    x = re.match('^https://soundcloud.com/',soundcloud)    

    if x is None and name is "" and zipcode is "":
        flash('Please fill out the form before submitting!')    
        return redirect(url_for('signin'))
    elif soundcloud is "":
        flash('Please enter your SoundCloud URL!')   
        return redirect(url_for('signin'))        
    elif name is "":
        flash('Please enter your name!')   
        return redirect(url_for('signin'))
    elif city == None:
        flash('Please enter a valid 5-digit zip code')
        return redirect(url_for('signin'))
    elif x is None:
        flash('Please enter a valid SoundCloud URL, beginning with https://soundcloud.com/')
        return redirect(url_for('signin'))


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

# def parseSoundcloud(x):
#     name = session.get('name')
#     soundcloud = session.get('soundcloud')
#     sc = str(soundcloud)
#     sc = sc.replace("https://soundcloud.com/", "")

#     z = str(x)

#     driver = webdriver.PhantomJS()
#     driver.set_window_size(1120, 550)
#     url = 'https://soundcloud.com/'+str(x)+'/tracks'
#     #url = z
#     driver.get(url)
#     html = driver.page_source
#     soup = BeautifulSoup(html, "html.parser")
#     songlinks=[]

#     scheight = .1
#     while scheight < 9.9:
#         driver.execute_script("window.scrollTo(0, document.body.scrollHeight/%s);" % scheight)
#         scheight += .01
#     #scrolls through the entire webpage so that all the songs are found, not just the first 10
#     elem = driver.find_element_by_tag_name('a')
#     for x in driver.find_elements_by_class_name('soundTitle__title'):
#     #finds the link to each song of each user
#         songlinks.append(x.get_attribute('href'))
#     #stores this in a list
#     driver.quit()
#     return render_template('sclinks.html', songlinks=songlinks, name=name, sc=sc)

@app.route('/soundcloud', methods= ['POST','GET'])
def scform():
    return render_template('scform.html')


@app.route('/yoursc')
def yoursc():
    if request.method == 'GET':
        result = request.args
        x = result.get('sc')
        return parseSoundcloud(x)
 

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
