import random
from collections import OrderedDict
import faker
from datetime import datetime

fake = faker.Faker()

########################### schools ###########################

DUMMY_DATA_NUMBER = 3
TABLE_NAME = "schools"
TABLE_COLUMNS = ["school_name", "principal_first_name", "principal_last_name","city","address","email","phone"]
content = ""
# fake_IDs = set(fake.unique.random_int(min=100000, max=999999) for i in range(DUMMY_DATA_NUMBER))
school_ids=[i+1 for i in range(DUMMY_DATA_NUMBER)]
for i in range(DUMMY_DATA_NUMBER):


    firstName1 = fake.first_name()
    lastName1 = fake.last_name()
    school_name=fake.unique.company()
    city=fake.city()
    adress=fake.unique.address()
    email=fake.unique.email()
    phone=fake.unique.phone_number()
    content += f'INSERT INTO {TABLE_NAME} ({",".join(TABLE_COLUMNS)}) VALUES ("{school_name}","{firstName1}", "{lastName1}","{city}","{adress}","{email}","{phone}");\n'

########################### students ###########################


DUMMY_DATA_NUMBER = 30
TABLE_NAME = "users"
TABLE_COLUMNS = ["username", "first_name", "last_name", "password","user_type","school_id","birthday"]
student_usernames=[]

school_users=[[],[],[]]
for i in range(DUMMY_DATA_NUMBER):
    username = "user"+str(i)
    student_usernames.append(username)
    firstname=fake.first_name()
    birthday=fake.date()
    lastname = fake.last_name()
    x=random.randint(8,30)
    password=fake.password(length=x)
    school_id=random.choice(school_ids)
    school_users[school_id-1].append(username)
    content += f'INSERT INTO {TABLE_NAME} ({",".join(TABLE_COLUMNS)}) VALUES ("{username}","{firstname}","{lastname}","{password}","student",{school_id},"{birthday}");\n'


########################### teachers ###########################


DUMMY_DATA_NUMBER = 10
TABLE_NAME = "users"
TABLE_COLUMNS = ["username", "first_name", "last_name", "password","user_type","school_id","birthday"]
teacher_usernames=[]


for i in range(DUMMY_DATA_NUMBER):
    username = "user"+str(i+30)
    teacher_usernames.append(username)
    firstname=fake.first_name()
    lastname = fake.last_name()
    x=random.randint(8,30)
    birthday=fake.date()
    password=fake.password(length=x)
    school_id=i%3 + 1
    school_users[school_id - 1].append(username)
    content += f'INSERT INTO {TABLE_NAME} ({",".join(TABLE_COLUMNS)}) VALUES ("{username}","{firstname}","{lastname}","{password}","teacher",{school_id},"{birthday}");\n'
    #operators
    if i>DUMMY_DATA_NUMBER-4:
        username = "user" + str(i + 30+3)
        password = fake.password(length=x)
        content += f'INSERT INTO {TABLE_NAME} ({",".join(TABLE_COLUMNS)}) VALUES ("{username}","{firstname}","{lastname}","{password}","operator",{school_id},"{birthday}");\n'




########################### administrator ###########################


DUMMY_DATA_NUMBER = 1
TABLE_NAME = "users"
TABLE_COLUMNS = ["username", "first_name", "last_name", "password","user_type","school_id", "birthday"]




username = "administrator"
firstname=fake.first_name()
lastname = fake.last_name()
x=random.randint(8,30)
birthday=fake.date()
password=fake.password(length=x)
content += f'INSERT INTO {TABLE_NAME} ({",".join(TABLE_COLUMNS)}) VALUES ("{username}","{firstname}","{lastname}","{password}","administrator",NULL,"{birthday}");\n'

########################### books ###########################

TABLE_NAME = "books"
TABLE_COLUMNS = ["isbn", "title", "publisher",
                 "image_url", "summary", "no_pages", "keywords"]
DUMMY_DATA_NUMBER = 100
isbns=[]


for i in range(DUMMY_DATA_NUMBER):
    isbn=fake.unique.isbn10()

    isbns.append(isbn)
    w=random.randint(1,8)
    title=fake.text(max_nb_chars=w*5)
    publisher=fake.first_name()+" "+fake.last_name()


    w=random.randint(3,5)
    summary=fake.paragraph(nb_sentences=w)
    no_pages=random.randint(50,600)
    w=random.randint(1,6)
    keywords_list=fake.words(nb=w)
    keywords=""
    for x in keywords_list:
        keywords+=x+","
    keywords=keywords[:-1]
    content += f'INSERT INTO {TABLE_NAME} ({",".join(TABLE_COLUMNS)}) VALUES ("{isbn}","{title}","{publisher}","/photos/book_image.png","{summary}",{no_pages},"{keywords}");\n'

########################### writer ###########################

