CREATE TABLE peeps (
    id SERIAL PRIMARY KEY,
    name VARCHAR NOT NULL,
    username VARCHAR NOT NULL,
    password VARCHAR NOT NULL
);

CREATE TABLE reviews (
    id SERIAL PRIMARY KEY,
    book_id INTEGER REFERENCES books,
    rating INTEGER NOT NULL,
    comments VARCHAR NOT NULL,
    name VARCHAR NOT NULL
);