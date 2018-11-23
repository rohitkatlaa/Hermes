from app import app, db
from app.models import User, Post
#from app.password_encrypt import encrypt,is_correct

@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'Post': Post}
