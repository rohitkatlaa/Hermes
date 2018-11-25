from flask import render_template, flash, redirect, url_for, request
import secrets
import os
from PIL import Image
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.urls import url_parse
from app import app, database
from app.forms import LoginForm, RegistrationForm
from app.models import User
from datetime import datetime
from app.forms import EditProfileForm
from app.forms import PostForm
from app.models import Post
from app.forms import MessageForm
from app.models import Message
from app.models import Likes
from app.models import No_of_users
from app.check_email import is_valid_email_id

@app.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        database.session.commit()

def save_picture(form_picture):
    random_hex=secrets.token_hex(8)
    _,f_ext=os.path.splitext(form_picture.filename)
    picture_fn=random_hex + f_ext
    picture_path=os.path.join(app.root_path,'static/posts_image',picture_fn)
    output_size=(125,125)
    i=Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)
    picture_path2=os.path.join('static/posts_image',picture_fn)
    return picture_path2

def save_picture2(form_picture):
    random_hex=secrets.token_hex(8)
    _,f_ext=os.path.splitext(form_picture.filename)
    picture_fn=random_hex + f_ext
    picture_path=os.path.join(app.root_path,'static/posts_image',picture_fn)
    output_size=(200,200)
    i=Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)
    picture_path2=os.path.join('static/posts_image',picture_fn)
    return picture_path2


@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
@login_required
def index():
    form = PostForm()
    if form.validate_on_submit():
        if form.picture.data:
            picture_file=save_picture(form.picture.data)
            post = Post(body=form.post.data, author=current_user,image_file=picture_file,no_of_likes=0)
        else:
            post = Post(body=form.post.data, author=current_user,image_file=form.picture.data,no_of_likes=0)
        database.session.add(post)
        database.session.commit()
        flash('Your post is now live!')
        return redirect(url_for('index'))
    posts=current_user.posts.order_by(Post.timestamp.desc())
    return render_template('index.html', title='Home', posts=posts,form=form,user=current_user)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')
            user1 = No_of_users.query.filter_by(user_id=user.id).first()
            user1.online=1
            database.session.commit()
        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form)


@app.route('/logout')
def logout():
    user = No_of_users.query.filter_by(user_id=current_user.id).first()
    user.online=0
    database.session.commit()
    logout_user()
    return redirect(url_for('index'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm() 
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data
)
        user.set_password(form.password.data)
        database.session.add(user)
        database.session.commit()
        num_user=No_of_users(author=user,online=1)
        database.session.add(num_user)
        database.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)

@app.route('/<username>')
@login_required
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    posts=user.posts.all()
    return render_template('user.html', user=user, posts=posts)

@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.username)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        if form.picture.data:
            current_user.profile_pic=save_picture2(form.picture.data)
        database.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('edit_profile'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', title='Edit Profile',form=form)

@app.route('/explore')
@login_required
def explore():
    posts = Post.query.order_by(Post.timestamp.desc()).all()
    return render_template('index.html', title='Explore', posts=posts,user=current_user)


@app.route('/send_message/<recipient>', methods=['GET', 'POST'])
@login_required
def send_message(recipient):
    user = User.query.filter_by(username=recipient).first_or_404()
    form = MessageForm()
    if form.validate_on_submit():
        msg = Message(author=current_user, recipient=user,
                      body=form.message.data)
        database.session.add(msg)
        database.session.commit()
        flash('Your message has been sent.')
        return redirect(url_for('user', username=recipient))
    return render_template('send_message.html', title='Send Message',
                           form=form, recipient=recipient)

@app.route('/messages_recieved')
@login_required
def messages_recieved():
    current_user.last_message_read_time = datetime.utcnow()
    database.session.commit()
    messages = current_user.messages_received.order_by(Message.timestamp.desc())
    return render_template('messages_recieved.html', messages=messages)

@app.route('/messages_sent')
@login_required
def messages_sent():
    current_user.last_message_read_time = datetime.utcnow()
    database.session.commit()
    messages = current_user.messages_sent.order_by(Message.timestamp.desc())
    return render_template('messages_sent.html', messages=messages)

@app.route('/follow/<username>')
@login_required
def follow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('User {} not found.'.format(username))
        return redirect(url_for('index'))
    if user == current_user:
        flash('You cannot follow yourself!')
        return redirect(url_for('user', username=username))
    current_user.follow(user)
    database.session.commit()
    flash('You are following {}!'.format(username))
    return redirect(url_for('user', username=username))

@app.route('/unfollow/<username>')
@login_required
def unfollow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('User {} not found.'.format(username))
        return redirect(url_for('index'))
    if user == current_user:
        flash('You cannot unfollow yourself!')
        return redirect(url_for('user', username=username))
    current_user.unfollow(user)
    database.session.commit()
    flash('You are not following {}.'.format(username))
    return redirect(url_for('user', username=username))

@app.route('/follower_messages')
@login_required
def follower_messages():
    current_user.last_message_read_time = datetime.utcnow()
    database.session.commit()
    messages=current_user.followed_posts()
    return render_template('messages_sent.html', messages=messages,user=current_user)

@app.route('/likes/<post_id>')
@login_required
def likes(post_id):
    #post_id=17
    post = Post.query.filter_by(id=post_id).first()
    if post is None:
        flash('Post {} not found.'.format(post))
        return redirect(url_for('index'))
    lik = Likes(author=current_user, recipient=post)
    a=post.no_of_likes
    a=a+1
    post.no_of_likes=a
    database.session.add(lik)
    database.session.commit()
    flash('You liked a post')
    return redirect(url_for('index'))

@app.route('/liked_posts')
@login_required
def liked_posts():
    current_user.last_message_read_time = datetime.utcnow()
    database.session.commit()
    messages=current_user.liked_posts()
    return render_template('messages_sent.html', messages=messages,user=current_user)

@app.route('/most_liked')
@login_required
def most_liked():
    posts = Post.query.order_by(Post.no_of_likes.desc())
    return render_template('most_liked.html', title='most_liked', posts=posts,user=current_user)

@app.route('/online_users')
@login_required
def online_users():
    users=No_of_users.query.filter_by(online=1).all()
    return render_template('online_users.html',users=users)
