import os
from click import prompt
from dotenv import load_dotenv
from flask import request
from flask import Flask, render_template
from config import Config
from extensions import db, login_manager, bcrypt
from flask import redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from forms import RegisterForm, LoginForm
from forms import SnippetForm

load_dotenv()

import google.generativeai as genai

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-pro-latest")

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
    search_query = request.args.get("search")
    language_filter = request.args.get("language")

    snippets_query = CodeSnippet.query.filter_by(
        user_id=current_user.id
    )

    if search_query:
        snippets_query = snippets_query.filter(
            CodeSnippet.title.ilike(f"%{search_query}%")
        )

    if language_filter:
        snippets_query = snippets_query.filter_by(
            language=language_filter
        )

    snippets = snippets_query.all()

    snippet_data = []

    for snippet in snippets:
        reviews = Review.query.filter_by(
            snippet_id=snippet.id
        ).all()

        ratings = [r.rating for r in reviews if r.rating]
        avg_rating = sum(ratings) / len(ratings) if ratings else None

        snippet_data.append({
            "snippet": snippet,
            "avg_rating": avg_rating
        })

    return render_template(
        "dashboard.html",
        snippet_data=snippet_data
    )

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

@app.route("/edit_snippet/<int:snippet_id>", methods=["GET", "POST"])
@login_required
def edit_snippet(snippet_id):
    snippet = CodeSnippet.query.get_or_404(snippet_id)

    # Security check
    if snippet.user_id != current_user.id:
        flash("Unauthorized action!", "danger")
        return redirect(url_for("dashboard"))

    form = SnippetForm(obj=snippet)

    if form.validate_on_submit():
        snippet.title = form.title.data
        snippet.language = form.language.data
        snippet.code = form.code.data

        db.session.commit()

        flash("Snippet updated successfully!", "success")
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

@app.route("/review_snippet/<int:snippet_id>")
@login_required
def review_snippet(snippet_id):
    snippet = CodeSnippet.query.get_or_404(snippet_id)

    if snippet.user_id != current_user.id:
        flash("Unauthorized action!", "danger")
        return redirect(url_for("dashboard"))

    prompt = f"""
    You are a senior software engineer.

    Review this {snippet.language} code:

    {snippet.code}

    Provide:
    1. Code quality feedback
    2. Optimization suggestions
    3. Security issues (if any)
    4. Best practices improvements
    5. Overall rating out of 10
    """

    import re

    rating_value = None   # ← IMPORTANT (initialize first)

    try:
        response = model.generate_content(prompt)
        review_text = response.text

        rating_match = re.search(r'(\d+(\.\d+)?)/10', review_text)
        if rating_match:
            rating_value = float(rating_match.group(1))

    except Exception:
        review_text = """
        ⚠️ AI Service Temporarily Unavailable (Quota Exceeded)

        Simulated AI Review:

        ✔ Code structure looks organized.
        ✔ Consider adding proper error handling.
        ✔ Improve variable naming for readability.
        ✔ Optimize loops if handling large datasets.
        ✔ Add input validation for security.

        Overall Rating: 7.5/10
        """

    rating_value = 7.5   # ← ALSO define it here

    review = Review(
    feedback=review_text,
    rating=rating_value,
    snippet_id=snippet.id
    )

    db.session.add(review)
    db.session.commit()

    flash("AI review generated!", "success")

    return render_template("review.html", snippet=snippet, review=review_text)

@app.route("/reviews/<int:snippet_id>")
@login_required
def view_reviews(snippet_id):
    snippet = CodeSnippet.query.get_or_404(snippet_id)

    if snippet.user_id != current_user.id:
        flash("Unauthorized action!", "danger")
        return redirect(url_for("dashboard"))

    reviews = Review.query.filter_by(
        snippet_id=snippet.id
    ).order_by(Review.created_at.desc()).all()

    return render_template("review_history.html",
                           snippet=snippet,
                           reviews=reviews)

@app.errorhandler(404)
def not_found_error(error):
    return render_template("404.html"), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template("500.html"), 500

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)