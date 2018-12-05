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

#Method to run an sql query. Please use this instead of writing the same 3 lines everytime.
#Input: query, data to be used in query, and amount, which is either "one" or "all" determines fetchone() or fetchall(). Last parameter is optional and will determine if commit() will be called.
#Output: returns data from query
def run_sql(query, data, amount, comm=None):
    cursor = conn.cursor()
    cursor.execute(query, data)
    data = None

    if amount == "one":
        data = cursor.fetchone()
    elif amount == "all":
        data = cursor.fetchall()

    if comm:
        conn.commit()
    cursor.close()
    return data


#Define a route to hello function
#View public content​​
@app.route('/')
def hello():
    query = """SELECT DISTINCT item_id, email_post, post_time, file_path, item_name 
                FROM ContentItem 
                    WHERE is_pub = 1
                ORDER BY post_time DESC"""
    data = run_sql(query, None, 'all')
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

    query = 'SELECT * FROM Person WHERE email = %s and password = %s'
    data = run_sql(query, (email, password), 'one')

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
    #grab information from the forms
    f_name, l_name, email, password = request.form['first_name'], request.form['last_name'], request.form['email'], request.form['password']
    
    query = 'SELECT * FROM Person WHERE email = %s'
    data = run_sql(query, email, 'one')

    error = None
    if (data):
        #If the previous query returns data, then user exists
        error = "This user already exists"
        return render_template('register.html', error = error)
    else:
        password = hashlib.sha256(password.encode('utf-8')).hexdigest()
        query = 'INSERT INTO Person(email, password, fname, lname) VALUES(%s, %s, %s, %s)'
        run_sql(query, (email, password, f_name, l_name), 'all', True)
        return redirect('/')

#View shared content items and info about them
@app.route('/home')
def home():
    email = session['email']
    query = """SELECT DISTINCT item_id, email_post, post_time, file_path, item_name 
                FROM ContentItem 
                WHERE is_pub = 1 OR item_id IN 
                    (SELECT item_id FROM PriCoSha.Share WHERE fg_name IN 
                        (SELECT fg_name FROM Belong WHERE email = %s)
                    )
                ORDER BY post_time DESC"""
    data = run_sql(query, email, 'all')

    #why do we pass in username???? i can't find it used anywhere in home.html
    return render_template('home.html', username=email, posts=data, fname = session['fname'])


#Post a content item        
@app.route('/post', methods=['GET', 'POST'])
def post():
    #grab request data
    email = session['email']
    f_path, i_name = request.form['file_path'], request.form['item_name']
    #check if public checkbox is not empty. Convert boolean to 0 or 1 value.
    visible = int(request.form.get('public') != None)
    print("value of visible is ", visible)

    ts = time.time()
    timestamp = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
    query = """INSERT INTO ContentItem 
                (email_post, post_time, file_path, item_name, is_pub) 
                VALUES(%s, %s, %s, %s, %s)"""
    run_sql(query, (email, timestamp, f_path, i_name, visible), 'one', True)
    return redirect(url_for('home'))

@app.route('/logout')
def logout():
    session.pop('email')
    return redirect('/')

#Feature #4. Create endpoint for managing tags. 
@app.route('/tag')
def tag():
    email = session['email']
    #grab all tags that are currently waiting for approval (status == "false")
    query = """SELECT email_tagger, item_id, tagtime  
                FROM Tag 
                WHERE email_tagged = %s AND status = "false"
                ORDER BY tagtime DESC"""
    data = run_sql(query, email, 'all')
    print("This isteh data", data)
    return render_template('tag.html', tags=data, fname = session['fname'])

#handle the post method for approving / declining tag applications.
@app.route('/edit_tag', methods=['GET', 'POST'])
def edit_tag():
    #grab the request data
    email_tagged = session['email']
    new_status, email_tagger, item_id = request.form['new_status'], request.form['email_tagger'], request.form['item_id']

    #if the person approves the tag, set the status to "true".
    if new_status == "approve":
        query = """UPDATE Tag
                    SET status = "true" 
                    WHERE email_tagged = %s AND email_tagger = %s AND item_id = %s"""
        run_sql(query, (email_tagged, email_tagger, item_id), 'one', True)
    #if the person declines the tag, delete from Tag database.
    elif new_status == "decline":
        query = """DELETE FROM Tag 
                    WHERE email_tagged = %s AND email_tagger = %s AND item_id = %s"""
        run_sql(query, (email_tagged, email_tagger, item_id), 'one', True)
    
    #return to the tag page
    return redirect(url_for('tag'))


app.secret_key = 'some key that you will never guess'
#Run the app on localhost port 5000
#debug = True -> you don't have to restart flask
#for changes to go through, TURN OFF FOR PRODUCTION
if __name__ == "__main__":
    app.run('127.0.0.1', 5000, debug = True)

