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

def apology(message, code=400):
    """Render message as an apology to user."""

    def escape(s):
        """
        Escape special characters.

        https://github.com/jacebrowning/memegen#special-characters
        """
        for old, new in [
            ("-", "--"),
            (" ", "-"),
            ("_", "__"),
            ("?", "~q"),
            ("%", "~p"),
            ("#", "~h"),
            ("/", "~s"),
            ('"', "''"),
        ]:
            s = s.replace(old, new)
        return s

    return render_template("apology.html", top=code, bottom=escape(message)), code

@app.route("/")
@login_required
def index():
    """ Show dashboard (homepage)"""
    return apology("TODO")

@app.route("/login", methods=["GET", "POST"])
def login():
    """ log in user """
    session.clear()

    if request.method == "POST":
        rows = db.execute(
            "SELECT * FROM users WHERE username = ?", request.form.get("username")
        )

        if len(rows) != 1 or not check_password_hash(
            rows[0]["hash"], request.form.get("password")
        ):
            return apology("Incorrect username or password")
        
        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]
        return redirect("/")
    
    else:
        return render_template("login.html")

@app.route("/logout")
def logout():
    """ Log user out """
    # Forget any user_id 
    session.clear()

    return redirect("/")

@app.route("/register", methods = ["GET", "POST"])
def register():
    """ Register user """
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        if password != confirmation:
            return apology("Reconfirm password")
        
        hash = generate_password_hash(password)

        try:
            db.execute(
                "INSERT INTO users (username, hash) VALUES (?, ?)", username, hash
            )
            flash("You're successfully registered!")
            return redirect("/login")
        except ValueError:
            return apology("Username already exist")
        
    else:
        return render_template("register.html")


@app.route("/add", methods=["GET", "POST"])
@login_required
def add():
    """ Add a new transaction """
    if request.method == "POST":
        type_ = request.form.get("type")
        category = request.form.get("category")
        amount = request.form.get("amount")
        note = request.form.get("note")

        try:
            amount = float(amount)
            if type_ == "Expense":
                amount = 0 - amount
        except ValueError:
            return apology("Invalid Amount")

        # insert into database
        db.execute(
            "INSERT INTO transactions (user_id, date, type, category, amount, note) VALUES (?, datetime('now'), ?, ?, ?, ?)",
            session["user_id"], type_, category, amount, note,
        )

        return redirect("/")
    
    # GET method
    return render_template("add.html")

@app.route("/history")
@login_required
def history():
    type_ = request.args.get("type")
    category = request.args.get("category")
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")

    query = "SELECT date, type, category, amount, note FROM transactions WHERE user_id = ?"

    params = [session["user_id"]]

    if type_:
        query += " AND type = ?"
        params.append(type_)

    if category:
        query += " AND category LIKE ?"
        params.append(f"%{category}%")

    if start_date:
        query += " AND date(date) >= ?"
        params.append(start_date)

    if end_date:
        query += " AND date(date) <= ?"
        params.append(end_date)

    query += " ORDER BY date DESC"

    transactions = db.execute(query, *params)

    return render_template("history.html", transactions = transactions)



if __name__ == "__main__":
    app.run(debug=True)