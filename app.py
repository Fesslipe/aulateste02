import os
from flask import Flask, render_template, session, redirect, url_for
from flask_bootstrap import Bootstrap
from flask_moment import Moment
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.config['SECRET_KEY'] = 'hard to guess string'
app.config['SQLALCHEMY_DATABASE_URI'] =\
    'sqlite:///' + os.path.join(basedir, 'data.sqlite')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

bootstrap = Bootstrap(app)
moment = Moment(app)
db = SQLAlchemy(app)
migrate = Migrate(app, db)


class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    users = db.relationship('User', backref='role', lazy='dynamic')

    def __repr__(self):
        return '<Role %r>' % self.name


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, index=True)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))

    def __repr__(self):
        return '<User %r>' % self.username


class NameForm(FlaskForm):
    name = StringField('What is your name?', validators=[DataRequired()])
    submit = SubmitField('Submit')


@app.shell_context_processor
def make_shell_context():
    return dict(db=db, User=User, Role=Role)


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500


@app.route('/', methods=['GET', 'POST'])
def index():
    form = NameForm()
    if form.validate_on_submit():
        # Obtenha o nome do usuário do formulário
        username = form.name.data

        # Verifique se o usuário já existe no banco de dados
        user = User.query.filter_by(username=username).first()

        if user is None:
            # Se o usuário não existir, crie um novo usuário
            user = User(username=username)

            # Defina a role do novo usuário como "User" (ID = 3)
            user.role_id = 3

            # Adicione o novo usuário ao banco de dados
            db.session.add(user)
            db.session.commit()

            # Defina a flag 'known' como False para indicar que o usuário é novo
            session['known'] = False
        else:
            # Se o usuário já existir, defina a flag 'known' como True
            session['known'] = True

        # Defina a sessão 'name' com o nome do usuário
        session['name'] = username

        # Redirecione de volta para a página inicial
        return redirect(url_for('index'))

    # Recupere todos os usuários e todas as roles do banco de dados
    users = User.query.all()
    roles = Role.query.all()

    # Renderize o template 'index.html' com os dados
    return render_template('index.html', form=form, users=users, roles=roles)


if __name__ == '__main__':
    app.run(debug=True)
