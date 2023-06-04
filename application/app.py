from flask import Flask,request, render_template,redirect ,url_for,session,send_from_directory,send_file
import MySQLdb
from flask_mysqldb import MySQL
from datetime import datetime, timedelta
from datetime import date as datetime_date
import subprocess

app = Flask(__name__)
app.secret_key = 'any random string'

#να κανουμε τους types operator,administrator αντι για το relationship
#αλλαγη περιοδου δανεισμου σε μία βδομαδα

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'LibraryManagement'

mysql=MySQL(app)

def check_login(arguement,s):
    if not session.get(arguement):
            session.pop(arguement, None)
            return redirect(s)


@app.route('/', methods=["GET","POST"])
def index():
    # Connect to the MariaDB database
    session.clear()
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        
        
        cur = mysql.connection.cursor()
        # Execute a query to fetch the user record
        cur.execute("SELECT password,user_type,school_id,enabled FROM users WHERE username = %s", (username,))

        # Fetch the result
        password_correct = cur.fetchone()
        
        try:
            if password_correct[0] == password:
                if password_correct[3]==0:
                    return "Account disabled, contact the operator"

                session["user"]=username
        
                
                if password_correct[1]=="administrator":
                    session['{}'.format(username)]=True
                    return redirect('/admin')
                

                if password_correct[1]=="operator":
                    session['{}'.format(username)]=True
                    return redirect('/operator/{}'.format(username))
                
                session['{}'.format(username)]=True
                return redirect('/user/{}'.format(username))
            else:
                # Invalid username or password
                error = 'Invalid credentials. Please try again.'
                return render_template('login.html', error=error)
        except:
            error = 'Invalid credentials. Please try again.'
            return render_template('login.html', error=error)

    return render_template("login.html")

@app.route('/photos/<path:filename>')
def get_photo(filename):
    return send_from_directory('photos', filename)




@app.route('/book/<arguement>', methods=["GET","POST"])
def book_page(arguement):
    cur=mysql.connection.cursor()
    cur.execute("select title,keywords,summary,no_pages,publisher,image_url from books where isbn=%s",(arguement,))
    a=cur.fetchone()
    result=a
    cur.execute("select first_name, last_name from books join book_writer on book_id=isbn join writers on writer_id=id where isbn=%s",(arguement,))
    a=cur.fetchall()
    writers=[i[0]+" "+i[1] for i in a]
    writers=", ".join(writers)
    cur.execute("select category_name from books join category_book on book_id=isbn join categories on category_id=id where isbn=%s",(arguement,))
    a=cur.fetchall()
    categories=[i[0] for i in a]
    categories=",".join(categories)

    cur.execute("select user_id,likert,review_text from reviews where published=%s and book_id=%s",("1",arguement))
    reviews=cur.fetchall()

    return render_template("book_page.html",isbn=arguement,title=result[0],keywords=result[1],summary=result[2],no_pages=result[3],publisher=result[4],image=result[5], writers=writers,categories=categories,reviews=reviews)

@app.route("/user/<username>/review/<isbn>", methods=["GET","POST"])
def review(username,isbn):
    cur=mysql.connection.cursor()
    cur.execute("select title from books where isbn=%s",(isbn,))
    title=cur.fetchone()[0]
    if "submit" in request.form:
         
         
         cur.execute("insert into reviews (user_id,book_id,likert,review_text) values (%s,%s,%s,%s) ",(username,isbn,request.form.get("likert"),request.form.get("paragraph")))  
         mysql.connection.commit()
         return redirect("/user/{}".format(username))   

    return render_template("create_review.html",username=username,isbn=isbn, title=title)

@app.route('/user/<username>/info', methods=["GET","POST"])
def user_info(username):

    if not session.get(username):
        session.pop(username, None)
        return redirect('/')

    cur=mysql.connection.cursor()
    cur.execute("select first_name,last_name,password,birthday,user_type from users where username=%s",(username,))
    result=cur.fetchone()

    if "save" in request.form:
        if result[4]=="student":
            password=request.form.get("password")
            cur.execute("update users set password=%s where username=%s",(password,username))
            mysql.connection.commit()
            return redirect("/user/{}".format(username))
        else:
            password=request.form.get("password")
            first_name=request.form.get("first_name")
            last_name=request.form.get("last_name")
            birthday=request.form.get("birthday")
            cur.execute("update users set password=%s, first_name=%s, last_name=%s,birthday=%s where username=%s",(password,first_name,last_name,birthday,username))
            mysql.connection.commit()
            return redirect("/user/{}".format(username))
    cur.execute("select isbn,title,likert,review_text,published from reviews join books on book_id=isbn join users on username=user_id where username=%s",(username,))
    reviews=cur.fetchall()
    if "isbn" in request.form:
        isbn=request.form.get("isbn")
        likert=request.form.get("likert")
        text=request.form.get("text")
        cur.execute("update reviews set likert=%s, review_text=%s,published=%s where user_id=%s and book_id=%s",(likert,text,"0",username,isbn))
        mysql.connection.commit()
        return redirect("/user/{}/info".format(username))


    return render_template("user_info.html",username=username,first_name=result[0],last_name=result[1],password=result[2],birthday=result[3],user_type=result[4],reviews=reviews)



