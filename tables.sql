



CREATE DATABASE if not exists LibraryManagement CHARACTER SET utf8 COLLATE utf8_general_ci;

/* =====================
	CREATE ENTITIES 
======================*/
USE LibraryManagement;



CREATE TABLE if not exists schools
(   school_name varchar(30) not null,
	school_id int auto_increment PRIMARY KEY,
	principal_first_name varchar(20) NOT NULL,
	principal_last_name varchar(20) NOT NULL,
	operator_first_name varchar(20) NOT NULL,
	operator_last_name varchar(20) NOT NULL,
	city varchar(20) NOT NULL,
	address varchar(20) NOT NULL,
	email varchar(40),
	phone varchar(15) 
);



CREATE TABLE if not exists users
(
	username varchar(20) NOT NULL PRIMARY KEY,
	first_name varchar(20) NOT NULL,
	last_name varchar(20) NOT NULL,
	password varchar(30) NOT NULL,
	user_type varchar(20) NOT NULL,
	school_id int NOT null,
	FOREIGN KEY (school_id) REFERENCES schools(school_id) ,
	CHECK (user_type="teacher" OR user_type="student")
);


CREATE TABLE if not exists books
(
	isbn char(13) NOT NULL PRIMARY KEY,
	title varchar(40) NOT NULL,
	image blob,
	summary varchar(500),
	no_pages int 
);



CREATE TABLE if not exists keywords
(
	word varchar(20) NOT NULL PRIMARY KEY
);


CREATE TABLE if not exists publishers
(
	id int AUTO_INCREMENT NOT NULL PRIMARY KEY,
	first_name varchar(20) NOT NULL,
	last_name varchar(20)
);


CREATE TABLE if not exists  writers
(
	id int AUTO_INCREMENT NOT NULL PRIMARY KEY,
	first_name varchar(20) NOT NULL,
	last_name varchar(20) NOT null
);



CREATE TABLE if not exists categories
(
	id int AUTO_INCREMENT NOT NULL PRIMARY KEY,
	category_name varchar(30) NOT NULL
);



CREATE TABLE if not exists  reviews
(
	id int AUTO_INCREMENT NOT NULL PRIMARY KEY,
	review_text varchar(500),
	likert int NOT NULL,
	user_id varchar(20),
	FOREIGN KEY (user_id) references users(username) ,
	book_id char(13) not null ,
	FOREIGN KEY (book_id) REFERENCES books(isbn),
	CHECK (likert>=1 AND likert<=5)
);



-- relations N to N
-- relations N to N
-- relations N to N


CREATE TABLE if not exists  schools_books	
(
	school_book_id int auto_increment PRIMARY KEY,
	school_id int, 
	FOREIGN KEY (school_id) REFERENCES schools(school_id),
	book_id char(13), 
	FOREIGN KEY (book_id) REFERENCES books(isbn),
	no_copies int
);


CREATE TABLE if not exists user_book
(
	user_book_id int auto_increment PRIMARY KEY,
	user_id varchar(20),
	FOREIGN KEY (user_id) REFERENCES users(username),
	book_id char(13),
	FOREIGN KEY (book_id) REFERENCES books(isbn),
	reservation_date datetime,
	borrow_date datetime
);




CREATE TABLE if not exists keyword_book
(
	keyword_book_id int auto_increment PRIMARY KEY,
	book_id char(13),
	FOREIGN KEY (book_id) REFERENCES books(isbn),
	keyword varchar(20),
	FOREIGN KEY (keyword) REFERENCES keywords(word)
);

CREATE TABLE IF not exists category_book 
(
    category_book_id INT AUTO_INCREMENT PRIMARY KEY,
    book_id CHAR(13),
    FOREIGN KEY (book_id) REFERENCES books(isbn),
    category_id int,
    FOREIGN KEY (category_id) REFERENCES categories(id)
);



CREATE TABLE if not exists book_writer
(
	book_writer int auto_increment PRIMARY KEY,
	book_id char(13),
	FOREIGN KEY (book_id) REFERENCES books(isbn),
	writer_id int,
	FOREIGN KEY (writer_id) REFERENCES writers(id)
	
);


CREATE TABLE if not exists book_publisher
(
	book_publisher int auto_increment PRIMARY KEY,
	book_id char(13),
	FOREIGN KEY (book_id) REFERENCES books(isbn),
	publisher_id int,
	FOREIGN KEY (publisher_id) REFERENCES publishers(id)
	
);
