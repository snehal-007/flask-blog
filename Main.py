from flask import Flask, render_template, request, session, redirect, flash
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
import json
from datetime import datetime
import os
from werkzeug import secure_filename
import math


# Open json file 
with open('config.json','r') as c:
    params = json.load(c)["params"]


local_server = True  


# Main Server Method
app = Flask(__name__)

# Secret Key
app.secret_key = 'super secret key'

# Mail Send from Gmail
app.config.update(

    MAIL_SERVER = 'smtp.gmail.com',
    MAIL_PORT = '465',
    MAIL_USE_SSL = True,
    MAIL_USERNAME = params['gmail-user'],
    MAIL_PASSWORD = params['gmail-password']
)
mail = Mail(app)




# SQL Server Linking
if(local_server):
    app.config['SQLALCHEMY_DATABASE_URI'] = params['local_uri']

else:
    app.config['SQLALCHEMY_DATABASE_URI'] = params['prod_uri']

db = SQLAlchemy(app)

# app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:@localhost/ai_works'
# db = SQLAlchemy(app)




# Fetching Main Contents From Database
class Contacts(db.Model):
    '''sno,name,phon_no,mes,email,date '''

    sno = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    phone_num = db.Column(db.String(12), nullable=False)
    mes = db.Column(db.String(120), nullable=False)
    date = db.Column(db.String(12), nullable=True)
    email = db.Column(db.String(20), nullable=False)

class Posts(db.Model):
    '''sno,name,phon_no,mes,email,date,img_file '''

    sno = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), nullable=False)
    slug = db.Column(db.String(21), nullable=False)
    content = db.Column(db.String(120), nullable=False)
    date = db.Column(db.String(12), nullable=True)
    img_file = db.Column(db.String(12), nullable=True)
    tagline = db.Column(db.String(80), nullable=False)




# Template Scripting And Endpoints 
# Index page
@app.route("/")
def home():
    # Massage Flashing
    flash("Subscribe Artificial Android","success")
    flash("We have a Many Opportunities of Developing AI","danger")
    # Post showing in index page
    posts = Posts.query.filter_by().all()                     # all posts        
    
    # pagination next and previous
    last = math.ceil(len(posts)/int(params['no_of_posts']))    # Last page logic
    page = request.args.get('page')
    if(not str(page).isnumeric()):
        page = 1
    page = int(page)

    # Post slicing how many posts showing in one page
    posts = posts[(page-1)*int(params['no_of_posts']):(page-1)*int(params['no_of_posts'])+ int(params['no_of_posts'])] 

    

    # Pagination Logic
    # First page
    if (page==1):
        prev='#'
        next = '/?page='+str(page+1)
    # Last page
    elif(page==last):
        prev = "/?page="+str(page-1)
        next='#'

    # Middel pages
    else:
        prev = "/?page="+str(page-1) 
        next = "/?page="+str(page+1)        

    return render_template('index.html',params=params,posts=posts,prev=prev,next=next)


@app.route("/contact",methods=['GET','POST'])
def contact():
    #  Users contacts posts fetching Users entered a detailed
    if(request.method == 'POST'):
        ''' Add Entry to database '''

        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        message = request.form.get('message')
        entry = Contacts(name=name,phone_num=phone,mes=message,date=datetime.now(),email=email)
        db.session.add(entry)
        db.session.commit()

        #send mail
        mail.send_message('New message from ' + name,sender=email,recipients=[params['gmail-user']],body=message + "\n" + phone)
        flash("Thanks for submitting your Details.We will get back soon","success")
    return render_template('contact.html',params=params)


# User/Admin Acsess Logging
@app.route("/dashboard",methods=['GET','POST'])
def dashboard():
    # if already user in session 
    if ('user' in session and session['user'] == params['admin_user']):
        posts = Posts.query.all()
        return render_template('dashboard.html',params=params,posts=posts)


    # Logging panel
    if request.method == 'POST':
        username = request.form.get('uname')
        userpass = request.form.get('pass')
        if (username == params['admin_user'] and userpass == params['admin_password']):
            # Set the session variable
            session['user'] = username
            posts = Posts.query.all()
            return render_template('dashboard.html',params=params,posts=posts)

    else:

        return render_template('login.html',params=params)

    return render_template('login.html',params=params) 

#Logout
@app.route("/logout")
def logout():
    session.pop('user')
    return redirect('/dashboard')



# Slug post
@app.route("/post/<string:post_slug>",methods=['GET'])
def post_route(post_slug):
    post = Posts.query.filter_by(slug=post_slug).first()
    return render_template('post.html',params=params,post=post)


#new post
@app.route("/edit/<string:sno>",methods=['GET','POST'])
def new_Post(sno):
    if ('user' in session and session['user'] == params['admin_user']):         # Already loggrd in
        # Users enter a post detail and send to database
        if request.method == 'POST':
            box_title = request.form.get('title')
            tline = request.form.get('tline')
            slug = request.form.get('slug')
            content = request.form.get('content')
            img_file = request.form.get('img_file')
            date = datetime.now()

            # New post
            if sno=='0':
                post = Posts(title=box_title,slug=slug,content=content,tagline=tline,img_file=img_file,date=date)
                db.session.add(post)
                db.session.commit()
                flash("Your post Added Successfully","success") 


            #Edit post
        #     else:
        #         post = Posts.query.filter_by(sno=sno).first()
        #         post.title = box_title
        #         post.slug = slug
        #         post.content = content
        #         post.tagline = tline
        #         post.img_file = img_file
        #         post.date = date
        #         db.session.commit()       
        #         return redirect('/edit/'+sno)                   # redirect currunt page

        # post = Posts.query.filter_by(sno=sno).first()
        
        return render_template('edit.html',params=params,sno=sno)    


# Edit post
@app.route("/edit2/<string:sno>",methods=['GET','POST'])
def edit2(sno):
    if ('user' in session and session['user'] == params['admin_user']):         # Already loggrd in
        # Users enter a post detail and send to database
        if request.method == 'POST':
            box_title = request.form.get('title')
            tline = request.form.get('tline')
            slug = request.form.get('slug')
            content = request.form.get('content')
            img_file = request.form.get('img_file')
            date = datetime.now()

            # New post dead content here
            if sno=='#':
                post = Posts(title=box_title,slug=slug,content=content,tagline=tline,img_file=img_file,date=date)
                db.session.add(post)
                db.session.commit() 


            #Edit post
            else:
                post = Posts.query.filter_by(sno=sno).first()
                post.title = box_title
                post.slug = slug
                post.content = content
                post.tagline = tline
                post.img_file = img_file
                post.date = date
                db.session.commit()       
                flash("Your post Edited Successfully","success")
                return redirect('/edit2/'+sno)                   # redirect currunt page

        post = Posts.query.filter_by(sno=sno).first()
        
        return render_template('edit2.html',params=params,post=post)   


# Uploader
@app.route("/uploader",methods = ['GET','POST'])
def uploader():

    if ('user' in session and session['user'] == params['admin_user']):

        if (request.method == 'POST'):

            f = request.files['file1']
            # f.save(f.filename)
            f.save(os.path.join(params['upload_location'], f.filename))

            return "Upload successfully"


# Delete post
@app.route("/delete/<string:sno>",methods=['GET','POST'])
def delete(sno):
    if ('user' in session and session['user'] == params['admin_user']):
        post = Posts.query.filter_by(sno=sno).first()
        db.session.delete(post)
        db.session.commit()
    return redirect('/dashboard')




@app.route("/about")
def about():

    return render_template('about.html',params=params)



app.run(debug=True)