@app.route('/user/<arguement>', methods=["GET","POST"])
def user_page(arguement):
    if not session.get(arguement):
            session.pop(arguement, None)
            return redirect('/')
    
    if "review" in request.form:
         isbn=request.form.get("review")
         cur=mysql.connection.cursor()
         cur.execute("select exists (select * from reviews where user_id=%s and book_id=%s)",(arguement,isbn))
         a=cur.fetchone()[0]
         if int(a):
              return "you have already reviewed that book, edit the review instead"
         else:
            return redirect("/user/{}/review/{}".format(arguement,isbn))

    if "reserve" in request.form:
        pressed_button=request.form.get("reserve")
        cur=mysql.connection.cursor()
        try:
            cur.execute("insert into reservations (user_id,book_id) values (%s,%s)",(arguement,session["available_isbns"][int(pressed_button)]))
            mysql.connection.commit()
        except MySQLdb.OperationalError as e:
    
            error_message = str(e)
            return error_message
    if "form2" in request.form:
        arguement=session["user"]
        writer_check=''
        category_check=''
        title_check=''
        writer=request.form.get("writer2", "")
        title=request.form.get("title2", "")
        category=request.form.get("category2", "")
        session["writer2"]=writer
        session["title2"]=title
        session["category2"]=category
        writer1=session["writer1"]
        category1=session["category1"]
        title1=session["title1"]
        
        param =(arguement,)
        if title!="":
            title_check="and books.title LIKE %s"
            param+=("%%"+title+"%%",)
            
        if category!="":
            category_check="and categories.category_name LIKE %s"  
            param+=("%%"+category+"%%",)
        if writer!="":
            writer_check="and CONCAT(writers.first_name,\" \",writers.last_name) LIKE %s"  
            param+=("%%"+writer+"%%",)
        cur = mysql.connection.cursor()
        cur.execute("select distinct title,isbn,returned,borrow_date from users join borrowings on username=user_id join books on book_id=isbn join category_book on category_book.book_id=isbn join categories on category_book.category_id=categories.id join book_writer on book_writer.book_id=isbn join writers on writers.id=book_writer.writer_id where users.username=%s "+title_check+category_check+writer_check,param)
        result=cur.fetchall()
        borrowed_titles = [row[0] for row in result]
        borrowed_isbns = [row[1] for row in result]
        borrowed_status=[row[2] for row in result]
        date=[row[3] for row in result]
        titles=[]
        borrowed_text=[]
        for i in range(len(borrowed_status)):
            if borrowed_status[i]:
              borrowed_text.append("returned")
              titles.append("borrowed on "+str(date[i].date()))
            else:
              endson=date[i].date()+timedelta(days=7)
              if datetime_date.today()>endson:
                   borrowed_text.append("delayed")
                   titles.append("you should  have returned it by "+str(endson))
              else:
                    borrowed_text.append("ongoing")
              
                    titles.append("return by "+str(endson))
        session["borrowed_titles"]=borrowed_titles
        session["borrowed_isbns"]=borrowed_isbns
        session["borrowed_text"]=borrowed_text
        session["titles"]=titles
        available_titles = session["available_titles"]
        available_isbns=session["available_isbns"]
        reservation_titles=session["reservation_titles"]
        reservation_isbns=session["reservation_isbns"]
        reservation_date=session["reservation_date"]
             
        cur.close()
        return render_template("user_dashboard.html",username=arguement,available_books=available_titles,borrowed_books=borrowed_titles,writer2=writer,category2=category,title2=title,title1=title1,category1=category1,writer1=writer1,available_isbns=available_isbns,status=borrowed_text,titles=titles,reservation_date=reservation_date,reservations=reservation_titles,reservation_isbns=reservation_isbns) 
    if "form1" in request.form:
        arguement=session["user"]
        writer_check=''
        category_check=''
        title_check=''
        writer=request.form.get("writer1", "")
        title=request.form.get("title1", "")
        
        category=request.form.get("category1", "")

        session["writer1"]=writer
        session["title1"]=title
        session["category1"]=category
        writer2=session["writer2"]
        category2=session["category2"]
        title2=session["title2"]

        for i in [writer2,title2,category2]:
            if i==None: i=""
              
        param =(arguement,)
        if title!="":
            title_check="and books.title LIKE %s"
            param+=("%%"+title+"%%",)
            
        if category!="":
            category_check="and categories.category_name LIKE %s"  
            param+=("%%"+category+"%%",)
        if writer!="":
            writer_check="and ((CONCAT(writers.first_name,\" \",writers.last_name) LIKE %s) or (CONCAT(writers.last_name,\" \",writers.first_name) LIKE %s)"  
            param+=("%%"+writer+"%%",)
            param+=("%%"+writer+"%%",)
        cur = mysql.connection.cursor()
        cur.execute("select distinct title,isbn from users join schools on users.school_id=schools.school_id join schools_books on schools.school_id=schools_books.school_id join books on schools_books.book_id=isbn join category_book on category_book.book_id=isbn join categories on category_book.category_id=categories.id join book_writer on book_writer.book_id=isbn join writers on writers.id=book_writer.writer_id where users.username=%s "+title_check+category_check+writer_check,param)
        result=cur.fetchall()
        available_titles = [row[0] for row in result]
        session["available_titles"]=available_titles
        available_isbns = [row[1] for row in result]
        session["available_isbns"]=available_isbns
        borrowed_titles = session["borrowed_titles"]
        borrowed_text = session["borrowed_text"]
        titles = session["titles"]
        reservation_titles=session["reservation_titles"]
        reservation_isbns=session["reservation_isbns"]
        reservation_date=session["reservation_date"]
        
        cur.close()
        return render_template("user_dashboard.html",username=arguement,available_books=available_titles,borrowed_books=borrowed_titles,writer1=writer,category1=category,title1=title,title2=title2,category2=category2,writer2=writer2,available_isbns=available_isbns,status=borrowed_text,titles=titles,reservation_date=reservation_date,reservations=reservation_titles,reservation_isbns=reservation_isbns) 
      
    if "remove" in request.form:
        isbn=request.form.get("remove")
        cur=mysql.connection.cursor()
        cur.execute("delete from reservations where user_id=%s and book_id=%s",(arguement,isbn))
        mysql.connection.commit()
        return redirect("/user/{}".format(arguement))
    cur = mysql.connection.cursor()
    cur.execute("select distinct title,isbn from users join schools on users.school_id=schools.school_id join schools_books on schools.school_id=schools_books.school_id join books on schools_books.book_id=isbn where users.username=%s",(arguement,))
    result = cur.fetchall()
    available_titles = [row[0] for row in result]
    available_isbns = [row[1] for row in result]
    cur.execute("select distinct title,isbn,returned,borrow_date from users join borrowings on user_id=username join books on book_id=isbn where username=%s",(arguement,))
    result = cur.fetchall()
    borrowed_titles = [row[0] for row in result]
    borrowed_isbns = [row[1] for row in result]
    borrowed_status=[row[2] for row in result]
    date=[row[3] for row in result]
    titles=[]
    borrowed_text=[]
    for i in range(len(borrowed_status)):
         if borrowed_status[i]:
              borrowed_text.append("returned")
              titles.append("borrowed on "+str(date[i].date()))
         else:
              endson=date[i].date()+timedelta(days=7)
              if datetime_date.today()>endson:
                   borrowed_text.append("delayed")
                   titles.append("you should  have returned it by "+str(endson))
              else:
                    borrowed_text.append("ongoing")
              
                    titles.append("return by "+str(endson))
    cur.execute("select title,reservation_date,isbn from users join reservations on username=user_id join books on book_id=isbn where username=%s",(arguement,))
    result=cur.fetchall()
    reservation_titles=[row[0] for row in result]
    reservation_date=[str(row[1]) for row in result]
    reservation_isbns=[row[2] for row in result]

    session["borrowed_titles"]=borrowed_titles
    session["available_titles"]=available_titles
    session["borrowed_isbns"]=borrowed_isbns
    session["available_isbns"]=available_isbns
    session["borrowed_text"]=borrowed_text
    session["titles"]=titles
    session["reservation_titles"]=reservation_titles
    session["reservation_isbns"]=reservation_isbns
    session["reservation_date"]=reservation_date
    
    session["writer1"]=""
    session["title1"]=""
    session["category1"]=""
    session["writer2"]=""
    session["title2"]=""
    session["category2"]=""
    cur.close()
    
    return render_template("user_dashboard.html",username=arguement,available_books=available_titles,borrowed_books=borrowed_titles,available_isbns=available_isbns,status = borrowed_text, titles=titles,reservation_date=reservation_date,reservations=reservation_titles,reservation_isbns=reservation_isbns)


