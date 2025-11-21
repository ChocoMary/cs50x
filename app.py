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

@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

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
            
            # creating balance for new user
            user_id = db.execute(
                "SELECT id FROM users WHERE username = ?", username
            )
            db.execute("INSERT INTO balances (user_id, balance) VALUES (?, 0)", user_id)
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
        category_id = request.form.get("category")
        amount = request.form.get("amount")
        note = request.form.get("note")

        # Optional: new category
        new_category = request.form.get("new_category").title()

        # Validate amount
        try:
            amount = float(amount)
            if amount < 0:
                return apology("Invalid Amount!")
            if type_ == "Expense":
                amount = -amount
        except ValueError:
            return apology("Invalid Amount")
        
        # Category Check
        if category_id and new_category:
            flash("Please choose only one category.")
            return redirect("/add")

        if not category_id and not new_category:
            flash("Please choose or create a category.")
            return redirect("/add")

        if new_category:

            # Check if it already exists
            existing = db.execute(
                "SELECT id FROM categories WHERE name = ? AND (user_id = ? OR user_id IS NULL)", new_category, session["user_id"]
            )
            if existing:
                category_id = existing[0]["id"]
            else:
                db.execute(
                    "INSERT INTO categories (user_id, name) VALUES(?, ?)", session["user_id"], new_category
                )

                category_id = db.execute(
                    "SELECT id FROM categories WHERE user_id = ? AND name = ?", session["user_id"], new_category
                )[0]["id"]

        # insert into database
        db.execute(
            "INSERT INTO transactions (user_id, date, type, category_id, amount, note) VALUES (?, datetime('now'), ?, ?, ?, ?)",
            session["user_id"], type_, category_id, amount, note,
        )

        # Update Balance
        db.execute(
            "UPDATE balances SET balance = balance + ? WHERE user_id = ?", amount, session["user_id"]
        )

        flash("Transaction added successfully!")

        return redirect("/add")
    
    # GET method
    categories = db.execute(
        "SELECT * FROM categories WHERE user_id IS NULL OR user_id = ? ORDER BY name", session["user_id"]
    )
    return render_template("add.html", categories = categories)

@app.route("/history")
@login_required
def history():
    categories = db.execute(
        "SELECT id, name FROM categories WHERE user_id IS NULL OR user_id = ?", session["user_id"]
    )

    type_ = request.args.get("type")
    category_id = request.args.get("category")
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")

    # query = "SELECT date, type, category, amount, note FROM transactions WHERE user_id = ?"
    query = """
            SELECT t.id, t.date, t.type, t.amount, t.note , c.name AS category_name
            FROM transactions t
            LEFT JOIN categories c ON t.category_id = c.id
            WHERE t.user_id = ?
"""
    params = [session["user_id"]]

    if type_:
        query += " AND t.type = ?"
        params.append(type_)

    if category_id:
        query += " AND t.category_id = ?"
        params.append(f"%{category_id}%")

    if start_date:
        query += " AND date(t.date) >= ?"
        params.append(start_date)

    if end_date:
        query += " AND date(t.date) <= ?"
        params.append(end_date)

    query += " ORDER BY t.date DESC"

    transactions = db.execute(query, *params)


    return render_template("history.html", transactions = transactions, categories = categories)

@app.route("/saving", methods=["GET", "POST"])
@login_required
def saving():

    if request.method == "POST":
        goal_id = request.form.get("goal_id")
        new_goal = request.form.get("new_goal")
        target_amount = request.form.get("target_amount")
        amount = request.form.get("amount")

        
        if goal_id and new_goal:
            return apology("Choose only one goal option.")
        
        if not goal_id and not new_goal:
            return apology("Please choose one goal option.")
        
        try:
            amount = float(amount)
            if amount < 0:
                return apology("Invalid amount!")
        except ValueError:
            return apology("Please enter numeric amount.")
        
        if new_goal:
            if not target_amount:
                return apology("Please set a target amount.")
            
            try:
                target_amount = float(target_amount)
            except ValueError:
                return apology("Invalid target amount.")
            
            db.execute(
                "INSERT INTO saving_goals (user_id, name, target, saved) VALUES (?, ?, ?, ?)", session["user_id"], new_goal, target_amount, 0
            )

            goal_id = db.execute(
                "SELECT id FROM saving_goals WHERE user_id = ? AND name = ?", session["user_id"], new_goal
            )[0]["id"]

        # Check current balance
        balance_row = db.execute(
            "SELECT balance FROM balances WHERE user_id = ?", session["user_id"]
        )

        current_balance = balance_row[0]["balance"]

        if amount > current_balance:
            return apology("Not enough balance for saving.")
        
        # Update balance
        db.execute(
            "UPDATE balances SET balance = balance - ? WHERE user_id = ?", amount, session["user_id"]
        )

        # Update the saved amount
        db.execute(
            "UPDATE saving_goals SET saved = saved + ? WHERE id = ? AND user_id = ?", amount, goal_id, session["user_id"]
        )

        # Insert Transaction Records
        db.execute(
            "INSERT INTO saving_deposits (user_id, goal_id, amount) VALUES (?, ?, ?)", session["user_id"], goal_id, amount
        )

        flash("Deposit added successfully!")
        return redirect("/saving")

    else:

        # GET all saving goals belonging to user
        goals = db.execute(
            "SELECT * FROM saving_goals WHERE user_id = ?", session["user_id"]
        )

        # GET current balance
        balance_row = db.execute(
            "SELECT balance FROM balances WHERE user_id = ?", session["user_id"]
        )

        current_balance = balance_row[0]["balance"]

        return render_template("saving.html", goals = goals, balance = current_balance)


if __name__ == "__main__":
    app.run(debug=True)