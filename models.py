from flask_login import UserMixin

# Simple user class for session management.
# The username and password are stored in environment variables.
class User(UserMixin):
    def __init__(self, username):
        self.id = 1  # static ID since there's only one user
        self.username = username

# Load the user from config (used by Flask-Login)
def load_user(user_id):
    from config import Config
    return User(Config.AUTH_USERNAME)

