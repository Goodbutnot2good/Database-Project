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

#Method to run an sql query without commit.
#Input: query, data to be used in query, and amount, which is either "one" or "all" determines fetchone() or fetchall(). 
#Output: returns data from query
def run_sql(query, data, amount):
    cursor = conn.cursor()
    cursor.execute(query, data)
    data = None
    if amount == "one":
        data = cursor.fetchone()
    elif amount == "all":
        data = cursor.fetchall()
    cursor.close()
    return data
#Method to run an sql query with commit. 
#Input: query, data to be used in query.
#output: none.
def run_sql_commit(query, data):
    cursor = conn.cursor()
    cursor.execute(query, data)
    conn.commit()
    cursor.close()

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
        run_sql_commit(query, (email, password, f_name, l_name))
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
    priOrPub = request.form.get('priOrPub')
    print(priOrPub)
    if (priOrPub == "public"): 
        visible = True
    else:
        visible = False

    ts = time.time()
    timestamp = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
    query = """INSERT INTO ContentItem 
                (email_post, post_time, file_path, item_name, is_pub) 
                VALUES(%s, %s, %s, %s, %s)"""
    run_sql_commit(query, (email, timestamp, f_path, i_name, visible))
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
        run_sql_commit(query, (email_tagged, email_tagger, item_id))
    #if the person declines the tag, delete from Tag database.
    elif new_status == "decline":
        query = """DELETE FROM Tag 
                    WHERE email_tagged = %s AND email_tagger = %s AND item_id = %s"""
        run_sql_commit(query, (email_tagged, email_tagger, item_id))
    
    #return to the tag page
    return redirect(url_for('tag'))
@app.route('/about', methods = ['GET', 'POST'], defaults={'item_id' : None})
@app.route('/about/<item_id>', methods = ['GET', 'POST'])
def about(item_id):
    email = session['email']
    print("this is request.form", request.form)
    #print("this is item_id", item_id)
    if not item_id:
        item_id = request.form.get('item_id')
    print("this is item_id", item_id)
    query_p = """SELECT DISTINCT item_id, email_post, post_time, file_path, item_name 
                FROM ContentItem
                WHERE item_id = %s"""
    post = run_sql(query_p, (item_id), "all")


    query_c = """SELECT fname, lname, comment_time, comment
                   FROM Comment NATURAL JOIN Person
                  WHERE item_id = %s
               ORDER BY comment_time DESC"""

    comments = run_sql(query_c, (item_id), "all")

    return render_template('about.html', username = email, post = post, item = item_id,
                                         comments = comments, fname = session['fname'])

#Post a content item        
@app.route('/add_comments', methods=['GET', 'POST'])
def add_comments():
    #grab request data
    email = session['email']
    comment, item = request.form['comment'], request.form['item_id']
    #check if public checkbox is not empty. Convert boolean to 0 or 1 value.
    ts = time.time()
    print("this is item_id in /add_comments ", item)
    timestamp = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
    query = """INSERT INTO Comment
                (email, item_id, comment_time, comment) 
                VALUES(%s, %s, %s, %s)"""
    run_sql(query, (email, int(item), timestamp, comment), 'one', True)
    return redirect(url_for('about', item_id = int(item)))

@app.route('/friendgroup')
def friendgroup():
    email = session['email']
    #select all friendgroups that this person belongs to. Grab that friendgroup's name, owner, and description. 
    query = """SELECT owner_email, fg_name, description FROM Belong NATURAL JOIN Friendgroup WHERE email = %s"""
    data = run_sql(query, email, 'all')
    return render_template('friendgroup.html', groups=data, fname=session['fname'])

@app.route('/add_friend')
def add_friend(error=None):
    error = request.args.get('error')
    email = session['email']
    #select all friendgroups that this person owns. Grab that friendgroup's name and description. 
    query = """SELECT fg_name FROM Belong NATURAL JOIN Friendgroup WHERE owner_email = %s"""
    data = run_sql(query, email, 'all')
    return render_template('add_friend.html', groups=data, fname=session['fname'], error=error)

@app.route('/add_friend_post', methods=['GET', 'POST'])
def add_friend_post():
    owner_email = session['email']
    group_name, fname, lname = request.form['fg_name'], request.form['fname'], request.form['lname']

    query = """SELECT email FROM Person WHERE fname = %s AND lname = %s"""
    friend_email = run_sql(query, (fname, lname), 'all')
    #Handle error when person is not found
    if len(friend_email) < 1:
        return redirect(url_for('add_friend', error="Error: Person not found with first and last name!"))

    #Handle error where multiple people with the same first and last name
    if len(friend_email) > 1:
        return redirect(url_for('add_friend', error = "Error: Multiple people with the same first and last name!"))
    
    try:
        query = """INSERT INTO Belong VALUES (%s, %s, %s)"""
        run_sql_commit(query, (friend_email, owner_email, group_name))
    #Handle error where person is already in group
    except:
        return redirect(url_for('add_friend', error= "Error: This person already exists in this group!"))

    return redirect(url_for('friendgroup'))

@app.route('/remove_friend')
def remove_friend():
    email = session['email']
    #select all friendgroups that this person belongs to. Grab that friendgroup's name, owner, and description. 
    query = """SELECT fg_name FROM Belong NATURAL JOIN Friendgroup WHERE owner_email = %s"""
    data = run_sql(query, email, 'all')
    return render_template('remove_friend.html', groups=data, fname=session['fname'])

@app.route('/remove_friend_post', methods=['POST'])
def remove_friend_post():
    owner_email = session['email']
    fg_name = request.form['fg_name']
    #find all the members of this friendgroup besides the owner
    query = """SELECT fname, lname, email FROM 
                Person NATURAL JOIN Belong 
                WHERE owner_email = %s AND fg_name = %s AND email != %s"""
    data = run_sql(query2, (owner_email, fg_name, owner_email), 'all')
    return render_template('remove_friend_2.html', members=data, fname=session['fname'], fg_name=fg_name)

#@app.route('/remove_friend_post_2', methods=['POST'])
#def remove_friend_post2():
#    owner_email = session['email']
#    email, fg_name = request.form['member_email'], request.form['fg_name']

    #remove this member from the friendgroup
#    query = """DELETE FROM Friendgroup WHERE """

    #remove all tags made by this person on items shared to this friendgroup
    #by grabbing all item_ids shared to this friendgroup, and then remove all instances tagged by member on those item_ids. 


    #remove all ratings made by this person on items shared to this friendgroup
    #by grabbing all ratings that have the item_ids shared to this friendgroup, and then remove all those ratings which match the member and item_id


@app.route('/create_friendgroup', methods=['GET', 'POST'])
def create_friendgroup():
    #grab the user's name, group name, and group description
    email = session['email']
    name, description = request.form['name'], request.form['description']
    #create the friendgroup
    query = """INSERT INTO Friendgroup VALUES (%s, %s, %s)"""
    run_sql_commit(query, (email, name, description))
    #add person to Belong
    query = """INSERT INTO Belong VALUES (%s, %s, %s)"""
    run_sql_commit(query, (email, email, name))
    return redirect(url_for('friendgroup'))

app.secret_key = 'some key that you will never guess'
#Run the app on localhost port 5000
#debug = True -> you don't have to restart flask
#for changes to go through, TURN OFF FOR PRODUCTION
if __name__ == "__main__":
    app.run('127.0.0.1', 5000, debug = True)

