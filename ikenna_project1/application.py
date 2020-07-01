import os, requests

from flask import Flask, session, render_template, url_for, request, redirect, jsonify
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from intersection import *

app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database - set DATABASE_URL to Heroku database URL
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))


@app.route("/")
def index():
    return render_template("index.html")

@app.route("/loginregister")
def loginregister():
    #maybe put like, if logged in hehe silly you don't need to be here
    return render_template("login_register.html")

@app.route("/registration", methods=["POST"])
def registration():
    name = request.form.get("fname")
    username = request.form.get("username")
    password = request.form.get("password")

    if db.execute("SELECT * FROM peeps WHERE username = :username", {"username": username}).fetchone() is None:
        db.execute("INSERT INTO peeps (name, username, password) VALUES (:name, :username, :password)", {"name": name, "username": username, "password": password})
        db.commit()
    else:
        return render_template("login_register.html", msg="User already exists, try a different user name!!")    
    success = "You are now registered! Go ahead and log in :)"
    return render_template("login_register.html", msg=success)

@app.route("/login", methods=["POST"])
def login():
    username = request.form.get("username")
    password = request.form.get("password")

    user = db.execute("SELECT * FROM peeps WHERE username = :username", {"username": username}).fetchone()
    error = "Hm there seems to be a boo-boo with your login. Try again?"

    if len(user) == 0:
        return render_template("login_register.html", msg = error)
    elif user.password == password:
        session["user"] = user.name
        name = session["user"]
        return render_template("search.html", name=name)
    else:
        return render_template("login_register.html", msg = error)

@app.route("/search", methods=["POST", "GET"])
def search():
    if "user" not in session:
        return render_template("login_register.html", msg = "You need to login >:(")
    elif request.method == "GET":
        name = session["user"]
        return render_template("search.html", name=name)
    else:
        name = session["user"]
        title = request.form.get("title")
        mtitle = '%' + title + '%'
        author = request.form.get("author")
        mauthor = '%' + author + '%'
        isbn = request.form.get("ISBN")
        misbn = '%' + isbn + '%'
        # code to find relevant matches
        if title != "":
            tresults = db.execute("SELECT * FROM books WHERE title LIKE :title", {"title": mtitle}).fetchall()
        else:
            tresults = []
        if author != "":
            aresults = db.execute("SELECT * FROM books WHERE author LIKE :author", {"author": mauthor}).fetchall()
        else:
            aresults = []
        if isbn != "":
            iresults = db.execute("SELECT * FROM books WHERE isbn LIKE :isbn", {"isbn": misbn}).fetchall()
        else:
            iresults = []

        atresults = intersectionality(tresults, aresults)
        if len(atresults) == 0:
            atresults = []
        results = intersectionality(atresults, iresults)

        if len(results) == 0:
            return render_template("search.html", name=name, info=None)
        
        return render_template("search.html", name=name, info=results)

@app.route("/zoomin/<int:book_id>")
def zoomin(book_id):
    if "user" not in session:
        return render_template("login_register.html", msg = "You need to login >:(")
    else:
        book = db.execute("SELECT * FROM books WHERE id = :id", {"id": book_id}).fetchall()
        reviews = db.execute("SELECT * FROM reviews WHERE book_id = :book_id", {"book_id": book_id}).fetchall()

        GRinfo = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": "C58nrku9rzsRPpjStLKnqQ", "isbns": book[0].isbn})
        if GRinfo.status_code != 200:
           GRdata = None
        else:
            GRdata = GRinfo.json()
        GRdata = GRdata["books"][0]

        return render_template("zoomin.html", book=book[0], reviews=reviews, message = None, data = GRdata)

@app.route("/review/<int:book>", methods=["POST"])
def review(book):
    book_id = book #or book[0].id
    books = db.execute("SELECT * FROM books WHERE id = :id", {"id": book_id}).fetchall()
    rating = request.form.get("rating")
    comments = request.form.get("comment")
    name = session["user"]

    GRinfo = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": "C58nrku9rzsRPpjStLKnqQ", "isbns": books[0].isbn})
    if GRinfo.status_code != 200:
        GRdata = None
    else:
        GRdata = GRinfo.json()
    GRdata = GRdata["books"][0]

    if rating == "":
        return "yo put in a rating come on"
    elif comments == "":
        return "hey say something about the book"
    elif len(db.execute("SELECT * FROM reviews JOIN books ON reviews.book_id = books.id WHERE name = :name AND book_id = :book_id", {"name": name, "book_id": book_id}).fetchall()) == 0:
        db.execute("INSERT INTO reviews (book_id, rating, comments, name) VALUES (:book_id, :rating, :comments, :name)", {"book_id": book_id, "rating": rating, "comments": comments, "name": name})
        db.commit()
        reviews = db.execute("SELECT * FROM reviews WHERE book_id = :book_id", {"book_id": book_id}).fetchall()
        return render_template("zoomin.html", book=books[0], reviews=reviews, message = None, data = GRdata)
    else:
        reviews = db.execute("SELECT * FROM reviews WHERE book_id = :book_id", {"book_id": book_id}).fetchall()
        message  = "you already left a review for this book! don't be greedy lol"
        return render_template("zoomin.html", book=books[0], reviews=reviews, message = message, data = GRdata)

@app.route("/api/<string:isbn>", methods=["GET"])
def api(isbn):
    books = db.execute("SELECT * FROM books WHERE isbn = :isbn", {"isbn": isbn}).fetchall()
    if len(books) == 0:
        return jsonify({"error": "No book found with in our database with the provided ISBN"}), 404
    book = books[0]
       
    GRinfo = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": "C58nrku9rzsRPpjStLKnqQ", "isbns": book.isbn})
    if GRinfo.status_code != 200:
        GRdata = None
    else:
        GRdata = GRinfo.json()
    GRdata = GRdata["books"][0]


    return jsonify({
        "title": book.title,
        "author": book.author,
        "publication_year": book.year,
        "isbn": book.isbn,
        "review_count": int(GRdata["reviews_count"]),
        "average_score": float(GRdata["average_rating"])
    })

@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for('index'))

# when starting flask server, input this code every time
# export FLASK_APP=application.py; export DATABASE_URL=postgres://zddfkjvbipltna:12b47f4f2119fef285c265545ee868e687150ba9bed216e63040fb3810bad31b@ec2-3-91-139-25.compute-1.amazonaws.com:5432/d6ea84c67ln8bu; export FLASK_DEBUG=1

#then do psql postgres://zddfkjvbipltna:12b47f4f2119fef285c265545ee868e687150ba9bed216e63040fb3810bad31b@ec2-3-91-139-25.compute-1.amazonaws.com:5432/d6ea84c67ln8bu to see table stuff