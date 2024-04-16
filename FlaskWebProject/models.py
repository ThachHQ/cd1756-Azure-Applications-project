from datetime import datetime
from FlaskWebProject import app, db, login
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from azure.storage.blob import BlobServiceClient
import string, random
from werkzeug.utils import secure_filename
from flask import flash

blob_container = app.config['BLOB_CONTAINER']
blob_account_url = 'https://'+ app.config['BLOB_ACCOUNT']  + '.blob.core.windows.net'
blob_service = BlobServiceClient(account_url=blob_account_url, credential=app.config['BLOB_STORAGE_KEY'])

def id_generator(size=32, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    password_hash = db.Column(db.String(128))

    def __repr__(self):
        return '<User {}>'.format(self.username)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

@login.user_loader
def load_user(id):
    return User.query.get(int(id))

class Post(db.Model):
    __tablename__ = 'posts'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150))
    subtitle = db.Column(db.String(150))
    author = db.Column(db.String(75))
    body = db.Column(db.String(800))
    image_path = db.Column(db.String(100))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    def __repr__(self):
        return '<Post {}>'.format(self.body)

    def save_changes(self, form, file, userId, new=False):
        self.title = form.title.data
        self.subtitle = form.subtitle.data
        self.author = form.author.data
        self.body = form.body.data
        self.user_id = userId

        if file:
            filename = secure_filename(file.filename);
            fileextension = filename.rsplit('.',1)[1];
            Randomfilename = id_generator();
            filename = Randomfilename + '.' + fileextension;
            try:
                new_img = blob_service.get_blob_client(container=blob_container,blob=filename)
                new_img.upload_blob(file.read())
                if(self.image_path):
                    old_img = blob_service.get_blob_client(container=blob_container,blob=self.image_path)
                    old_img.delete_blob()
            except Exception as e:
                flash(Exception)
                app.logger.error(e)
            self.image_path =  filename
        if new:
            db.session.add(self)
        db.session.commit()
        app.logger.info('Edit Post success!')

    def delete(self):
        try:
            if(self.image_path):
                img = blob_service.get_blob_client(container=blob_container,blob=self.image_path)
                img.delete_blob()
        except Exception as e:
            flash(Exception)
            app.logger.error(e)
        db.session.delete(self)
        db.session.commit()
        app.logger.info('Delete Post success!')