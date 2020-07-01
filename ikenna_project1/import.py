import os
import csv

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

def create_table():
	db.execute("CREATE TABLE books (id SERIAL PRIMARY KEY, isbn VARCHAR NOT NULL, title VARCHAR NOT NULL, author VARCHAR NOT NULL, year INTEGER NOT NULL)")
	db.commit()
	print("books table has been created")

def main():
    create_table()
    b = open("books.csv")
    reader = csv.reader(b)
    for isbn, title, author, year in reader:
        if isbn == "isbn":
            continue
        else:
            db.execute("INSERT INTO books (isbn, title, author, year) VALUES (:isbn, :title, :author, :year)", 
            {"isbn": isbn, "title": title, "author": author, "year": year})
    db.commit()

if __name__ == "__main__":
    main()