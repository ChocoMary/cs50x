from flask import Flask, flash, render_template, request, redirect, session
from flask_session import Session
from functools import wraps
from werkzeug.security import check_password_hash, generate_password_hash
from cs50 import SQL

app = Flask(__name__)

app.config["SESSION_PERMANENT"] = Flask
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Connect to database
db = SQL("sqlite:///budget.db")

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    
    return decorated_function

@app.route("/")
@login_required
def index():
    """ Show dashboard (homepage)"""
    return render_template("index.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    """ log in user """
    session.clear()

    if request.method == "POST":
        

@app.route("/add", methods=["GET", "POST"])
@login_required
def add():
    """ Add a new transaction """
    if request.method == "POST":
        date = request.form.get("date")
        type = request.form.get("type")
        category = request.form.get("category")
        amount = request.form.get("amount")
        note = request.form.get("note")

        # insert into database
        db.execute(
            "INSERT INTO transactions (date, type, category, amount, note) VALUES (?, ?, ?, ?, ?)",
            date, type, category, amount, note,
        )

        return redirect("/")
    
    # GET method
    return render_template("add.html")

if __name__ == "__main__":
    app.run(debug=True)