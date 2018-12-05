#Import Flask Library
from flask import Flask, render_template, request, session, url_for, redirect
import pymysql.cursors
import time
import datetime
import hashlib

#Initialize the app from Flask
app = Flask(__name__)

#Configure MySQL
conn = pymysql.connect(host='localhost',
                       port = 8889,
                       user='root',
                       password='root',
                       db='PriCoSha',
                       charset='utf8mb4',
                       cursorclass=pymysql.cursors.DictCursor)

#Define a route to hello function
#View public content​​
@app.route('/')
def hello():
    cursor = conn.cursor()
    query = """SELECT DISTINCT item_id, email_post, post_time, file_path, item_name 
                FROM ContentItem 
                    WHERE is_pub = 1
                ORDER BY post_time DESC"""

    cursor.execute(query)
    data = cursor.fetchall()
    cursor.close()
    return render_template('index.html', posts = data)

#Define route for login
@app.route('/login')
def login():
    return render_template('login.html')

#Define route for register
@app.route('/register')
def register():
    return render_template('register.html')

    

#Authenticates the login
@app.route('/loginAuth', methods=['GET', 'POST'])
def loginAuth():
    #grabs information from the forms
    email    = request.form['email']
    password = request.form['password']
    password = hashlib.sha256(password.encode('utf-8')).hexdigest()

    #cursor used to send queries
    cursor = conn.cursor()
    #executes query
    query = 'SELECT * FROM Person WHERE email = %s and password = %s'
    cursor.execute(query, (email, password))
    #stores the results in a variable
    data = cursor.fetchone()
    print("This is the fetchone", data)
    #use fetchall() if you are expecting more than 1 data row
    cursor.close()
    error = None
    if(data):
        #creates a session for the the user
        #session is a built in
        session['email'] = email
        #save the user's name for later
        session['fname'] = data['fname']
        return redirect(url_for('home'))
    else:
        #returns an error message to the html page
        error = 'Invalid login or email'
        return render_template('login.html', error=error)

#Authenticates the register
@app.route('/registerAuth', methods=['GET', 'POST'])
def registerAuth():
    #grabs information from the forms
    f_name = request.form['first_name']
    l_name = request.form['last_name']
    email = request.form['email']
    password = request.form['password']

    #cursor used to send queries
    cursor = conn.cursor()
    #executes query
    query = 'SELECT * FROM Person WHERE email = %s'
    cursor.execute(query, (email))
    #stores the results in a variable
    data = cursor.fetchone()
    #use fetchall() if you are expecting more than 1 data row
    error = None
    if (data):
        #If the previous query returns data, then user exists
        error = "This user already exists"
        return render_template('register.html', error = error)
    else:
        password = hashlib.sha256(password.encode('utf-8')).hexdigest()
        ins = 'INSERT INTO Person(email, password, fname, lname) VALUES(%s, %s, %s, %s)'
        cursor.execute(ins, (email, password, f_name, l_name))
        conn.commit()
        cursor.close()
        return render_template('index.html')

#View shared content items and info about them
@app.route('/home')
def home():
    user = session['email']
    cursor = conn.cursor()
    query = """SELECT DISTINCT item_id, email_post, post_time, file_path, item_name 
                FROM ContentItem 
                WHERE is_pub = 1 OR item_id IN 
                    (SELECT item_id FROM PriCoSha.Share WHERE fg_name IN 
                        (SELECT fg_name FROM Belong WHERE email = %s)
                    )
                ORDER BY post_time DESC"""
    cursor.execute(query, (user))
    data = cursor.fetchall()
    cursor.close()
    return render_template('home.html', username=user, posts=data, fname = session['fname'])


#Post a content item        
@app.route('/post', methods=['GET', 'POST'])
def post():
    email = session['email']
    cursor = conn.cursor()

    f_path = request.form['file_path'] 
    i_name = request.form['item_name']
    visible = request.form['public']
    if visible == 'on':
        visible = 1
    else:
        visible = 0
    ts = time.time()
    timestamp = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
    query = 'INSERT INTO ContentItem (email_post, post_time, file_path, item_name, is_pub) VALUES(%s, %s, %s, %s, %s)'
    cursor.execute(query, (email, timestamp, f_path, i_name, visible))
    conn.commit()
    cursor.close()
    return redirect(url_for('home'))


@app.route('/logout')
def logout():
    session.pop('username')
    return redirect('/')
        
app.secret_key = 'some key that you will never guess'
#Run the app on localhost port 5000
#debug = True -> you don't have to restart flask
#for changes to go through, TURN OFF FOR PRODUCTION
if __name__ == "__main__":
    app.run('127.0.0.1', 5000, debug = True)



#Add/View comments about a post. Extra feature #10
#@app.route('/comment')
#def comment():