@app.route("/admin/operators_same_number", methods=["GET","POST"])
def operators_same_number():
    if not session.get('administrator'):
            session.pop('administrator', None)
            return redirect('/')
    cur=mysql.connection.cursor()
    
    cur.execute("select distinct u1.first_name, u1.last_name, u1.school_id, u2.first_name,u2.last_name, u2.school_id ,(select count(*)  from borrowings join users on user_id=username where school_id=u1.school_id and borrow_date>=DATE_SUB(CURDATE(), INTERVAL 1 YEAR))  from users u1 join users u2 on u1.school_id!=u2.school_id where (select count(*)  from borrowings join users on user_id=username where school_id=u1.school_id and borrow_date>=DATE_SUB(CURDATE(), INTERVAL 1 YEAR))>20 and (u1.first_name,u1.last_name,u2.first_name,u2.last_name)<(u2.first_name,u2.last_name,u1.first_name,u1.last_name) and u1.user_type=%s and u2.user_type=%s and (select count(*) from borrowings join users on username=user_id where school_id=u1.school_id and borrow_date>=DATE_SUB(CURDATE(), INTERVAL 1 YEAR))=(select count(*) from borrowings join users on username=user_id where school_id=u2.school_id and borrow_date>=DATE_SUB(CURDATE(), INTERVAL 1 YEAR)) group by u1.first_name,u1.last_name,u2.first_name,u2.last_name;",("operator","operator"))

    data=cur.fetchall()
    schools=[]
    for i in data:
        cur.execute("select school_name from schools where school_id=%s",(i[2],))
        a=cur.fetchone()[0]
        cur.execute("select school_name from schools where school_id=%s",(i[5],))
        b=cur.fetchone()[0]
        schools.append([a,b])


    return render_template("operators_same_number.html",data=data,schools=schools)


@app.route("/admin/writers_5_books_less", methods=["GET","POST"])
def writers_5_books_less():
    if not session.get('administrator'):
            session.pop('administrator', None)
            return redirect('/')
    cur=mysql.connection.cursor()
    cur.execute("""
    SELECT first_name, last_name, c
    FROM (
        SELECT first_name, last_name, COUNT(*) AS c
        FROM writers
        JOIN book_writer ON writer_id = id
        GROUP BY first_name, last_name
    ) AS subquery
    WHERE c < (SELECT MAX(c) FROM (
        SELECT COUNT(*) AS c
        FROM writers
        JOIN book_writer ON writer_id = id
        GROUP BY writer_id
    ) AS subsubquery) - 4
    ORDER BY c DESC
""")

    data=cur.fetchall()
    cur.execute("select first_name,last_name,count(*) as c from writers join book_writer on writers.id=book_writer.writer_id group by first_name,last_name order by c desc")

    writer=cur.fetchall()[0]

    return render_template("writers_5_books_less.html",data=data,writer=writer)


@app.route("/admin/popular_cat_pairs", methods=["GET","POST"])
def popular_cat_pairs():
    if not session.get('administrator'):
            session.pop('administrator', None)
            return redirect('/')
    cur=mysql.connection.cursor()
    cur.execute("SELECT c1.category_name, c2.category_name, COUNT(*) AS category_count FROM books JOIN category_book cb1 ON books.isbn = cb1.book_id JOIN category_book cb2 ON books.isbn = cb2.book_id JOIN categories c1 ON cb1.category_id = c1.id JOIN categories c2 ON cb2.category_id = c2.id JOIN borrowings ON borrowings.book_id = books.isbn WHERE c1.category_name < c2.category_name GROUP BY c1.category_name, c2.category_name ORDER BY category_count DESC")
    data=cur.fetchall()



    return render_template("popular_cat_pairs.html",data=data)

