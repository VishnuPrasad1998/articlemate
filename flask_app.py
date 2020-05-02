from flask import Flask, render_template, flash, url_for, session, request, redirect, logging
#from data import Articles
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
from functools import wraps

app = Flask(__name__)
app.secret_key = "super secret key"

def is_logged_in(f): #Check if user logged in
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized user', 'danger')
            return redirect(url_for('login'))
    return wrap

#Configure MYSQL
app.config['MYSQL_HOST'] = 'myarticles.mysql.pythonanywhere-services.com'
app.config['MYSQL_USER'] = 'myarticles'
app.config['MYSQL_PASSWORD'] = 'password123'
app.config['MYSQL_DB'] = 'myarticles$myflaskapp'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

#Initialize MYSQL
mysql = MySQL(app)


@app.route('/')

def index():
    return render_template('home.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/articles')
def articles():
    cur = mysql.connection.cursor()

    result = cur.execute("SELECT * FROM articles")

    articles = cur.fetchall()

    if result > 0:
        return render_template('articles.html', articles=articles)
    else:
        msg = 'No articles found'
        return render_template('articles.html',msg=msg)

    cur.close()

@app.route('/article/<string:id>/')
def article(id):
    cur = mysql.connection.cursor()

    result = cur.execute("SELECT * FROM articles WHERE id= %s", [id])

    articles = cur.fetchone()

    return render_template('article.html', articles = articles)

class RegisterForm(Form):
    name = StringField('', [validators.Length(min=1, max=50)])
    username = StringField('', [validators.Length(min=4, max=25)])
    email = StringField('', [validators.Length(min=6, max=50)])
    password = PasswordField('', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message="Passwords do not match")
    ])
    confirm = PasswordField('')

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        name = form.name.data
        email = form.email.data
        username = form.username.data
        password = sha256_crypt.encrypt(str((form.password.data)))
        
        #Create cursor
        cur = mysql.connection.cursor()

        cur.execute("INSERT INTO user(name, email, username, password) VALUES(%s, %s, %s, %s)", (name, email, username, password))

        #Commit to DB
        mysql.connection.commit()

        #Close Connection
        cur.close()

        flash("You are now registered", 'success')

        return redirect(url_for('index'))

    return render_template('register.html', form=form)    

 #User login
@app.route('/login', methods=['GET', 'POST'])
def login():    
    if request.method == 'POST':
        #Get Form fields
        username = request.form['username']
        password_candidate = request.form['password']
        
        #Create cursor
        cur = mysql.connection.cursor()

        #Get user based on username
        result = cur.execute("SELECT * FROM user WHERE username = %s", [username])

        if result>0:
            #Get stored hash
            data = cur.fetchone()
            password = data['password']

            #Compare the passwords
            if sha256_crypt.verify(password_candidate, password):
                #app.logger.info("Passwords matched")
                session['logged_in'] = True
                session['username'] = username

                flash('You are now logged in', 'success')
                return redirect(url_for('dashboard'))
            else:
                error = 'Invalid login'
                return render_template('login.html', error=error)   
            cur.close()
        else:
            error = 'Username not found'
            return render_template('login.html', error=error)
    
    return render_template('login.html')


#Logout
@app.route('/logout')
@is_logged_in
def logout():
    session.clear()
    flash('You are now logged out', 'success')
    return redirect(url_for('login'))

@app.route('/dashboard')
@is_logged_in
def dashboard():
    cur = mysql.connection.cursor()

    result = cur.execute("SELECT * FROM articles")

    articles = cur.fetchall()

    if result > 0:
        return render_template('dashboard.html', articles=articles)
    else:
        msg = 'No articles found'
        return render_template('dashboard.html',msg=msg)

    cur.close()
    
#Article form class
class ArticleForm(Form):
    title = StringField('', [validators.Length(min=1, max=200)])
    body = TextAreaField('', [validators.Length(min=30)])

#Add article
@app.route('/add_article', methods=['GET', 'POST'])
@is_logged_in
def add_article():
    form = ArticleForm(request.form)
    if request.method == 'POST' and form.validate():
        title = form.title.data
        body = form.body.data

        #Create cursor
        cur = mysql.connection.cursor()

        cur.execute("INSERT INTO articles(title, body, author) VALUES(%s, %s, %s)", (title, body, session['username']))

        #Commit to DB
        mysql.connection.commit()

        #Close Connection
        cur.close()

        flash("Added", 'success')

        return redirect(url_for('dashboard'))

    return render_template('add_article.html', form=form)

#Edit article
@app.route('/edit_article/<string:id>/', methods=['GET', 'POST'])
@is_logged_in
def edit_article(id):
    cur = mysql.connection.cursor()

    result = cur.execute("SELECT * FROM articles WHERE id= %s", [id])

    article = cur.fetchone()

    #Get Form
    form = ArticleForm(request.form)

    #Populate article from fields
    form.title.data = article['title']
    form.body.data = article['body']


    if request.method == 'POST' and form.validate():
        title = request.form['title']
        body = request.form['body']

        #Create cursor
        cur = mysql.connection.cursor()

        cur.execute("UPDATE articles SET title=%s, body=%s WHERE id=%s",(title, body, id))

        #Commit to DB
        mysql.connection.commit()

        #Close Connection
        cur.close()

        flash("Editted", 'success')

        return redirect(url_for('dashboard'))

    return render_template('edit_article.html', form=form) 

#Delete article
@app.route('/delete_article/<string:id>/', methods=['POST'])
@is_logged_in
def delete_article(id):
    cur = mysql.connection.cursor()

    cur.execute("DELETE FROM articles WHERE id=%s", [id])
        #Commit to DB
    mysql.connection.commit()
    
    cur.close()

    flash("Deleted", 'success')

    return redirect(url_for('dashboard'))




if __name__ == "__main__":
    app.secret_key='secret123'
    app.run(debug=True)