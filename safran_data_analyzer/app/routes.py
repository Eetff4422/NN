"""Définition des contrôleurs Flask (routes web et API)."""
import os
import uuid
import json
from datetime import datetime, timedelta
from flask import render_template, request, flash, redirect, url_for, session, current_app as app, jsonify
from werkzeug.utils import secure_filename
from flask_login import current_user, login_user, logout_user, login_required
from itsdangerous import URLSafeTimedSerializer

from app.extensions import db
from app.models import User, Report, LoginAttempt
from app.services.readers import ReaderFactory
from app.services.analyzer import ProductionAnalyzer

def allowed_file(filename):
    """Vérifie si l'extension du fichier est autorisée."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def _check_bruteforce(ip_address, email=None):
    """Vérifie si l'utilisateur a dépassé 5 tentatives en 10 minutes."""
    ten_mins_ago = datetime.utcnow() - timedelta(minutes=10)
    query = LoginAttempt.query.filter(
        LoginAttempt.timestamp >= ten_mins_ago,
        LoginAttempt.success == False
    )
    
    if email:
        attempts = query.filter((LoginAttempt.ip_address == ip_address) | (LoginAttempt.email_attempted == email)).count()
    else:
        attempts = query.filter(LoginAttempt.ip_address == ip_address).count()
        
    return attempts >= 5

def _log_attempt(ip_address, email, success):
    """Enregistre une tentative de connexion."""
    attempt = LoginAttempt(ip_address=ip_address, email_attempted=email, success=success)
    db.session.add(attempt)
    db.session.commit()

@app.before_request
def make_session_permanent():
    """Renouvelle la session."""
    session.permanent = True

# ==========================================
# ROUTES D'AUTHENTIFICATION
# ==========================================

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Gère la connexion et protège contre le bruteforce."""
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        ip_address = request.remote_addr
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        email = user.email if user else username
        
        if _check_bruteforce(ip_address, email):
            return "Trop de tentatives échouées. Compte bloqué pour 15 minutes.", 429

        if user is None or not user.check_password(password):
            _log_attempt(ip_address, email, False)
            flash("Identifiant ou mot de passe invalide.", "danger")
            return redirect(url_for('login'))
            
        _log_attempt(ip_address, email, True)
        login_user(user)
        flash(f"Bienvenue, {user.username} !", "success")
        return redirect(url_for('index'))

    return render_template('login.html')

@app.route('/logout')
def logout():
    """Déconnecte l'utilisateur."""
    logout_user()
    flash("Vous avez été déconnecté avec succès.", "info")
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Gère l'inscription avec contraintes métier."""
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    questions = app.config.get('SECURITY_QUESTIONS', [])

    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email').lower()
        password = request.form.get('password')
        question = request.form.get('secret_question')
        answer = request.form.get('secret_answer')

        domaines_autorises = app.config.get('ALLOWED_DOMAINS', [])
        if domaines_autorises and not any(email.endswith(domaine) for domaine in domaines_autorises):
            domaines_str = " ou ".join(domaines_autorises)
            flash(f"Inscription refusée : Vous devez utiliser une adresse e-mail valide ({domaines_str}).", "danger")
            return redirect(url_for('register'))

        if User.query.filter_by(email=email).first() or User.query.filter_by(username=username).first():
            flash("Un compte existe déjà avec cet e-mail ou cet identifiant.", "warning")
            return redirect(url_for('register'))

        if question not in questions:
            flash("Question de sécurité invalide.", "danger")
            return redirect(url_for('register'))

        new_user = User(username=username, email=email, secret_question=question)
        new_user.set_password(password)
        new_user.set_secret_answer(answer)
        
        db.session.add(new_user)
        db.session.commit()
        
        flash("Compte créé avec succès ! Vous pouvez maintenant vous connecter.", "success")
        return redirect(url_for('login'))

    return render_template('register.html', questions=questions)

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    """Demande de réinitialisation de mot de passe."""
    if request.method == 'POST':
        email = request.form.get('email').lower()
        user = User.query.filter_by(email=email).first()
        
        if user:
            serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
            token = serializer.dumps(user.email, salt='recuperation-mdp')
            reset_url = url_for('reset_password_question', token=token, _external=True)
            
            print("\n" + "="*50)
            print(f"📧 E-MAIL ENVOYÉ À : {user.email}")
            print(f"Lien de réinitialisation : {reset_url}")
            print("="*50 + "\n")
            
        flash("Si cette adresse existe, un e-mail avec un lien de récupération vient d'être envoyé.", "info")
        return redirect(url_for('login'))

    return render_template('forgot_password.html')

@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password_question(token):
    """Vérification de la question secrète."""
    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    try:
        email = serializer.loads(token, salt='recuperation-mdp', max_age=1800)
    except:
        flash("Le lien de récupération est invalide ou a expiré.", "danger")
        return redirect(url_for('forgot_password'))

    user = User.query.filter_by(email=email).first()
    if not user:
        flash("Erreur lors de la récupération.", "danger")
        return redirect(url_for('login'))

    if request.method == 'POST':
        answer = request.form.get('secret_answer')
        if user.check_secret_answer(answer):
            session['reset_authorized_for'] = user.email
            return redirect(url_for('set_new_password'))
        else:
            flash("Réponse incorrecte.", "danger")

    return render_template('reset_question.html', question=user.secret_question)