@app.route("/admin/unpopular_writers", methods=["GET","POST"])
def unpopular_writers():
    if not session.get('administrator'):
            session.pop('administrator', None)
            return redirect('/')
    cur=mysql.connection.cursor()
    cur.execute("select first_name, last_name from writers where id not in (select writer_id from borrowings join book_writer on borrowings.book_id=book_writer.book_id)")
    data=cur.fetchall()



    return render_template("unpopular_writers.html",data=data)

@app.route("/admin/backup",methods=["GET","POST"])
def backup():
    if not session.get('administrator'):
            session.pop('administrator', None)
            return redirect('/')
    try:
        # Define the command to execute mysqldump
        cmd = 'mysqldump -u root  librarymanagement > backup.sql'
        
        # Execute the command as a subprocess
        subprocess.run(cmd, shell=True, check=True)
        
        # Return a success message or redirect to another page
        
        return send_file(
                'backup.sql',
                as_attachment=True                
            )
    except subprocess.CalledProcessError as e:
        # Handle any errors that occur during the backup process
        return f"Backup failed: {str(e)}"

@app.route("/admin/restore", methods=["GET", "POST"])
def restore():
    if not session.get('administrator'):
        session.pop('administrator', None)
        return redirect('/')

    if request.method=="POST":
        if 'file' not in request.files:
            return "No file uploaded"

        file = request.files['file']

        if file.filename == '':
            return "No file selected"

        try:
            # Save the uploaded file
            file.save('restore.sql')

            # Define the command to restore the database
            cmd = 'D:/mariadb/download/bin/mysql -u root librarymanagement < restore.sql'

            # Execute the command as a subprocess
            subprocess.run(cmd, shell=True, check=True)

            # Return a success message or redirect to another page
            return "Database restored successfully!"
        except subprocess.CalledProcessError as e:
            # Handle any errors that occur during the restoration process
            return f"Restore failed: {str(e)}"
    return render_template("restore.html")


@app.route("/admin/young_teachers", methods=["GET","POST"])
def young_teachers():
    if not session.get('administrator'):
            session.pop('administrator', None)
            return redirect('/')
    cur=mysql.connection.cursor()
    cur.execute("select first_name,last_name,count(*) as count from users join borrowings on borrowings.user_id=username where birthday>=DATE_SUB(CURDATE(), INTERVAL 40 YEAR) and user_type=%s group by username order by count desc",("teacher",))
    data=cur.fetchall()

    return render_template("young_teachers.html",data=data)

@app.route("/admin/writers_teachers", methods=["GET","POST"])
def writers_teachers():
    if not session.get('administrator'):
            session.pop('administrator', None)
            return redirect('/')
    cur=mysql.connection.cursor()
    if "category" in request.form:
        category_id=request.form.get("category")
        cur.execute("select writers.first_name,writers.last_name from writers join book_writer on book_writer.writer_id=writers.id join books on books.isbn=book_writer.book_id join category_book on category_book.book_id=isbn where category_book.category_id=%s",(category_id,))
        writers=cur.fetchall()
        cur.execute("select category_name,id from categories")
        result=cur.fetchall()

        cur.execute("select users.first_name,users.last_name from users join borrowings on borrowings.user_id=username join books on borrowings.book_id=isbn join category_book on category_book.book_id=isbn where category_book.category_id=%s and user_type=%s and borrow_date>= DATE_SUB(CURDATE(), INTERVAL 1 YEAR)",(category_id,"teacher"))
        teachers=cur.fetchall()
        cur.execute("select category_name from categories where id=%s",(category_id,))
        category=cur.fetchone()[0]
        return render_template("writers_teachers.html",writers=writers,teachers=teachers,categories=result,category=category)

        

    
    cur.execute("select category_name,id from categories")
    result=cur.fetchall()

    return render_template("writers_teachers.html",writers=[],teachers=[],categories=result)


@app.route('/admin/borrowings', methods=["GET","POST"])
def show_borrowings():
    if not session.get('administrator'):
            session.pop('administrator', None)
            return redirect('/')
    
    cur=mysql.connection.cursor()
    cur.execute("select school_id,school_name from schools")
    schools=cur.fetchall()
    

    if "school" in request.form:
        school_id=request.form.get("school")
        session["school_id"]=school_id
        cur.execute("select first_name,last_name,title,borrow_date,returned from borrowings join users on user_id=username join schools on schools.school_id=users.school_id join books on isbn=book_id where schools.school_id=%s",(school_id,))
        data=cur.fetchall()
        cur.execute("select school_name from schools where school_id=%s",(school_id,))
        sname=cur.fetchone()[0]
        return render_template("borrowings.html",schools=schools,data=data,sname=sname)


    if "search" in request.form:
        school_id=session["school_id"]
        y=request.form.get("year")
        m=request.form.get("month")
        year=""
        month=""
        if y!="":
            year=" and YEAR(borrow_date) ={}".format(y)
        if m!="":    
            month=" and MONTH(borrow_date) ={}".format(m)
        cur.execute("select first_name,last_name,title,borrow_date,returned from borrowings join users on user_id=username join schools on schools.school_id=users.school_id join books on isbn=book_id where schools.school_id=%s"+year+month,(school_id,))
        data=cur.fetchall()
        cur.execute("select school_name from schools where school_id=%s",(school_id,))
        sname=cur.fetchone()[0]
        return render_template("borrowings.html",schools=schools,data=data,sname=sname,year=y,month=m)
        

    
    


    return render_template("borrowings.html",schools=schools,data=[])


