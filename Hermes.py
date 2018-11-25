from app import app, database
from app.models import User, Post


@app.shell_context_processor
def make_shell_context():
    return {'database': database, 'User': User, 'Post': Post}
