from flask import Flask, render_template, request, redirect, url_for, flash, g
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import or_
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:toor@localhost:5432/personal_notes_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'none'
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)

class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    date_created = db.Column(db.DateTime, default=db.func.current_timestamp())
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    user = db.relationship('User', backref=db.backref('notes', lazy=True))


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.before_request
def before_request():
    g.first_request = not hasattr(g, 'first_request')
    if g.first_request:
        db.create_all()
        if not User.query.filter_by(username='admin').first():
            new_user = User(username='admin', password='password')
            db.session.add(new_user)
            db.session.commit()

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and user.password == password:
            login_user(user)
            return redirect(url_for('index'))
        else:
            flash('Login failed. Check your username and/or password')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    notes = Note.query.filter_by(user_id=current_user.id).order_by(Note.date_created.desc()).all()
    return render_template('index.html', notes=notes)

@app.route('/add', methods=['POST'])
@login_required
def add_note():
    title = request.form.get('title')
    content = request.form.get('content')
    new_note = Note(title=title, content=content, user_id=current_user.id)
    db.session.add(new_note)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/delete/<int:id>')
@login_required
def delete(id):
    note = Note.query.get(id)
    if note:
        db.session.delete(note)
        db.session.commit()
    return redirect(url_for('index'))

@app.route('/update/<int:id>', methods=['GET', 'POST'])
@login_required
def update(id):
    note = Note.query.get(id)
    if request.method == 'POST':
        note.title = request.form.get('title')
        note.content = request.form.get('content')
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('update.html', note=note)

@app.route('/search')
@login_required
def search():
    query = request.args.get('query')
    notes = Note.query.filter(
        (Note.content.ilike(f'%{query}%') | Note.title.ilike(f'%{query}%'))
    ).filter_by(user_id=current_user.id).all()
    return render_template('index.html', notes=notes)

if __name__ == '__main__':
    app.run(debug=True)