@app.route('/schools', methods=["GET","POST"])
def schools():
    if not session.get('administrator'):
            session.pop('administrator', None)
            return redirect('/')
    
    
    cur=mysql.connection.cursor()
    
    cur.execute("select school_name,school_id,principal_first_name,principal_last_name,city,address,email,phone from schools")
    result=cur.fetchall()
    
    operators=[]
    for i in result:
        cur.execute("select first_name,last_name,username from users join schools on schools.school_id=users.school_id where schools.school_id=%s and user_type=%s",(i[1],"operator"))
        a=cur.fetchone()

        if a==None:
            operators.append(["-","-","-"])
        else:
            operators.append([a[0],a[1],a[2]])
    

    if "edit" in request.form:
        number=request.form.get("edit")
        data=result[int(number)]
        operator=operators[int(number)]
        session["operator"]=operator
        session["data"]=data
        
        return render_template("edit_school.html",data=data,operator=operator)
    
    

    if "delete" in request.form:
        number=request.form.get("delete")
        
        school=result[int(number)]
        cur.execute("delete from schools where school_id =%s",(school[1],))
        mysql.connection.commit()
        cur.execute("select school_name,school_id,principal_first_name,principal_last_name,city,address,email,phone from schools")
        result=cur.fetchall()
        
        operators=[]
        for i in result:
            cur.execute("select first_name,last_name,username from users join schools on schools.school_id=users.school_id where schools.school_id=%s and user_type=%s",(i[1],"operator"))
            a=cur.fetchone()

            if a==None:
                operators.append(["-","-","-"])
            else:
                operators.append([a[0],a[1],a[2]])
        
        return render_template("schools.html",data=result,operators=operators)
        

    
    
    if "apply" in request.form:
        school_name=request.form.get("school_name")
        p_fn=request.form.get("p_fn")
        p_ln=request.form.get("p_ln")
        city=request.form.get("city")
        address=request.form.get("address")
        email=request.form.get("email")
        phone=request.form.get("phone")
        if request.form.get("checkbox")=="True":
            cur.execute("delete from users where username=%s",(session["operator"][2],))
        cur.execute("update schools set school_name=%s,principal_first_name=%s,principal_last_name=%s,city=%s,address=%s,email=%s,phone=%s where school_id=%s",(school_name,p_fn,p_ln,city,address,email,phone,int(session["data"][1])))
        mysql.connection.commit()
        return redirect("/schools")
        
        


    
    return render_template("schools.html",data=result,operators=operators)

@app.route('/admin/insert_school', methods=["GET","POST"])
def insert_school():
    if not session.get('administrator'):
        session.pop('administrator', None)
        return redirect('/')
    if "register" in request.form:
        try:
            name=request.form.get("name")
            city=request.form.get("city")
            address=request.form.get("address")
            pfn=request.form.get("principal_fn")
            pln=request.form.get("principal_ln")
            email=request.form.get("email")
            phone=request.form.get("phone")
            cur=mysql.connection.cursor()
            cur.execute("insert into schools (school_name,principal_first_name,principal_last_name,city,address,email,phone) values (%s,%s,%s,%s,%s,%s,%s)",(name,pfn,pln,city,address,email,phone))
            mysql.connection.commit()
        except MySQLdb.IntegrityError as e:
    
            error_message = str(e)
            return error_message
    return render_template("insert_school.html")

@app.route('/admin', methods=["GET","POST"])
def admin_dashboard():
        if not session.get('administrator'):
            session.pop('administrator', None)
            return redirect('/')
        return render_template("administrator_dashboard.html")

@app.route('/admin/operator_requests', methods=["GET","POST"])
def operator_requests():
    cur=mysql.connection.cursor()
    if not session.get('administrator'):
            session.pop('administrator', None)
            return redirect('/')
    if "reject" in request.form:
        result=session["result"]
        a=request.form.get("reject")
        operator=result[int(a)]
        
        
        date_obj = datetime.strptime(operator[4], "%a, %d %b %Y %H:%M:%S %Z")
        date = date_obj.strftime("%Y-%m-%d")
        
        
        cur.execute("delete from register_requests where first_name=%s and last_name=%s and user_type=%s and school_id=%s",(operator[1],operator[2],"operator",operator[5]))
        mysql.connection.commit()
        cur.execute("select username,first_name,last_name,school_name,birthday,register_requests.school_id, password from register_requests join schools on register_requests.school_id=schools.school_id")
        result=cur.fetchall()
        session["result"]=result
        
        return render_template("operator_requests.html",result=result)


    if "approve" in request.form:
        result=session["result"]
        a=request.form.get("approve")
        operator=result[int(a)]
        cur.execute("select count(username) from users where school_id=%s and user_type=%s",(operator[5],"operator"))
        result=cur.fetchone()[0]
        
        date_obj = datetime.strptime(operator[4], "%a, %d %b %Y %H:%M:%S %Z")
        date = date_obj.strftime("%Y-%m-%d")
        
        
        if result==1:
            return "there is already an operator for this school"
        

        cur.execute("insert into users (username, first_name,last_name,password,user_type,school_id,birthday) values (%s,%s,%s,%s,%s,%s,%s)",(operator[0],operator[1],operator[2],operator[6],"operator",operator[5],date))
        cur.execute("delete from register_requests where first_name=%s and last_name=%s and user_type=%s and school_id=%s",(operator[1],operator[2],"operator",operator[5]))
        mysql.connection.commit()
        cur.execute("select username,first_name,last_name,school_name,birthday,register_requests.school_id, password from register_requests join schools on register_requests.school_id=schools.school_id")
        result=cur.fetchall()
        session["result"]=result
        
        return render_template("operator_requests.html",result=result)

    
    cur.execute("select username,first_name,last_name,school_name,birthday,register_requests.school_id, password from register_requests join schools on register_requests.school_id=schools.school_id")
    result=cur.fetchall()
    session["result"]=result
    
    return render_template("operator_requests.html",result=result)

@app.route('/register', methods=["GET","POST"])
def register():
    cur=mysql.connection.cursor()
    cur.execute("select school_name,school_id from schools")
    schools=cur.fetchall()
    if "register" in request.form:
        username=request.form.get("username")
        first_name=request.form.get("first_name")
        last_name=request.form.get("last_name")
        password=request.form.get("password")
        user_type=request.form.get("user_type")
        school_id=request.form.get("school")
        date = str(request.form.get("birthday"))
        
        
        
        cur.execute("select count(username) from users where username=%s",(username,))
        res=cur.fetchone()
        if res[0]==1:
            return "username taken"
        
        try:
            cur.execute("insert into register_requests (username,first_name,last_name,password,user_type,school_id,birthday) values (%s,%s,%s,%s,%s,%s,%s)",(username,first_name,last_name,password,user_type,school_id,date))
            mysql.connection.commit()
            return "wait for approval"
        except: 
            return "request pending"

    return render_template("register.html",schools=schools)


