import io
import json
import uuid
from flask import Flask, request, jsonify, redirect, url_for, render_template, flash, session
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo
from werkzeug.security import generate_password_hash, check_password_hash
import firebase_admin
from firebase_admin import credentials, firestore, storage
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import imgkit
from flask_wtf import CSRFProtect
from flask_wtf.csrf import generate_csrf
import os
from dotenv import load_dotenv

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
csrf = CSRFProtect(app)
@app.context_processor
def csrf_context_processor():
    return dict(csrf_token=generate_csrf())
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'  # Update as needed
load_dotenv()
# Initialize Firebase Admin
service_account_path = os.getenv("FIREBASE_SERVICE_ACCOUNT_KEY_PATH")
cred = credentials.Certificate(service_account_path)
firebase_admin.initialize_app(cred, {
    'storageBucket': 'e-template-manager.appspot.com'
})

# Initialize Firestore
db = firestore.client()

# Initialize Cloud Storage
bucket = storage.bucket()

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin):
    def __init__(self, id, email, password):
        self.id = id
        self.email = email
        self.password = password

    @staticmethod
    def get(user_id):
        user_doc = db.collection('users').document(user_id).get()
        if user_doc.exists:
            user_data = user_doc.to_dict()
            return User(user_id, user_data['email'], user_data['password'])
        return None

@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)

def generate_thumbnail(template_html, new_template_id):
    thumbnail_filename = f'thumbnail_{new_template_id}.jpg'
    imgkit_options = {'format': 'jpg'}
    
    try:
        img_data = imgkit.from_string(template_html, False, options=imgkit_options)
        blob = bucket.blob(f'thumbnails/{thumbnail_filename}')
        blob.upload_from_file(io.BytesIO(img_data), content_type='image/jpeg')
        blob.make_public()
        thumbnail_url = blob.public_url
    except Exception as e:
        print(f"Error generating or uploading thumbnail: {e}")
        thumbnail_url = None
    return thumbnail_url

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    submit = SubmitField('Login')

class SignupForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])  # Using StringField for email
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password', message='Passwords must match.')])
    submit = SubmitField('Sign Up') 

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        user = db.collection('users').where('email', '==', email).get()
        if user and check_password_hash(user[0].to_dict()['password'], password):
            user_id = user[0].id
            login_user(User(user_id, email, user[0].to_dict()['password']))
            flash('Login successful.', 'success')
            return redirect(url_for('index'))
        else:
            flash('Login failed. Check your email and/or password.', 'danger')
    return render_template('login.html', form=form)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    form = SignupForm()
    if form.validate_on_submit():
        username = form.username.data
        email = form.email.data
        password = form.password.data
        if password == form.confirm_password.data:
            hashed_password = generate_password_hash(password, method='sha256')
            user_ref = db.collection('users').add({
                'username':username,
                'email': email,
                'password': hashed_password
            })
            flash('Account created successfully. You can now log in.', 'success')
            return redirect(url_for('login'))
        else:
            flash('Passwords do not match.', 'danger')
    return render_template('signup.html', form=form)

@app.route('/upload', methods=['POST'])
@login_required
def upload_template():
    new_template_id = str(uuid.uuid4())
    new_template = {
        "subject_line": request.form['subject_line'],
        "segment": request.form['segment'],
        "template": request.form['template'],
        "date": request.form['date'],
        "added_by": current_user.id
    }
    
    thumbnail_url = generate_thumbnail(new_template['template'], new_template_id)
    new_template['thumbnail'] = thumbnail_url
    db.collection('templates').add(new_template)

    return jsonify({'success': True})

@app.route('/update/<string:template_id>', methods=['POST'])
@login_required
def update_template(template_id):
    template_ref = db.collection('templates').document(template_id)
    template = template_ref.get().to_dict()

    if not template:
        return jsonify({'error': 'Template not found'}), 404
    
    old_thumbnail_url = template.get('thumbnail', '')
    if old_thumbnail_url:
        old_thumbnail_filename = old_thumbnail_url.split('/')[-1]
        old_blob = bucket.blob(f'thumbnails/{old_thumbnail_filename}')
        old_blob.delete()

    thumbnail_url = generate_thumbnail(request.form['template'], template_id)
    updated_template = {
        'subject_line': request.form['subject_line'],
        'segment': request.form['segment'],
        'template': request.form['template'],
        'date': request.form['date'],
        'thumbnail': thumbnail_url
    }

    template_ref.update(updated_template)

    return redirect(url_for('index'))

@app.route('/template/<string:template_id>', methods=['GET'])
def get_template(template_id):
    template_ref = db.collection('templates').document(template_id)
    template = template_ref.get().to_dict()

    if not template:
        return jsonify({'error': 'Template not found'}), 404

    return jsonify({'template': template['template']})

@app.route('/template/<string:template_id>', methods=['DELETE'])
@login_required
def delete_template(template_id):
    template_ref = db.collection('templates').document(template_id)
    template = template_ref.get().to_dict()

    if not template:
        return jsonify({'error': 'Template not found'}), 404

    try:
        thumbnail_path = template['thumbnail'].split('/')[-1]
        blob = bucket.blob(f'thumbnails/{thumbnail_path}')
        blob.delete()

        template_ref.delete()

        return '', 204
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/edit/<string:template_id>', methods=['GET'])
@login_required
def edit_template(template_id):
    template_ref = db.collection('templates').document(template_id)
    template = template_ref.get().to_dict()
    template['id'] = template_id

    if not template:
        return jsonify({'error': 'Template not found'}), 404

    return render_template('edit.html', template=template)

@app.route('/')
@login_required
def index():
    templates = load_templates()
    users = load_users()
    date_filter = request.args.get('date')
    segment_filter = request.args.get('segment')

    if date_filter and segment_filter:
        # Apply both filters
        templates = [template for template in templates if template['date'] == date_filter and template['segment'] == segment_filter]
    elif date_filter:
        # Apply only date filter
        templates = [template for template in templates if template['date'] == date_filter]
    elif segment_filter:
        # Apply only segment filter
        templates = [template for template in templates if template['segment'] == segment_filter]

    csrf_token = generate_csrf()

    return render_template('index.html', templates=templates, users=users, csrf_token=csrf_token)

def get_username(user_id):
    user_doc = db.collection('users').document(user_id).get()
    if user_doc.exists:
        return user_doc.to_dict().get('username', '')
    return ''

def load_users():
    users=[]
    docs=db.collection('users').stream()
    for doc in docs:
        user= doc.to_dict()
        user['id'] = doc.id
        users.append(user)
    return users


def load_templates():
    templates = []
    docs = db.collection('templates').stream()
    for doc in docs:
        template = doc.to_dict()
        template['id'] = doc.id
        templates.append(template)
    return templates

@app.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))



if __name__ == '__main__':
    app.run(debug=True)
