from datetime import datetime
from app import database, login
from flask_login import UserMixin
from hashlib import md5
from app.password3 import encrypt,decrypt,is_correct


followers = database.Table('followers',
    database.Column('follower_id', database.Integer, database.ForeignKey('user.id')),
    database.Column('followed_id', database.Integer, database.ForeignKey('user.id'))
)

class User(UserMixin, database.Model):
    id = database.Column(database.Integer, primary_key=True)
    username = database.Column(database.String(50), index=True, unique=True)
    email = database.Column(database.String(100), index=True, unique=True)
    password_hash = database.Column(database.String(50))
    posts = database.relationship('Post', backref='author', lazy='dynamic')
    about_me = database.Column(database.String(200))
    last_seen = database.Column(database.DateTime, default=datetime.utcnow)
    messages_sent = database.relationship('Message',
                                    foreign_keys='Message.sender_id',
                                    backref='author', lazy='dynamic')
    messages_received = database.relationship('Message',
                                        foreign_keys='Message.recipient_id',
                                        backref='recipient', lazy='dynamic')
    last_message_read_time = database.Column(database.DateTime)
    profile_pic = database.Column(database.String(60),nullable=True)


    followed = database.relationship('User', secondary=followers,primaryjoin=(followers.c.follower_id == id),secondaryjoin=(followers.c.followed_id == id),backref=database.backref('followers', lazy='dynamic'), lazy='dynamic')
    likes_sent= database.relationship('Likes',foreign_keys='Likes.likesSent_id',backref='author', lazy='dynamic')
    no_of_users = database.relationship('No_of_users', backref='author', lazy='dynamic')

    def new_messages(self):
        last_read_time = self.last_message_read_time or datetime(1900, 1, 1)
        return Message.query.filter_by(recipient=self).filter(
            Message.timestamp > last_read_time).count()

    def __repr__(self):
        return '<User {}>'.format(self.username)

    def set_password(self, password):
    	self.password_hash=encrypt(password)
        #self.password_hash = generate_password_hash(password)

    def check_password(self, password):
    	return is_correct(password,self.password_hash)
        #return check_password_hash(self.password_hash, password)

    def avatar(self,a):
        if a is 256:
            return 'static/posts_image/profile_pic.png'
        else:
            return 'static/posts_image/profile_pic2.png'
    def profile_picture(self):
        if self.profile_pic:
            return self.profile_pic
        else:
            return None
    def follow(self, user):
        if not self.is_following(user):
            self.followed.append(user)

    def unfollow(self, user):
        if self.is_following(user):
            self.followed.remove(user)

    def is_following(self, user):
        return self.followed.filter(
            followers.c.followed_id == user.id).count() > 0
    def followed_posts(self):
        followed = Post.query.join(followers, (followers.c.followed_id == Post.user_id)).filter(followers.c.follower_id == self.id)
        own = Post.query.filter_by(user_id=self.id)
        return followed.union(own).order_by(Post.timestamp.desc())

    def liked_posts(self):
        liked = Post.query.join(Likes, (Likes.likesRecieved_id == Post.id)).filter(Likes.likesSent_id == self.id)
        return liked



@login.user_loader
def load_user(id):
    return User.query.get(int(id))


class Post(database.Model):
    id = database.Column(database.Integer, primary_key=True)
    body = database.Column(database.String(200))
    timestamp = database.Column(database.DateTime, index=True, default=datetime.utcnow)
    user_id = database.Column(database.Integer, database.ForeignKey('user.id'))
    likes_received = database.relationship('Likes',
                                        foreign_keys='Likes.likesRecieved_id',
                                        backref='recipient', lazy='dynamic')
    image_file = database.Column(database.String(60),nullable=True)
    no_of_likes = database.Column(database.Integer)
    def is_liking(self,user):
        return self.likes_received.filter(Likes.likesSent_id==user.id).count() > 0

    def __repr__(self):
        return '<Post {}>'.format(self.body)
    def return_id(self):
        return self.id

class Message(database.Model):
    id = database.Column(database.Integer, primary_key=True)
    sender_id = database.Column(database.Integer, database.ForeignKey('user.id'))
    recipient_id = database.Column(database.Integer, database.ForeignKey('user.id'))
    body = database.Column(database.String(200))
    timestamp = database.Column(database.DateTime, index=True, default=datetime.utcnow)

    def __repr__(self):
        return '<Message {}>'.format(self.body)


class Likes(database.Model):
    id = database.Column(database.Integer, primary_key=True)
    likesSent_id = database.Column(database.Integer, database.ForeignKey('user.id'))
    likesRecieved_id = database.Column(database.Integer, database.ForeignKey('post.id'))
    timestamp = database.Column(database.DateTime, index=True, default=datetime.utcnow)

class No_of_users(database.Model):
    id = database.Column(database.Integer, primary_key=True)
    user_id = database.Column(database.Integer, database.ForeignKey('user.id'))
    online=database.Column(database.Integer)
    
