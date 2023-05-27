from flask import Flask,request, render_template,redirect ,url_for,session

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





@app.route('/user/<arguement>', methods=["GET","POST"])
def user_page(arguement):
    if not session.get(arguement):
            session.pop(arguement, None)
            return redirect('/')
    if request.method=="POST":
        writer_check=''
        category_check=''
        title_check=''
        writer=request.form.get("writer")
        title=request.form.get("title")
        
        category=request.form.get("category")
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
        cur.execute("select title from users join schools on users.school_id=schools.school_id join schools_books on schools.school_id=schools_books.school_id join books on schools_books.book_id=isbn join category_book on category_book.book_id=isbn join categories on category_book.category_id=categories.id join book_writer on book_writer.book_id=isbn join writers on writers.id=book_writer.writer_id where users.username=%s "+title_check+category_check+writer_check,param)
        result=cur.fetchall()
        available_titles = [row[0] for row in result]
        cur.execute("select title from users join borrowings on user_id=username join books on book_id=isbn where username=%s",(arguement,))
        result = cur.fetchall()
        borrowed_titles = [row[0] for row in result]
        cur.close()
        return render_template("user_dashboard.html",username=arguement,available_books=available_titles,borrowed_books=borrowed_titles) 
    cur = mysql.connection.cursor()
    cur.execute("select title from users join schools on users.school_id=schools.school_id join schools_books on schools.school_id=schools_books.school_id join books on schools_books.book_id=isbn where users.username=%s",(arguement,))
    result = cur.fetchall()
    available_titles = [row[0] for row in result]
    cur.execute("select title from users join borrowings on user_id=username join books on book_id=isbn where username=%s",(arguement,))
    result = cur.fetchall()
    borrowed_titles = [row[0] for row in result]
    cur.close()
    
    return render_template("user_dashboard.html",username=arguement,available_books=available_titles,borrowed_books=borrowed_titles)




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