@app.route('/operator/<arguement>', methods=["GET", "POST"])
def operator_dashboard(arguement):
    if not session.get(arguement):
        session.pop(arguement, None)
        return redirect('/')
    if request.method == "POST" and "books" in request.form:
        url = url_for('books',arguement=arguement)
        return redirect(url)
    if request.method == "POST" and "users" in request.form:
        url = url_for('users_handler',arguement=arguement)
        return redirect(url)
    if request.method == "POST" and "reviews" in request.form:
        return redirect('/reviews')
    if request.method == "POST" and "borrowings" in request.form:
        return redirect(url_for('/borrowings2',arguement=arguement))
    return render_template("operator_dashboard.html",arguement=arguement)

@app.route('/borrowings2', methods=["GET", "POST"])
def borrowings2():
    arguement = request.args.get('arguement')
    result = []
    if request.method == "POST":
        cur = mysql.connection.cursor()
        cur.execute('select school_id from users where username = %s',(arguement,))
        sid = cur.fetchone()
        cur.execute('select borrowings.id,borrow_date,title,username from borrowings join books on borrowings.book_id=books.isbn join users on users.username = borrowings.user_id where returned = FALSE and school_id = %s',(sid,))
        result = cur.fetchall()
        returned = request.form.get('returned')
        bid = request.form.get('bid')
        new_borrowing = request.form.get('new_borrowing')
        if returned:
            cur.execute('update borrowings set returned = TRUE where id = %s',(bid,))
            mysql.connection.commit()
            return redirect(url_for('borrowings2',arguement=arguement))
        if new_borrowing:
            return redirect(url_for('new_borrowing',arguement=arguement))
    return render_template("borrowings2.html",arguement=arguement,borrowings_data=result)

@app.route('/new_borrowing', methods=["GET", "POST"])
def new_borrowing():
    arguement = request.args.get('arguement')
    if request.method == "POST":
        cur = mysql.connection.cursor()
        cur.execute('select school_id from users where username = %s',(arguement,))
        sid = cur.fetchone()
        cur.execute('select username from users where school_id = %s',(sid,))
        users = cur.fetchall()
        cur.execute('select title,isbn from books join schools_books on book_id = isbn where school_id = %s and no_copies>=1',(sid,))
        books = cur.fetchall()
        user = request.form.get('user')
        book = request.form.get('book')
        save = request.form.get('save')
        if save:
            cur.execute('select DATEDIFF(current_date,borrow_date) from borrowings join users on username = user_id where username = %s',(user,))
            b = cur.fetchall()
            cur.execute('select user_id from reservations where user_id = %s',(user,))
            nr = cur.fetchall()
            if len(b) and b[0][0]>=7 or len(b)+len(nr)>=2:
                return redirect('/exceeded_limits')
            else:
                cur.execute('SELECT username FROM users WHERE username = %s', (user,))
                user_row = cur.fetchone()
                cur.execute('SELECT isbn FROM books WHERE isbn = %s', (book,))
                book_row = cur.fetchone()
                if user_row and book_row:
                    cur.execute('INSERT INTO borrowings (user_id, book_id) VALUES (%s, %s)', (user_row[0], book_row[0]))
                    mysql.connection.commit()
                    return redirect('/success')
    return render_template("new_borrowing.html",arguement=arguement,books=books,users=users)


