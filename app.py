from flask import Flask,request, render_template,redirect ,url_for,session,send_from_directory
import MySQLdb
from flask_mysqldb import MySQL
from datetime import datetime, timedelta
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
        cur.execute("SELECT password,user_type,school_id FROM users WHERE username = %s", (username,))

        # Fetch the result
        password_correct = cur.fetchone()
        
        try:
            if password_correct[0] == password:

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
    return render_template("book_page.html",isbn=arguement,title=result[0],keywords=result[1],summary=result[2],no_pages=result[3],publisher=result[4],image=result[5], writers=writers,categories=categories)

@app.route('/user/<arguement>', methods=["GET","POST"])
def user_page(arguement):
    if not session.get(arguement):
            session.pop(arguement, None)
            return redirect('/')
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
                borrowed_text.append("ongoing")
                endson=date[i].date()+timedelta(days=7)
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
            writer_check="and CONCAT(writers.first_name,\" \",writers.last_name) LIKE %s"  
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
              borrowed_text.append("ongoing")
              endson=date[i].date()+timedelta(days=7)
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
    usernames=[i[0] for i in result]
    fnames=[i[1] for i in result]
    lnames=[i[2] for i in result]
    sids=[i[3] for i in result]
    birthdays=[i[4] for i in result]
    snames=[i[5] for i in result]
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
        return redirect('/books')
    if request.method == "POST" and "users" in request.form:
        url = url_for('users_handler',arguement=arguement)
        return redirect(url)
    if request.method == "POST" and "reviews" in request.form:
        return redirect('/reviews')
    return render_template("operator_dashboard.html",arguement=arguement)

@app.route('/books', methods=["GET", "POST"])
def books():
    return render_template("books.html")

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
        res = cur2.fetchall();
        sid = [r[0] for r in res]
        cur.execute('select first_name,last_name,borrow_date from users join borrowings on users.username = borrowings.user_id where users.user_type = "student" and borrowings.returned = False and DATEDIFF(current_date,borrowings.borrow_date) >= 7 and users.school_id = %s',(sid,))
        result = cur.fetchall();
        first_names = [row[0] for row in result]
        last_names = [row[1] for row in result]
        days_of_delay = [(current_date-row[2].date()).days for row in result]
        first_names_len = len(first_names)
        search_first_name = request.form.get('first_name')
        search_last_name = request.form.get('last_name')
        search_days_of_delay = request.form.get('days_of_delay')
        if search_first_name:
            cur.execute('select first_name,last_name,borrow_date from users join borrowings on users.username = borrowings.user_id where users.user_type = "student" and borrowings.returned = False and DATEDIFF(current_date,borrowings.borrow_date) >= 7 and users.first_name = %s and users.school_id = %s',(search_first_name,sid,))
            result2 = cur.fetchall();
            first_names = [row[0] for row in result2]
            last_names = [row[1] for row in result2]
            days_of_delay = [(current_date - row[2].date()).days for row in result2]
            first_names_len = len(first_names)
        if search_last_name:
            cur.execute('select first_name,last_name,borrow_date from users join borrowings on users.username = borrowings.user_id where users.user_type = "student" and borrowings.returned = False and DATEDIFF(current_date,borrowings.borrow_date) >= 7 and users.last_name = %s and users.school_id = %s', (search_last_name,sid,))
            result3 = cur.fetchall();
            first_names = [row[0] for row in result3]
            last_names = [row[1] for row in result3]
            days_of_delay = [(current_date - row[2].date()).days for row in result3]
            first_names_len = len(first_names)
        if search_days_of_delay:
            cur.execute('select first_name,last_name,borrow_date from users join borrowings on users.username = borrowings.user_id where users.user_type = "student" and borrowings.returned = False and DATEDIFF(current_date,borrowings.borrow_date) = %s and users.school_id = %s',(search_days_of_delay,sid,))
            result4 = cur.fetchall();
            first_names = [row[0] for row in result4]
            last_names = [row[1] for row in result4]
            days_of_delay = [(current_date - row[2].date()).days for row in result4]
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
        if approve:
            cur2 = mysql.connection.cursor()
            cur3 = mysql.connection.cursor()
            cur3.execute('select * from register_requests where register_requests.username = %s',(user,))
            info = cur3.fetchone()
            if info:
                cur2.execute('insert into users (username,first_name,last_name,password,user_type,school_id,birthday) values (%s,%s,%s,%s,%s,%s,%s)',(info[0],info[1],info[2],info[3],info[4],info[5],info[6]))
                cur2.execute('delete from register_requests where username = %s and first_name = %s',(info[0],info[1]))
                mysql.connection.commit()
            return redirect(url_for('users_requests', sid=sid))
    return render_template("user_request.html",sid=sid,users=users)


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
        if username:
            cur.execute('select likert from reviews join users on reviews.user_id = users.username where users.username = %s',(username,))
            rows = cur.fetchall()
            likert_values = [row[0] for row in rows]
            if likert_values:
                avg = sum(likert_values)/len(likert_values)
            else:
                avg = 0
        if category:
            cur.execute('select likert from reviews join books on reviews.book_id = books.isbn join category_book on category_book.book_id = books.isbn join categories on categories.id = category_book.category_id where category_name = %s',(category,))
            rows = cur.fetchall()
            likert_values = [row[0] for row in rows]
            if likert_values:
                avg2 = sum(likert_values) / len(likert_values)
            else:
                avg2 = 0
    return render_template("reviews.html",avg=avg,username=username,category=category,avg2=avg2)

if __name__ == '__main__':
    app.run()

