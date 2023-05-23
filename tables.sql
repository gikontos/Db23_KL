



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
	publisher varchar(40) not null,
	image blob,
	summary varchar(500),
	no_pages int
);



CREATE TABLE if not exists keywords
(
	word varchar(20) NOT NULL PRIMARY KEY
);

/*
CREATE TABLE if not exists publishers
(
	id int AUTO_INCREMENT NOT NULL PRIMARY KEY,
	first_name varchar(20) NOT NULL,
	last_name varchar(20)
);
*/

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
	review_text varchar(500),
	likert int NOT NULL,
	user_id varchar(20),
	FOREIGN KEY (user_id) references users(username) ,
	book_id char(13) not null ,
	FOREIGN KEY (book_id) REFERENCES books(isbn),
	primary key (book_id,user_id),
	CHECK (likert>=1 AND likert<=5)
);



-- relations N to N
-- relations N to N
-- relations N to N


CREATE TABLE if not exists  schools_books	
(
	
	school_id int, 
	FOREIGN KEY (school_id) REFERENCES schools(school_id),
	book_id char(13), 
	FOREIGN KEY (book_id) REFERENCES books(isbn),
	primary key (school_id,book_id),
	no_copies int
);


CREATE TABLE if not exists reservations
(
	user_id varchar(20),
	FOREIGN KEY (user_id) REFERENCES users(username),
	book_id char(13),
	FOREIGN KEY (book_id) REFERENCES books(isbn),
	reservation_date datetime default current_timestamp,
	primary key (user_id,book_id)
);

CREATE TABLE if not exists borrowings
(
	user_id varchar(20),
	FOREIGN KEY (user_id) REFERENCES users(username),
	book_id char(13),
	FOREIGN KEY (book_id) REFERENCES books(isbn),
	borrow_date datetime default current_timestamp,
	primary key (user_id,book_id),
	duration_in_days int not null,
	check (duration_in_days>0),
	returned boolean default false
);




CREATE TABLE if not exists keyword_book
(
	
	book_id char(13),
	FOREIGN KEY (book_id) REFERENCES books(isbn),
	keyword varchar(20),
	FOREIGN KEY (keyword) REFERENCES keywords(word),
	primary key (book_id,keyword)
);

CREATE TABLE IF not exists category_book 
(
    book_id CHAR(13),
    FOREIGN KEY (book_id) REFERENCES books(isbn),
    category_id int,
    FOREIGN KEY (category_id) REFERENCES categories(id),
	primary key (book_id,category_id)
);



CREATE TABLE if not exists book_writer
(
	
	book_id char(13),
	FOREIGN KEY (book_id) REFERENCES books(isbn),
	writer_id int,
	FOREIGN KEY (writer_id) REFERENCES writers(id),
	primary key (book_id,writer_id)	
	
);

/*
CREATE TABLE if not exists book_publisher
(
	
	book_id char(13),
	FOREIGN KEY (book_id) REFERENCES books(isbn),
	publisher_id int,
	FOREIGN KEY (publisher_id) REFERENCES publishers(id),
	primary key (book_id,publisher_id)
	
);*/

--delete reservations after a week
SET GLOBAL event_scheduler = ON;

CREATE EVENT IF NOT EXISTS delete_reservation_event
ON SCHEDULE EVERY 1 DAY
COMMENT 'Delete entries older than one week'
DO
    DELETE FROM reservations
    WHERE reservation_date <= NOW() - INTERVAL 1 WEEK;



DELIMITER $ --handling more than two reservations from user per week
CREATE TRIGGER check_two_reservations
BEFORE INSERT ON reservations
FOR EACH ROW
BEGIN
    DECLARE count INT;
    declare u_type varchar(20);
    SELECT COUNT(*) INTO count
    FROM reservations
    WHERE (user_id=new.user_id) and reservation_date>=date_sub(current_date, INTERVAL 1 week);
	SELECT user_type into u_type
	from users
	where (username=new.user_id);
    
    IF (count >= 2) or (count>=1 and u_type="teacher") THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Cannot reserve. Maximum entries reached for the user in a week.';
  	END IF;
END$
DELIMITER ;


DELIMITER $ --handling more than two borrowings from user per week
CREATE TRIGGER check_two_borrowings
BEFORE INSERT ON borrowings
FOR EACH ROW
BEGIN
    DECLARE count INT;
    declare u_type varchar(20);
    SELECT COUNT(*) INTO count
    FROM borrowings
    WHERE (user_id=new.user_id) and borrow_date>=date_sub(current_date, INTERVAL 1 week);
	SELECT user_type into u_type
	from users
	where (username=new.user_id);
    
    IF (count >= 2) or (count>=1 and u_type="teacher") THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Cannot borrow. Maximum entries reached for the user in a week.';
  	END IF;
END$
DELIMITER ;

DELIMITER $ --handling pending return

CREATE TRIGGER check_delayed_return BEFORE INSERT ON reservations
FOR EACH ROW
BEGIN
  DECLARE flag_value BOOLEAN;
  
  -- Check if any existing row for the same user_id has flag_column false and date_column more than 5 days in the past
  SELECT EXISTS(
    SELECT 1
    FROM borrowings
    WHERE user_id = NEW.user_id
      AND returned = FALSE
      AND borrow_date <= DATE_SUB(CURRENT_DATE, INTERVAL duration_in_days DAY)
  ) INTO flag_value;
  
  -- If there is a matching row, raise an error
  IF flag_value = TRUE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Cannot insert. Return pending.';
  END IF;
  
END$

DELIMITER ;


DELIMITER $ --handling reservation for a book that is at the same time lended to the user

CREATE TRIGGER check_already_borrowed BEFORE INSERT ON reservations
FOR EACH ROW
BEGIN
  DECLARE flag_value BOOLEAN;
  
  
  SELECT EXISTS(
    SELECT 1
    FROM borrowings
    WHERE user_id = NEW.user_id
      AND returned = FALSE
	  and book_id = new.book_id
      AND borrow_date >= DATE_SUB(CURRENT_DATE, INTERVAL duration_in_days DAY)
  ) INTO flag_value;
  
  -- If there is a matching row, raise an error
  IF flag_value = TRUE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Cannot insert. You have this book now.';
  END IF;
  
END$

DELIMITER ;