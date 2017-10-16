from flask import Flask, redirect, render_template, request, flash, url_for
from flask_sqlalchemy import SQLAlchemy
import jinja2

app = Flask(__name__)
app.config['DEBUG'] = True

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://build-a-blog:buildablog@localhost:8889/build-a-blog'
app.config['SQLALCHEMY_ECHO'] = True
db = SQLAlchemy(app)
app.secret_key = "XXXsecretkeyXXX"

class Blog(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120))
    body = db.Column(db.String(256))

    def __init__(self, title, body):
        self.title = title
        self.body = body


@app.route('/', methods=['GET'])
def index():
    return redirect('/blog')

@app.route('/blog', methods=['GET'])
def blog_mainpage():

    idnum = request.args.get("id")
    if idnum:
        post = Blog.query.filter_by(id=idnum).all()
        return render_template("main_page.html",all_posts=post)

    all_posts = Blog.query.all()
    return render_template("main_page.html",all_posts=all_posts)

@app.route('/newpost', methods=['GET', 'POST'])
def newpost():

    if request.method == 'GET':
        return render_template("new_post.html")

    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']

        if title == '' or body == '':
            flash("need a title and body u scrub lol")
            return render_template("new_post.html",title=title,body=body)

        blogpost = Blog(title, body)
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


if __name__ == '__main__':
    app.run()