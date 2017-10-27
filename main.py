from flask import Flask, redirect, render_template, request, flash, url_for, session
from flask_sqlalchemy import SQLAlchemy
import jinja2
from hashutils import make_pw_hash, check_pw_hash

app = Flask(__name__)
app.config['DEBUG'] = True

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://blogz:blogz@localhost:8889/blogz'
app.config['SQLALCHEMY_ECHO'] = True
db = SQLAlchemy(app)
app.secret_key = "XXXsecretkeyXXX"

class User(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(256))
    pw_hash = db.Column(db.String(256))
    blogs = db.relationship('Blog', backref='owner')

    def __init__(self,username,password):
        self.username = username
        self.pw_hash = make_pw_hash(password)


class Blog(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120))
    body = db.Column(db.String(256))
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __init__(self, title, body, owner):
        self.title = title
        self.body = body
        self.owner = owner

#Check if a user is logged in first:
@app.before_request
def require_login():
    #loggeduser = session.get('user')
    #if loggeduser:
        #loggeduserobj = User.query.filter_by(username=loggeduser).first()
    not_allowed = ['newpost', 'logout']
    if request.endpoint in not_allowed and 'user' not in session:
        return redirect('/login')


# Routes:
# 1. / (redirects to /home)
# 2. /blog (displays all blog posts)
# 3. /newpost (new post page, submits new post to databse and redirects to single post)
# 4. /singlepost (renders page for a single post when created, or selected from the main page)
# 5. /deletepost (called from single post page, removes from database and redirects)
# 6. /login (logs an existing user into the session)
# 7. /signup (put a new user into the database and redirects to newpost page)
# 8. /logout (deletes the session, redirects to log-in)

@app.route('/')
def root():
    return redirect('/home')

@app.route('/home', methods=['GET'])
def index():

    all_users = User.query.all()
    return render_template('index.html',all_users=all_users)

@app.route('/blog', methods=['GET'])
def blog_mainpage():

    loggeduser = session.get('user','')
    loggeduserobj = User.query.filter_by(username=loggeduser).first()

    if request.args.get('userid') != None:
        userid = request.args.get('userid')
        user = User.query.filter_by(id=userid).first()
        get_posts = Blog.query.filter_by(owner_id=user.id).all()
    else:
        get_posts = Blog.query.all()

    return render_template("main_page.html",all_posts=get_posts, loggeduser=loggeduser, loggeduserobj=loggeduserobj)

@app.route('/newpost', methods=['GET', 'POST'])
def newpost():

    loggeduser = session.get('user','')
    loggeduserobj = User.query.filter_by(username=loggeduser).first()

    if request.method == 'GET':
        return render_template("new_post.html", loggeduser=loggeduser, loggeduserobj=loggeduserobj)

    if request.method == 'POST':
        title = str(request.form['title'])
        body = str(request.form['body'])

        if title == '' or body == '' or title == ' ' or body == ' ':
            flash("need a title and body u scrub lol")
            return render_template("new_post.html",title=title,body=body, loggeduser=loggeduser, loggeduserobj=loggeduserobj)
        
        owner = User.query.filter_by(username=session['user']).first()
        blogpost = Blog(title, body, owner)
        db.session.add(blogpost)
        db.session.commit()

        url = '/singlepost?id=' + str(blogpost.id)

        return redirect(url)

@app.route('/singlepost', methods=['GET'])
def blogpost():
    if request.method == 'GET':
        idnum = request.args.get("id")
        if idnum:
            post = Blog.query.filter_by(id=idnum).all()
            return render_template("single_post.html",the_post=post)
        
@app.route('/deletepost', methods=['POST'])
def delete():
    post_id = int(request.form['post-id'])
    post_to_del = Blog.query.filter_by(id=post_id).first()

    db.session.delete(post_to_del)
    db.session.commit()

    flash("Blog post deleted")
    return redirect("/")

@app.route('/login', methods=['POST','GET'])
def login():

    if request.method == 'GET':
        return render_template("login.html")

    if request.method == 'POST':

        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        #if either is blank
        if not username or not password:
            flash("OMG STOP LEAVING SHIT BLANK, SERIOUSLY")
            return render_template('login.html')

        #as long as everything is clear, log in and redirect to new post
        if user and check_pw_hash(password, user.pw_hash):
            flash("Logged in as {0}".format(user.username))
            session['user'] = username
            return redirect('/newpost')

        #check if exists        
        elif not user:
            flash("User doesnt exist")
            return render_template("login.html")

        #check is passwords match
        elif not check_pw_hash(password, user.pw_hash):
            flash('Wrong password')
            return render_template('login.html')
        
        else:
            return render_template('login.html')

@app.route('/signup', methods=['POST', 'GET'])
def signup():

    if request.method == 'GET':
        return render_template("signup.html")

    if request.method == 'POST':

        username = str(request.form['username'])
        password = str(request.form['password'])
        verifypassword = str(request.form['verifypassword'])
        existing_user = User.query.filter_by(username=username).first()
        usererror = False
        passerror = False
        verifypasserror = False

        if existing_user:
            flash("User already exists")
            return render_template('signup.html')
        
        #Verify new data:
            #If any are blank, that is priority, so redirect immediately if any are blank:
        if not username or not password or not verifypassword:
            flash("Cant leave anything blank, you nonce, lol...")
            return render_template('signup.html')
            #If not blank, verify actual:
        if len(username) < 4 or " " in username:
            usererror = True
            flash("Username must have 4 or more characters and no spaces")
        if len(password) < 4 or " " in password:
            passerror = True
            flash("Password must have 4 or more characters and no spaces")
        if verifypassword != password:
            verifypasserror = True
            flash("Passwords must match")
        if usererror or passerror or verifypasserror:
            return render_template('signup.html')
        
        else:
            new_user = User(username, password)
            db.session.add(new_user)
            db.session.commit()
            session['user'] = username

            flash("Logged in as {0}! Time to create your first post lmao.".format(username))
            return redirect('/newpost')

@app.route('/logout')
def logout():
    del session['user']
    flash("You were logged out")
    return redirect('/login')


if __name__ == '__main__':
    app.run()