@app.route('/books', methods=["GET", "POST"])
def books():
    arguement = request.args.get('arguement')
    books_data = []
    if request.method == "POST":
        cur = mysql.connection.cursor()
        writer_s = request.form.get("writer")
        category_s = request.form.get("category")
        title_s = request.form.get("title")
        no_copies_s = request.form.get("no_copies")
        Edit = request.form.get("Edit")
        cur.execute('select title,isbn,no_copies from books join schools_books on schools_books.book_id = books.isbn join schools on schools.school_id = schools_books.school_id join users on schools.school_id = users.school_id where username = %s',(arguement,))
        books2 = cur.fetchall()
        for book in books2:
            cur.execute('select first_name,last_name from book_writer join books on book_writer.book_id = books.isbn join writers on book_writer.writer_id = writers.id where books.isbn = %s',(book[1],))
            a = cur.fetchall()
            names = [i[0]+" "+i[1] for i in a]
            cur.execute('select category_name from categories join category_book on categories.id = category_book.category_id join books on category_book.book_id=books.isbn where books.isbn = %s',(book[1],))
            b = cur.fetchall()
            category = [j[0] for j in b]
            books_data.append({
                'title': book[0],
                'isbn': book[1],
                'no_copies': book[2],
                'writers': names,
                'category': category
            })

        if title_s:
            books_data = []
            cur.execute('select title,isbn,no_copies from books join schools_books on schools_books.book_id = books.isbn join schools on schools.school_id = schools_books.school_id join users on schools.school_id = users.school_id where username = %s and title LIKE %s',(arguement,title_s,))
            books3 = cur.fetchall()
            for book in books3:
                cur.execute('select first_name,last_name from book_writer join books on book_writer.book_id = books.isbn join writers on book_writer.writer_id = writers.id where books.isbn = %s',(book[1],))
                a = cur.fetchall()
                names = [i[0] + " " + i[1] for i in a]
                cur.execute('select category_name from categories join category_book on categories.id = category_book.category_id join books on category_book.book_id=books.isbn where books.isbn = %s', (book[1],))
                b = cur.fetchall()
                category = [j[0] for j in b]
                books_data.append({
                    'title': book[0],
                    'isbn': book[1],
                    'no_copies': book[2],
                    'writers': names,
                    'category': category
                })

        if no_copies_s:
            books_data = []
            cur.execute('select title,isbn,no_copies from books join schools_books on schools_books.book_id = books.isbn join schools on schools.school_id = schools_books.school_id join users on schools.school_id = users.school_id where username = %s and no_copies = %s',(arguement,no_copies_s,))
            books3 = cur.fetchall()
            for book in books3:
                cur.execute('select first_name,last_name from book_writer join books on book_writer.book_id = books.isbn join writers on book_writer.writer_id = writers.id where books.isbn = %s',(book[1],))
                a = cur.fetchall()
                names = [i[0] + " " + i[1] for i in a]
                cur.execute('select category_name from categories join category_book on categories.id = category_book.category_id join books on category_book.book_id=books.isbn where books.isbn = %s', (book[1],))
                b = cur.fetchall()
                category = [j[0] for j in b]
                books_data.append({
                    'title': book[0],
                    'isbn': book[1],
                    'no_copies': book[2],
                    'writers': names,
                    'category': category
                })

        if category_s:
            books_data = []
            cur.execute('select title,isbn,no_copies from books join schools_books on schools_books.book_id = books.isbn join schools on schools.school_id = schools_books.school_id join users on schools.school_id = users.school_id join category_book on category_book.book_id = books.isbn join categories on category_book.category_id = categories.id where username = %s and category_name = %s',(arguement, category_s,))
            books3 = cur.fetchall()
            for book in books3:
                cur.execute('select first_name,last_name from book_writer join books on book_writer.book_id = books.isbn join writers on book_writer.writer_id = writers.id where books.isbn = %s',(book[1],))
                a = cur.fetchall()
                names = [i[0] + " " + i[1] for i in a]
                cur.execute('select category_name from categories join category_book on categories.id = category_book.category_id join books on category_book.book_id=books.isbn where books.isbn = %s',(book[1],))
                b = cur.fetchall()
                category = [j[0] for j in b]
                books_data.append({
                    'title': book[0],
                    'isbn': book[1],
                    'no_copies': book[2],
                    'writers': names,
                    'category': category
                })


        if writer_s:
            books_data = []
            cur.execute('select title,isbn,no_copies from books join schools_books on schools_books.book_id = books.isbn join schools on schools.school_id = schools_books.school_id join users on schools.school_id = users.school_id join book_writer on book_writer.book_id = books.isbn join writers on writers.id = book_writer.writer_id where username = %s and CONCAT(writers.first_name," ",writers.last_name)= %s',(arguement,writer_s,))
            books3 = cur.fetchall()
            for book in books3:
                cur.execute('select first_name,last_name from book_writer join books on book_writer.book_id = books.isbn join writers on book_writer.writer_id = writers.id where books.isbn = %s',(book[1],))
                a = cur.fetchall()
                names = [i[0] + " " + i[1] for i in a]
                cur.execute('select category_name from categories join category_book on categories.id = category_book.category_id join books on category_book.book_id=books.isbn where books.isbn = %s', (book[1],))
                b = cur.fetchall()
                category = [j[0] for j in b]
                books_data.append({
                    'title': book[0],
                    'isbn': book[1],
                    'no_copies': book[2],
                    'writers': names,
                    'category': category
                })

        if Edit:
            isbn = request.form.get("isbn")
            url = url_for('/books/edit_book',isbn=isbn)
            return redirect(url)

    return render_template("books.html",books_data=books_data,arguement=arguement)

@app.route('/books/edit_book', methods=["GET", "POST"])
def edit_book():
    isbn = request.args.get('isbn')
    return render_template("edit_book.html",isbn = isbn)

@app.route('/users_handler', methods=["GET", "POST"])
def users_handler():
    arguement = request.args.get('arguement')
    first_names = None
    last_names = None
    days_of_delay = None
    sid = None
    first_names_len = 0
    if request.method == "POST":
        cur = mysql.connection.cursor()
        cur2 = mysql.connection.cursor()
        current_date = datetime.now().date()
        cur2.execute('select school_id from users where users.username = %s',(arguement,))
        res = cur2.fetchall()
        sid = [r[0] for r in res]
        cur.execute('select first_name,last_name,DATEDIFF(current_date,borrowings.borrow_date) from users join borrowings on users.username = borrowings.user_id where  borrowings.returned = False and DATEDIFF(current_date,borrowings.borrow_date) >= 7 and users.school_id = %s',(sid,))
        result = cur.fetchall()
        first_names = [row[0] for row in result]
        last_names = [row[1] for row in result]
        days_of_delay = [row[2] for row in result]
        first_names_len = len(first_names)
        search_first_name = request.form.get('first_name')
        search_last_name = request.form.get('last_name')
        search_days_of_delay = request.form.get('days_of_delay')
        if search_first_name:
            cur.execute('select first_name,last_name,DATEDIFF(current_date,borrowings.borrow_date) from users join borrowings on users.username = borrowings.user_id where  borrowings.returned = False and DATEDIFF(current_date,borrowings.borrow_date) >= 7 and users.first_name = %s and users.school_id = %s',(search_first_name,sid,))
            result2 = cur.fetchall()
            first_names = [row[0] for row in result2]
            last_names = [row[1] for row in result2]
            days_of_delay = [row[2] for row in result2]
            first_names_len = len(first_names)
        if search_last_name:
            cur.execute('select first_name,last_name,DATEDIFF(current_date,borrowings.borrow_date) from users join borrowings on users.username = borrowings.user_id where  borrowings.returned = False and DATEDIFF(current_date,borrowings.borrow_date) >= 7 and users.last_name = %s and users.school_id = %s', (search_last_name,sid,))
            result3 = cur.fetchall()
            first_names = [row[0] for row in result3]
            last_names = [row[1] for row in result3]
            days_of_delay = [row[2] for row in result3]
            first_names_len = len(first_names)
        if search_days_of_delay:
            cur.execute('select first_name,last_name,DATEDIFF(current_date,borrowings.borrow_date) from users join borrowings on users.username = borrowings.user_id where  borrowings.returned = False and DATEDIFF(current_date,borrowings.borrow_date) = %s and users.school_id = %s',(search_days_of_delay,sid,))
            result4 = cur.fetchall()
            first_names = [row[0] for row in result4]
            last_names = [row[1] for row in result4]
            days_of_delay = [row[2] for row in result4]
            first_names_len = len(first_names)
        requests = request.form.get("requests")
        if requests:
            url = url_for('/users_handler/users_requests',sid=sid)
            return redirect(url)
        edit_users = request.form.get("edit_users")
        if edit_users:
            url = url_for('/users_handler/edit_users',sid=sid)
            return redirect(url)

    return render_template("users2.html",last_names=last_names,first_names=first_names,days_of_delay=days_of_delay,first_names_len=first_names_len,arguement=arguement,sid=sid)

