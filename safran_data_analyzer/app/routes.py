import os
from flask import render_template, request, flash, redirect, url_for, session, current_app as app
from app.services.readers import ReaderFactory
from app.services.analyzer import ProductionAnalyzer
from flask_login import current_user, login_user, logout_user, login_required
from app.models import User, Report
from app.extensions import db
from itsdangerous import URLSafeTimedSerializer
from werkzeug.utils import secure_filename

def allowed_file(filename):
    """
    Vérifie si le fichier a une extension autorisée.

    Args:
        filename (str): Le nom du fichier à vérifier.

    Returns:
        bool: True si l'extension est autorisée, False sinon.
    """
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/', methods=['GET', 'POST'])
@login_required
def index():
    """
    Page d'accueil de l'application. Affiche l'historique des rapports
    et permet d'importer un nouveau fichier pour analyse.
    """
    if request.method == 'POST':
        if 'file' not in request.files:
            flash("Aucun fichier n'a été envoyé.", "danger")
            return redirect(request.url)
            
        file = request.files['file']
        if file.filename == '':
            flash("Aucun fichier sélectionné.", "warning")
            return redirect(request.url)
            
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            # --- LE CRASH TEST AVANT SAUVEGARDE EN BASE DE DONNÉES ---
            try:
                # 1. On tente de lire le fichier
                reader = ReaderFactory.get_reader(filepath)
                df = reader.read(filepath)
                
                # 2. On tente de l'analyser (C'est ici que l'erreur de colonne sera détectée)
                ProductionAnalyzer(df)
                
                # 3. SI ET SEULEMENT SI aucune erreur n'a éclaté, on sauvegarde dans l'historique !
                nouveau_rapport = Report(filename=filename, filepath=filepath, author=current_user)
                db.session.add(nouveau_rapport)
                db.session.commit()
                
                session['filepath'] = filepath
                session['filename'] = filename
                
                return redirect(url_for('dashboard'))
                
            except Exception as e:
                # ÉCHEC DU CRASH TEST : Le fichier est mauvais
                if os.path.exists(filepath):
                    os.remove(filepath) # On nettoie le serveur en supprimant le mauvais fichier
                
                flash(f"Fichier rejeté (Format invalide) : {str(e)}", "danger")
                return redirect(request.url)
            # ---------------------------------------------------------
            
        else:
            flash("Format non autorisé.", "danger")
            return redirect(request.url)

    # Récupération de l'historique de l'utilisateur (trié du plus récent au plus ancien)
    historique = Report.query.filter_by(user_id=current_user.id).order_by(Report.upload_date.desc()).all()
    
    return render_template('index.html', historique=historique)