TABLE_NAME = "writers"
TABLE_COLUMNS = ["first_name", "last_name"]
DUMMY_DATA_NUMBER = 30
writer_ids=[]
for i in range(DUMMY_DATA_NUMBER):
    writer_ids.append(i+1)
    firstname=fake.first_name()
    lastname=fake.unique.last_name()
    content += f'INSERT INTO {TABLE_NAME} ({",".join(TABLE_COLUMNS)}) VALUES ("{firstname}","{lastname}");\n'


########################### categories ###########################

TABLE_NAME = "categories"
TABLE_COLUMNS = ["category_name"]
DUMMY_DATA_NUMBER = 10
categories=["history","literature","science fiction","math","physics","biology","technology","geography","music","arts"]
for i in categories:
    content += f'INSERT INTO {TABLE_NAME} ({",".join(TABLE_COLUMNS)}) VALUES ("{i}");\n'






########################### schools-books ###########################

TABLE_NAME = "schools_books"
TABLE_COLUMNS = ["school_id","book_id","no_copies"]
DUMMY_DATA_NUMBER = 200
school_book=[[],[],[]]
for i in range(DUMMY_DATA_NUMBER):
    no_copies=random.randint(1,40)
    school_id=random.choice(school_ids)
    book_id=random.choice(isbns)
    school_book[school_id-1].append(book_id)
    content += f'INSERT INTO {TABLE_NAME} ({",".join(TABLE_COLUMNS)}) VALUES ({school_id},"{book_id}",{no_copies});\n'




########################### reviews ###########################

TABLE_NAME = "reviews"
TABLE_COLUMNS = ["review_text","likert","user_id","book_id", "published"]
DUMMY_DATA_NUMBER = 70
for i in range(DUMMY_DATA_NUMBER):
    review_text=fake.text(max_nb_chars=300)
    likert=random.randint(1,5)
    sc=random.choice(school_ids)
    user_id=random.choice(school_users[sc-1])
    book_id=random.choice(school_book[sc-1])
    content += f'INSERT INTO {TABLE_NAME} ({",".join(TABLE_COLUMNS)}) VALUES ("{review_text}",{likert},"{user_id}","{book_id}",1);\n'


########################### reservations ###########################

TABLE_NAME = "reservations"
TABLE_COLUMNS = ["user_id","book_id","reservation_date"]
DUMMY_DATA_NUMBER = 40
for i in range(DUMMY_DATA_NUMBER):
    reservation=fake.date_time_between(start_date='-7d')
    sc = random.choice(school_ids)
    user_id = random.choice(school_users[sc - 1])
    book_id = random.choice(school_book[sc - 1])
    content += f'INSERT INTO {TABLE_NAME} ({",".join(TABLE_COLUMNS)}) VALUES ("{user_id}","{book_id}","{reservation}");\n'


########################### borrowings ###########################

TABLE_NAME = "borrowings"
TABLE_COLUMNS = ["user_id","book_id","borrow_date","returned"]
DUMMY_DATA_NUMBER = 200
for i in range(DUMMY_DATA_NUMBER):
    borrow=fake.date_time_between(start_date='-30d')
    sc = random.choice(school_ids)
    user_id = random.choice(school_users[sc - 1])
    book_id = random.choice(school_book[sc - 1])

    a=random.uniform(0,1)
    returned=(a>0.3)
    if returned:
        a=1
    else:
        a=0
    content += f'INSERT INTO {TABLE_NAME} ({",".join(TABLE_COLUMNS)}) VALUES (\'{user_id}\',\'{book_id}\',\'{borrow}\',{a});\n'



########################### category-book ###########################

TABLE_NAME = "category_book"
TABLE_COLUMNS = ["book_id","category_id"]
DUMMY_DATA_NUMBER = 70
for i in isbns:
    book_id=i
    category=random.randint(1,len(categories))
    content += f'INSERT INTO {TABLE_NAME} ({",".join(TABLE_COLUMNS)}) VALUES ("{book_id}",{category});\n'
for i in range(20):
    book_id = random.choice(isbns)
    category = random.randint(1,len(categories))
    content += f'INSERT INTO {TABLE_NAME} ({",".join(TABLE_COLUMNS)}) VALUES ("{book_id}",{category});\n'

########################### book-writer ###########################

TABLE_NAME = "book_writer"
TABLE_COLUMNS = ["book_id","writer_id"]
DUMMY_DATA_NUMBER = 70
for i in isbns:
    book_id=i
    writer=random.choice(writer_ids)
    content += f'INSERT INTO {TABLE_NAME} ({",".join(TABLE_COLUMNS)}) VALUES ("{book_id}",{writer});\n'
for i in range(20):
    book_id = random.choice(isbns)
    writer = random.choice(writer_ids)
    content += f'INSERT INTO {TABLE_NAME} ({",".join(TABLE_COLUMNS)}) VALUES ("{book_id}",{writer});\n'

f = open("dummy_data.sql", "w", encoding="utf-8")
f.write(content)
