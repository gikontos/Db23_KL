from flask import Flask,request, render_template,redirect ,url_for,session,send_from_directory
import MySQLdb
from flask_mysqldb import MySQL
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
        cur.execute("select distinct title,isbn from users join borrowings on username=user_id join books on book_id=isbn join category_book on category_book.book_id=isbn join categories on category_book.category_id=categories.id join book_writer on book_writer.book_id=isbn join writers on writers.id=book_writer.writer_id where users.username=%s "+title_check+category_check+writer_check,param)
        result=cur.fetchall()
        borrowed_titles = [row[0] for row in result]
        borrowed_isbns = [row[1] for row in result]
        session["borrowed_titles"]=borrowed_titles
        session["borrowed_isbns"]=borrowed_isbns
        available_titles = session["available_titles"]
        available_isbns=session["available_isbns"]
             
        cur.close()
        return render_template("user_dashboard.html",username=arguement,available_books=available_titles,borrowed_books=borrowed_titles,writer2=writer,category2=category,title2=title,title1=title1,category1=category1,writer1=writer1,available_isbns=available_isbns) 
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
        
        cur.close()
        return render_template("user_dashboard.html",username=arguement,available_books=available_titles,borrowed_books=borrowed_titles,writer1=writer,category1=category,title1=title,title2=title2,category2=category2,writer2=writer2,available_isbns=available_isbns) 
      
     
    cur = mysql.connection.cursor()
    cur.execute("select distinct title,isbn from users join schools on users.school_id=schools.school_id join schools_books on schools.school_id=schools_books.school_id join books on schools_books.book_id=isbn where users.username=%s",(arguement,))
    result = cur.fetchall()
    available_titles = [row[0] for row in result]
    available_isbns = [row[1] for row in result]
    cur.execute("select distinct title,isbn from users join borrowings on user_id=username join books on book_id=isbn where username=%s",(arguement,))
    result = cur.fetchall()
    borrowed_titles = [row[0] for row in result]
    borrowed_isbns = [row[1] for row in result]
    session["borrowed_titles"]=borrowed_titles
    session["available_titles"]=available_titles
    session["borrowed_isbns"]=borrowed_isbns
    session["available_isbns"]=available_isbns
    session["writer1"]=""
    session["title1"]=""
    session["category1"]=""
    session["writer2"]=""
    session["title2"]=""
    session["category2"]=""
    cur.close()
    
    return render_template("user_dashboard.html",username=arguement,available_books=available_titles,borrowed_books=borrowed_titles,available_isbns=available_isbns)




@app.route('/admin', methods=["GET","POST"])
def admin_dashboard():
        if not session.get('administrator'):
            session.pop('administrator', None)
            return redirect('/')
        return render_template("administrator_dashboard.html")

@app.route('/operator/<arguement>', methods=["GET","POST"])
def operator_dashboard(arguement):
    if not session.get(arguement):
            session.pop(arguement, None)
            return redirect('/')
    return render_template("operator_dashboard.html")

if __name__ == '__main__':
    app.run()