@app.route('/load_history/<int:report_id>')
@login_required
def load_history(report_id):
    """Charge un ancien fichier depuis la base de données."""
    rapport = Report.query.get_or_404(report_id)
    
    # Sécurité : Vérifier que l'utilisateur n'essaie pas d'ouvrir le rapport d'un collègue
    if rapport.user_id != current_user.id:
        flash("Accès refusé : Ce rapport ne vous appartient pas.", "danger")
        return redirect(url_for('index'))
        
    # Vérifier que le fichier physique n'a pas été supprimé du serveur entre-temps
    if not os.path.exists(rapport.filepath):
        flash("Le fichier source de cette analyse a été supprimé du serveur.", "warning")
        # Optionnel : nettoyer la base de données si le fichier n'existe plus
        db.session.delete(rapport)
        db.session.commit()
        return redirect(url_for('index'))

    # On remet le fichier en session et on lance le dashboard
    session['filepath'] = rapport.filepath
    session['filename'] = rapport.filename
    return redirect(url_for('dashboard'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    Gère la connexion des utilisateurs.
    """
    # Si l'utilisateur est déjà connecté, on l'envoie sur l'accueil
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        # Vérification des identifiants
        if user is None or not user.check_password(password):
            flash("Identifiant ou mot de passe invalide.", "danger")
            return redirect(url_for('login'))
            
        # Création de la session sécurisée
        login_user(user)
        flash(f"Bienvenue, {user.username} !", "success")
        return redirect(url_for('index'))

    return render_template('login.html')

@app.route('/logout')
def logout():
    """
    Déconnecte l'utilisateur actuel.
    """
    logout_user()
    flash("Vous avez été déconnecté avec succès.", "info")
    return redirect(url_for('login'))

# --- 1. GESTION DES 15 MINUTES D'INACTIVITÉ ---
@app.before_request
def make_session_permanent():
    """Réinitialise le chrono de 15 minutes à chaque fois que l'utilisateur clique quelque part."""
    session.permanent = True

# --- 2. INSCRIPTION SÉCURISÉE ---
@app.route('/register', methods=['GET', 'POST'])
def register():
    """
    Gère l'inscription de nouveaux utilisateurs.
    """
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email').lower()
        password = request.form.get('password')
        question = request.form.get('secret_question')
        answer = request.form.get('secret_answer')

        # Règle Métier 1 : Vérification du domaine
        domaines_autorises = app.config.get('ALLOWED_DOMAINS', [])
        if domaines_autorises and not any(email.endswith(domaine) for domaine in domaines_autorises):
            domaines_str = " ou ".join(domaines_autorises)
            flash(f"Inscription refusée : Vous devez utiliser une adresse e-mail valide ({domaines_str}).", "danger")
            return redirect(url_for('register'))

        # Règle Métier 2 : Unicité du compte
        if User.query.filter_by(email=email).first() or User.query.filter_by(username=username).first():
            flash("Un compte existe déjà avec cet e-mail ou cet identifiant.", "warning")
            return redirect(url_for('register'))

        # Création du compte
        new_user = User(username=username, email=email, secret_question=question)
        new_user.set_password(password)
        new_user.set_secret_answer(answer)
        
        db.session.add(new_user)
        db.session.commit()
        
        flash("Compte créé avec succès ! Vous pouvez maintenant vous connecter.", "success")
        return redirect(url_for('login'))

    return render_template('register.html')

# --- 3. RÉCUPÉRATION DE MOT DE PASSE ---
def generate_reset_token(user_email):
    """Génère un jeton crypté valable 30 minutes."""
    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    return serializer.dumps(user_email, salt='recuperation-mdp')

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    """Étape 1 : Demande de réinitialisation."""
    if request.method == 'POST':
        email = request.form.get('email').lower()
        user = User.query.filter_by(email=email).first()
        
        if user:
            token = generate_reset_token(user.email)
            reset_url = url_for('reset_password_question', token=token, _external=True)
            
            # SIMULATION D'ENVOI D'E-MAIL (Puisque nous n'avons pas de vrai serveur SMTP configuré)
            print("\n" + "="*50)
            print(f"📧 E-MAIL ENVOYÉ À : {user.email}")
            print(f"Sujet: Récupération de votre mot de passe Safran")
            print(f"Lien de réinitialisation : {reset_url}")
            print("="*50 + "\n")
            
        # Par sécurité, on affiche toujours le même message (pour empêcher les pirates de deviner quels e-mails existent)
        flash("Si cette adresse existe, un e-mail avec un lien de récupération vient d'être envoyé.", "info")
        return redirect(url_for('login'))

    return render_template('forgot_password.html')

@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password_question(token):
    """Étape 2 : Le lien de l'e-mail amène ici. On pose la question secrète."""
    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    try:
        # Le jeton expire après 1800 secondes (30 minutes)
        email = serializer.loads(token, salt='recuperation-mdp', max_age=1800)
    except:
        flash("Le lien de récupération est invalide ou a expiré.", "danger")
        return redirect(url_for('forgot_password'))

    user = User.query.filter_by(email=email).first()

    if request.method == 'POST':
        answer = request.form.get('secret_answer')
        
        if user.check_secret_answer(answer):
            # Réponse correcte : on l'autorise à changer le mot de passe
            session['reset_authorized_for'] = user.email
            return redirect(url_for('set_new_password'))
        else:
            flash("Réponse incorrecte.", "danger")

    return render_template('reset_question.html', question=user.secret_question)

@app.route('/set_new_password', methods=['GET', 'POST'])
def set_new_password():
    """Étape 3 : Changement du mot de passe."""
    if 'reset_authorized_for' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        new_password = request.form.get('new_password')
        user = User.query.filter_by(email=session['reset_authorized_for']).first()
        
        user.set_password(new_password)
        db.session.commit()
        
        # On nettoie l'autorisation
        session.pop('reset_authorized_for', None)
        flash("Votre mot de passe a été modifié avec succès.", "success")
        return redirect(url_for('login'))

    return render_template('set_new_password.html')

@app.route('/dashboard')
@login_required
def dashboard():
    """
    Affiche le tableau de bord avec les résultats de l'analyse du fichier.
    """
    filepath = session.get('filepath')
    
    if not filepath or not os.path.exists(filepath):
        flash("Veuillez d'abord importer un fichier.", "warning")
        return redirect(url_for('index'))

    try:
        # 1. LECTURE : On demande à l'usine (Factory) de lire le fichier
        reader = ReaderFactory.get_reader(filepath)
        df = reader.read(filepath)
        
        # 2. ANALYSE : On donne les données à notre nouveau cerveau métier
        analyzer = ProductionAnalyzer(df)
        
        # Gestion du filtre (choisi par l'utilisateur sur la page web)
        selected_piece = request.args.get('piece', 'Toutes')
        analyzer.apply_filter(selected_piece)
        
        # Récupération des résultats calculés
        total_pieces, taux_rebut = analyzer.get_kpis()
        graph1JSON, graph2JSON, graph3JSON = analyzer.get_charts()
        
        # 3. AFFICHAGE : On envoie tout ça à la page HTML
        return render_template('dashboard.html', 
                               graph1JSON=graph1JSON, 
                               graph2JSON=graph2JSON,
                               graph3JSON=graph3JSON,
                               total_pieces=total_pieces,
                               taux_rebut=taux_rebut,
                               pieces_uniques=analyzer.pieces_uniques,
                               selected_piece=selected_piece)
        
    except Exception as e:
        # Si un fichier corrompu passe les sécurités, l'erreur est interceptée proprement ici
        flash(f"Erreur lors de l'analyse : {str(e)}", "danger")
        return redirect(url_for('index'))