@app.route('/users_handler/edit_users', methods=["GET","POST"])
def edit_users():
    sid = request.args.get('sid')
    cur = mysql.connection.cursor()
    cur.execute('select username,first_name,last_name,user_type,enabled from users where users.user_type != "operator" and users.school_id = %s',(sid,))
    users = cur.fetchall()
    if request.method == "POST":
        d = request.form.get("delete")
        user = request.form.get("user")
        disable = request.form.get("disable")
        enable = request.form.get("enable")
        if d:
            cur2 = mysql.connection.cursor()
            cur2.execute('delete from users where username = %s',(user,))
            mysql.connection.commit()
            return redirect(url_for('edit_users',sid=sid))
        if disable:
            cur3 = mysql.connection.cursor()
            cur3.execute('update users set enabled = FALSE where username = %s',(user,))
            mysql.connection.commit()
            return redirect(url_for('edit_users', sid=sid))
        if enable:
            cur3 = mysql.connection.cursor()
            cur3.execute('update users set enabled = TRUE where username = %s', (user,))
            mysql.connection.commit()
            return redirect(url_for('edit_users', sid=sid))
    return render_template("edit_users.html", sid=sid,users=users)

@app.route('/users_handler/users_requests', methods=["GET","POST"])
def users_requests():
    sid = request.args.get('sid')
    cur = mysql.connection.cursor()
    cur.execute('select username,first_name,last_name,user_type from register_requests where user_type != "operator" and register_requests.school_id = %s',(sid,))
    users = cur.fetchall()
    if request.method == "POST":
        approve = request.form.get("approve")
        user = request.form.get("user")
        reject = request.form.get("reject")
        if approve:
            cur2 = mysql.connection.cursor()
            cur3 = mysql.connection.cursor()
            cur3.execute('select * from register_requests where register_requests.username = %s',(user,))
            info = cur3.fetchone()
            if info:
                cur2.execute('insert into users (username,first_name,last_name,password,user_type,school_id,birthday) values (%s,%s,%s,%s,%s,%s,%s)',(info[0],info[1],info[2],info[3],info[4],info[5],info[6]))
                cur2.execute('delete from register_requests where username = %s and first_name = %s',(info[0],info[1]))
                mysql.connection.commit()
                return redirect(url_for('card', username=info[0]))
        if reject:
            cur2 = mysql.connection.cursor()
            cur2.execute('delete from register_requests where username = %s',(user,))
            mysql.connection.commit()
            return redirect(url_for('users_requests', sid=sid))
    return render_template("user_request.html",sid=sid,users=users)

@app.route('/card/<username>', methods=["GET", "POST"])
def card(username):
    cur = mysql.connection.cursor()
    cur.execute('select username,first_name,last_name,user_type,school_name from users join schools on users.school_id = schools.school_id where username = %s',(username,))
    result = cur.fetchone()
    return render_template("card.html",username=username,first_name=result[1],last_name=result[2],user_type=result[3],school_name=result[4])

@app.route('/reviews', methods=["GET", "POST"])
def reviews():
    cur = mysql.connection.cursor()
    avg = None
    username = None
    category = None
    avg2 = None
    if request.method == "POST":
        username = request.form.get("username")
        category = request.form.get("category")
        requests = request.form.get("requests")
        if username:
            cur.execute('select likert from reviews join users on reviews.user_id = users.username where reviews.published = TRUE and users.username = %s',(username,))
            rows = cur.fetchall()
            likert_values = [row[0] for row in rows]
            if likert_values:
                avg = sum(likert_values)/len(likert_values)
            else:
                avg = 0
        if category:
            cur.execute('select likert from reviews join books on reviews.book_id = books.isbn join category_book on category_book.book_id = books.isbn join categories on categories.id = category_book.category_id where reviews.published = TRUE and category_name = %s',(category,))
            rows = cur.fetchall()
            likert_values = [row[0] for row in rows]
            if likert_values:
                avg2 = sum(likert_values) / len(likert_values)
            else:
                avg2 = 0
        if requests:
            return redirect(url_for('/reviews/reviews_requests'))

    return render_template("reviews.html",avg=avg,username=username,category=category,avg2=avg2)

@app.route('/reviews/reviews_requests', methods=["GET","POST"])
def reviews_requests():
    cur = mysql.connection.cursor()
    cur.execute('select review_text,likert,username,title,isbn from reviews join users on users.username = reviews.user_id join books on books.isbn = reviews.book_id where reviews.published = FALSE')
    reviews = cur.fetchall()
    if request.method == "POST":
        approve = request.form.get("approve")
        user = request.form.get("user")
        book = request.form.get("book")
        reject = request.form.get("reject")
        if approve:
            cur2 = mysql.connection.cursor()
            cur2.execute('update reviews set published = TRUE where user_id = %s and book_id = %s',(user,book,))
            mysql.connection.commit()
            return redirect(url_for('reviews_requests'))
        if reject:
            cur2 = mysql.connection.cursor()
            cur2.execute('delete from reviews where user_id = %s and book_id = %s',(user,book,))
            mysql.connection.commit()
            return redirect(url_for('reviews_requests'))
    return render_template("review_request.html",reviews=reviews)

if __name__ == '__main__':
    app.run()