@app.route('/set_new_password', methods=['GET', 'POST'])
def set_new_password():
    """Définition du nouveau mot de passe."""
    if 'reset_authorized_for' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        new_password = request.form.get('new_password')
        user = User.query.filter_by(email=session['reset_authorized_for']).first()
        
        user.set_password(new_password)
        db.session.commit()
        
        session.pop('reset_authorized_for', None)
        flash("Votre mot de passe a été modifié avec succès.", "success")
        return redirect(url_for('login'))

    return render_template('set_new_password.html')

# ==========================================
# ROUTES APPLICATION (AJAX)
# ==========================================

@app.route('/', methods=['GET'])
@login_required
def index():
    """Page d'accueil."""
    historique = Report.query.filter_by(user_id=current_user.id).order_by(Report.uploaded_at.desc()).all()
    return render_template('index.html', historique=historique)

@app.route('/api/upload', methods=['POST'])
@login_required
def api_upload():
    """Endpoint AJAX pour uploader et analyser un fichier."""
    if 'file' not in request.files:
        return jsonify({"success": False, "error": "Aucun fichier n'a été envoyé."}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"success": False, "error": "Aucun fichier sélectionné."}), 400

    # Vérification MIME type pour plus de sécurité
    if file.content_type not in ['application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 'application/vnd.ms-excel']:
        return jsonify({"success": False, "error": "Format MIME invalide."}), 400

    if file and allowed_file(file.filename):
        original_filename = secure_filename(file.filename)
        # Nommage UUID+timestamp
        ext = original_filename.rsplit('.', 1)[1].lower()
        stored_filename = f"{uuid.uuid4().hex}_{int(datetime.utcnow().timestamp())}.{ext}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], stored_filename)

        file.save(filepath)

        # Crash Test
        try:
            reader = ReaderFactory.get_reader(filepath)
            df = reader.read(filepath)

            analyzer = ProductionAnalyzer(df)
            analysis_results = analyzer.analyze() # Retourne {kpis: {}, charts: {}}

            # Sauvegarde en base
            nouveau_rapport = Report(
                user_id=current_user.id,
                original_filename=original_filename,
                stored_filename=stored_filename,
                row_count=len(analyzer.df),
                column_snapshot=json.dumps(list(analyzer.df.columns)),
                graphs_json=json.dumps(analysis_results)
            )
            db.session.add(nouveau_rapport)
            db.session.commit()

            session['active_report_id'] = nouveau_rapport.id

            return jsonify({"success": True, "redirect_url": url_for('dashboard')}), 200

        except Exception as e:
            if os.path.exists(filepath):
                os.remove(filepath)
            return jsonify({"success": False, "error": str(e)}), 400

    return jsonify({"success": False, "error": "Format non autorisé."}), 400

@app.route('/dashboard')
@login_required
def dashboard():
    """Affiche la coquille vide du dashboard."""
    report_id = session.get('active_report_id')
    if not report_id:
        flash("Veuillez d'abord importer un fichier ou sélectionner un historique.", "warning")
        return redirect(url_for('index'))
    return render_template('dashboard.html')

@app.route('/api/dashboard_data')
@login_required
def api_dashboard_data():
    """Endpoint AJAX pour récupérer les données du dashboard."""
    report_id = session.get('active_report_id')
    if not report_id:
        return jsonify({"success": False, "error": "Aucun rapport actif."}), 400
        
    rapport = Report.query.get(report_id)
    if not rapport or rapport.user_id != current_user.id:
        return jsonify({"success": False, "error": "Rapport introuvable ou accès refusé."}), 404
        
    # Les données ont été précalculées au moment de l'upload et stockées en JSON
    if not rapport.graphs_json:
         return jsonify({"success": False, "error": "Données d'analyse corrompues."}), 500

    try:
        data = json.loads(rapport.graphs_json)
        # Add metadata
        data["metadata"] = {
            "filename": rapport.original_filename,
            "date": rapport.uploaded_at.strftime('%d/%m/%Y'),
            "rows": rapport.row_count
        }
        return jsonify({"success": True, "data": data}), 200
    except json.JSONDecodeError:
        return jsonify({"success": False, "error": "Erreur de lecture des données (JSONDecodeError)."}), 500

@app.route('/load_history/<int:report_id>')
@login_required
def load_history(report_id):
    """Charge un ancien fichier depuis la base de données."""
    rapport = Report.query.get_or_404(report_id)
    if rapport.user_id != current_user.id:
        flash("Accès refusé : Ce rapport ne vous appartient pas.", "danger")
        return redirect(url_for('index'))
        
    # L'avantage ici c'est qu'on a même plus besoin que le fichier physique existe
    # Les JSON sont en base de données.
    session['active_report_id'] = rapport.id
    return redirect(url_for('dashboard'))

@app.route('/delete_history/<int:report_id>', methods=['POST'])
@login_required
def delete_history(report_id):
    """Supprime un rapport d'analyse."""
    rapport = Report.query.get_or_404(report_id)
    if rapport.user_id != current_user.id:
        flash("Accès refusé : Ce rapport ne vous appartient pas.", "danger")
        return redirect(url_for('index'))
        
    try:
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], rapport.stored_filename)
        if os.path.exists(filepath):
            os.remove(filepath)

        if session.get('active_report_id') == rapport.id:
            session.pop('active_report_id', None)

        db.session.delete(rapport)
        db.session.commit()
        flash(f"L'analyse a été supprimée avec succès.", "success")
        
    except Exception as e:
        flash(f"Erreur lors de la suppression : {str(e)}", "danger")

    return redirect(url_for('index'))