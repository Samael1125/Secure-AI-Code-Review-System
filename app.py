from flask import Flask, render_template
from config import Config
from extensions import db, login_manager, bcrypt
from flask import redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from forms import RegisterForm, LoginForm
from forms import SnippetForm

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
bcrypt.init_app(app)
login_manager.init_app(app)

login_manager.login_view = "login"

from models import User, CodeSnippet, Review


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    form = RegisterForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(
            form.password.data
        ).decode("utf-8")

        user = User(email=form.email.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()

        flash("Account created successfully!", "success")
        return redirect(url_for("login"))

    return render_template("register.html", form=form)

@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()

        if user and bcrypt.check_password_hash(
            user.password, form.password.data
        ):
            login_user(user)
            flash("Login successful!", "success")
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid credentials", "danger")

    return render_template("login.html", form=form)

@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Logged out successfully", "info")
    return redirect(url_for("home"))

@app.route("/dashboard")
@login_required
def dashboard():
    snippets = CodeSnippet.query.filter_by(
        user_id=current_user.id
    ).all()

    return render_template("dashboard.html", snippets=snippets)

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/add_snippet", methods=["GET", "POST"])
@login_required
def add_snippet():
    form = SnippetForm()

    if form.validate_on_submit():
        snippet = CodeSnippet(
            title=form.title.data,
            language=form.language.data,
            code=form.code.data,
            user_id=current_user.id
        )

        db.session.add(snippet)
        db.session.commit()

        flash("Snippet added successfully!", "success")
        return redirect(url_for("dashboard"))

    return render_template("add_snippet.html", form=form)

@app.route("/delete_snippet/<int:snippet_id>")
@login_required
def delete_snippet(snippet_id):
    snippet = CodeSnippet.query.get_or_404(snippet_id)

    # Security check (very important)
    if snippet.user_id != current_user.id:
        flash("Unauthorized action!", "danger")
        return redirect(url_for("dashboard"))

    db.session.delete(snippet)
    db.session.commit()

    flash("Snippet deleted successfully!", "info")
    return redirect(url_for("dashboard"))

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)