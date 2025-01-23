from flask import Flask, flash, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import requests
import random

# Função para obter um versículo aleatório de uma API externa
def obter_versiculo_aleatorio():
    url = "https://bible-api.com/random?translation=kjv"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        versiculo = data.get('text', 'Versículo não encontrado.')
        referencia = data.get('reference', 'Referência não encontrada.')
        return f"{versiculo} - {referencia}"
    else:
        return "Não foi possível obter o versículo."

# Configuração do Flask e SQLAlchemy
app = Flask(__name__)
app.secret_key = 'chave_secreta_para_o_site'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///devocional.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)  # Configurando Flask-Migrate

# Modelo para os usuários
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    devocionais = db.relationship('Devocional', backref='user', lazy=True)

# Modelo para os devocionais
class Devocional(db.Model):
    __tablename__ = 'devocionais'

    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_favorite = db.Column(db.Boolean, default=False)

# Rota inicial
@app.route('/')
def home():
    return render_template('index.html')

# Rota para cadastro de usuários
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = generate_password_hash(request.form['password'], method='pbkdf2:sha256')

        user = User(email=email, password=password)
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('login'))

    return render_template('register.html')

# Rota para login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            return redirect(url_for('dashboard'))
        else:
            flash("Usuário ou senha incorretos!", 'error')

    return render_template('login.html')

# Rota para o painel de devocionais
@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']

    if request.method == 'POST':
        content = request.form['content']
        devocional = Devocional(content=content, user_id=user_id)
        db.session.add(devocional)
        db.session.commit()

    devocionais = Devocional.query.filter_by(user_id=user_id).all()
    return render_template('dashboard.html', devocionais=devocionais)

# Rota para logout
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('home'))

# Rota para deletar um devocional
@app.route('/delete_devocional/<int:id>', methods=['POST'])
def delete_devocional(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    devocional = Devocional.query.filter_by(id=id, user_id=user_id).first()

    if devocional:
        db.session.delete(devocional)
        db.session.commit()

    return redirect(url_for('dashboard'))

# Rota para exibir devocionais favoritos
@app.route('/meus-devocionais-favoritos')
def meus_devocionais_favoritos():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    devocionais_favoritos = Devocional.query.filter_by(user_id=user_id, is_favorite=True).all()

    return render_template('meus_devocionais_favoritos.html', devocionais=devocionais_favoritos)

# Rota para favoritar ou desfavoritar um devocional
@app.route('/favoritar/<int:id>', methods=['POST'])
def favoritar_devocional(id):
    devocional = Devocional.query.get(id)
    if devocional:
        devocional.is_favorite = not devocional.is_favorite
        db.session.commit()
        flash('Devocional atualizado com sucesso!', 'success')
    else:
        flash('Devocional não encontrado.', 'error')
    return redirect(url_for('dashboard'))

# Rota para sortear um versículo
@app.route('/sortear_versiculo', methods=['GET'])
def sortear_versiculo():
    versiculos = [
        "João 3:16 - Porque Deus amou o mundo de tal maneira que deu o seu Filho unigênito...",
        "Salmo 23:1 - O Senhor é o meu pastor, nada me faltará.",
        "Filipenses 4:13 - Posso todas as coisas naquele que me fortalece.",
    ]

    versiculo_escolhido = random.choice(versiculos)
    return render_template('versiculo_aleatorio.html', versiculo=versiculo_escolhido)

# Rota para exibir todos os devocionais do usuário
@app.route('/meus-devocionais')
def meus_devocionais():
    if 'user_id' not in session:
        return redirect(url_for('login'))  # Redireciona para login se não estiver logado

    user_id = session['user_id']
    devocionais = Devocional.query.filter_by(user_id=user_id).all()  # Busca todos os devocionais do usuário

    return render_template('meus_devocionais.html', devocionais=devocionais)

@app.route('/buscar_devocionais', methods=['GET', 'POST'])
def buscar_devocionais():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    devocionais = []
    if request.method == 'POST':
        search_query = request.form['search']
        devocionais = Devocional.query.filter(Devocional.content.ilike(f'%{search_query}%'), Devocional.user_id == user_id).all()

    return render_template('buscar_devocionais.html', devocionais=devocionais)

@app.route('/editar_devocional/<int:id>', methods=['GET', 'POST'])
def editar_devocional(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    devocional = Devocional.query.get_or_404(id)
    if devocional.user_id != session['user_id']:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        devocional.content = request.form['content']
        db.session.commit()
        flash('Devocional atualizado com sucesso!', 'success')
        return redirect(url_for('dashboard'))

    return render_template('editar_devocional.html', devocional=devocional)



if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
