#Import Flask Library
from flask import Flask, render_template, request, session, url_for, redirect, flash
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
                OR email_post = %s
                ORDER BY post_time DESC"""

    data = run_sql(query, (email, email), 'all')

    error = None
    if 'error' in session:
        error = session['error']
        session.pop('error')
    #why do we pass in username???? i can't find it used anywhere in home.html
    return render_template('home.html', username=email, posts=data, fname = session['fname'], error = error)


#Post a content item        
@app.route('/post', methods=['GET', 'POST'])
def post():
    #grab request data
    email = session['email']
    file_path, item_name = request.form['file_path'], request.form['item_name']
    #check if public checkbox is not empty. Convert boolean to 0 or 1 value.
    priOrPub = request.form.get('priOrPub')
    if (priOrPub == "public"): 
        visible = True
    else:
        visible = False
        query = """SELECT DISTINCT owner_email, fg_name, description FROM Belong NATURAL JOIN Friendgroup WHERE email = %s"""
        groups = run_sql(query, (email), 'all')
        return render_template('select_group.html', groups = groups, file_path = file_path, item_name = item_name, fname = session['fname'])


    ts = time.time()
    timestamp = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
    query = """INSERT INTO ContentItem 
                (email_post, post_time, file_path, item_name, is_pub) 
                VALUES(%s, %s, %s, %s, %s)"""
    run_sql_commit(query, (email, timestamp, file_path, item_name, visible))

    query = """SELECT item_id 
                FROM ContentItem 
                WHERE email_post = %s AND post_time = %s AND file_path = %s AND item_name = %s"""
    itemId = run_sql(query, (email, timestamp, file_path, item_name), 'one' )

    # print("item ID from posting is ->", itemId)
    # This function could be implemented with some API in future
    # Suppose we pass in the file path 
    # and the function returns a dictionary containing last_modified and num_of_pages
    info = getPdfDetail(file_path)
    
    # for demo, just gonna assign some arbitrary value
    info = {"last_modified" : "2018-12-05 20:12:02", "num_of_pages" : 38}

    query = """INSERT INTO PdfDetail
                (item_id, last_modified, num_of_pages) 
                VALUES(%s, %s, %s)"""
    run_sql_commit(query, (itemId["item_id"], info["last_modified"], info["num_of_pages"]))

    return redirect(url_for('home'))

@app.route('/select_group', methods=['POST'])
def select_group():
    email = session['email']
    file_path, item_name = request.form['file_path'], request.form['item_name']
    selected_groups = request.form.getlist('selected_groups')
    owner_emails = request.form.getlist('owner_email')
    
    print("This is owner_emails", owner_emails)
    if len(selected_groups):
        ts = time.time()
        timestamp = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
        query = """INSERT INTO ContentItem 
                (email_post, post_time, file_path, item_name, is_pub) 
                VALUES(%s, %s, %s, %s, %s)"""
        run_sql_commit(query, (email, timestamp, file_path, item_name, 0))
        query = """SELECT item_id 
                FROM ContentItem 
                WHERE email_post = %s AND post_time = %s AND file_path = %s AND item_name = %s"""
        item_id = run_sql(query, (email, timestamp, file_path, item_name), 'one' )
        print("this is item_id",item_id)
        share_query = """INSERT INTO Share 
                         (fg_name, owner_email, item_id)
                         VALUES(%s, %s, %s)"""
        for i in range(len(selected_groups)):
            run_sql_commit(share_query, (selected_groups[i], owner_emails[i], item_id['item_id']))
        return redirect(url_for('home'))

    session['error'] = "You must select at least one friend group"
    return redirect(url_for('home'))



def getPdfDetail(f_path):
    return 0
    # This function could be implemented by using some API, 
    # will finish that someday.. 

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
@app.route('/edit_tag', methods=['POST'])
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


@app.route('/view_tags', methods = ['GET', 'POST'], defaults = {'item_id' : None, 'error' : None})
@app.route('/view_tags/<item_id>', methods = ['GET', 'POST'],defaults = {'error' : None})
@app.route('/view_tags/<item_id>/<error>', methods = ['GET', 'POST'])
def view_tags(item_id, error = None):
    email = session['email']
    if not item_id:
        item_id = request.form.get('item_id')
    query = """SELECT email_tagged, email_tagger, tagtime
                 FROM Tag
                WHERE status = 'true' 
                  AND item_id = %s"""
    tags = run_sql(query, (item_id), "all")
    print(error)
    return render_template('view_tags.html', tags = tags, item_id = item_id, error = error)


@app.route('/tag_user', methods = ['GET', 'POST'])
def tag_user():
    email = session['email']
    tagged_email, item_id = request.form['tagged_email'], request.form['item_id']
    find_query = """SELECT * FROM Person WHERE email = %s"""
    if len(run_sql(find_query, (tagged_email), "all")) < 1:
        return redirect(url_for('view_tags', item_id = item_id, error = "User with this email doesn't exist"))
    ts = time.time()
    timestamp = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
    #if you are tagging yourself
    if tagged_email == email:
        insert_query = """INSERT INTO Tag(email_tagger, email_tagged, item_id, status, tagtime)
                           VALUES (%s,%s,%s,%s,%s)"""
        run_sql_commit(insert_query, (email, email, item_id, 'true', timestamp))
        return redirect(url_for('view_tags', item_id = item_id))

    #code to check if the item is visible for the tagged user
    check_visible = """SELECT COUNT(*) 
                         FROM Share NATURAL JOIN Belong
                        WHERE email = %s
                          AND item_id = %s"""
    check_public = """SELECT COUNT(*) 
                         FROM ContentItem
                        WHERE is_pub = %s
                        AND item_id = %s"""
    visible = run_sql(check_visible, (tagged_email, item_id), "all")[0]["COUNT(*)"]
    public = run_sql(check_public, (1, item_id), "all")[0]["COUNT(*)"]
    
    if visible > 0 or public > 0:
        
        insert_query = """INSERT INTO Tag(email_tagger, email_tagged, item_id, status, tagtime)
                           VALUES (%s,%s,%s,%s,%s)"""
        run_sql_commit(insert_query, (email, tagged_email, item_id, 'false', timestamp))
        return redirect(url_for('view_tags', item_id = item_id))
    #if not visible:
    return redirect(url_for('view_tags', item_id = item_id, error = "User doesn't have access to this post."))



@app.route('/about', methods = ['GET', 'POST'], defaults={'item_id' : None})
@app.route('/about/<item_id>', methods = ['GET', 'POST'])
def about(item_id):
    email = session['email']
    # print("this is request.form", request.form)
    # print("this is item_id", item_id)
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

    return render_template('about.html', username = email,     post = post, item = item_id,
                                         comments = comments, fname = session['fname'])

#Post a content item        
@app.route('/add_comments', methods=['POST'])
def add_comments():
    #grab request data
    email = session['email']
    comment, item = request.form['comment'], request.form['item_id']
    #check if public checkbox is not empty. Convert boolean to 0 or 1 value.
    ts = time.time()
    timestamp = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
    query = """INSERT INTO Comment
                (email, item_id, comment_time, comment) 
                VALUES(%s, %s, %s, %s)"""

    run_sql_commit(query, (email, int(item), timestamp, comment))
    return redirect(url_for('about', item_id = int(item)))

@app.route('/pdf_detail', methods = ['GET', 'POST'], defaults={'item_id' : None})
@app.route('/pdf_detail/<item_id>', methods = ['GET', 'POST'])
def pdfdetail(item_id):
    email = session['email']    

    # if the item_id is null, we need to get our itemID from the post request sent from the form

    if not item_id: 
        item_id = request.form['item_id']

    # print("this is item_id  -> ", item_id)

    # executing the query to get the information regarding the Pdf Details with the itemID
    query = """SELECT item_id, last_modified, num_of_pages 
                FROM PdfDetail
                WHERE item_id = %s"""
    file_detail = run_sql(query, item_id, "one")

    # render the returned page called pdf_detail
    return render_template('pdf_detail.html', username = email, item = item_id,
                                         detail = file_detail, fname = session['fname'])
    
    
#Show all of the groups that this user belongs to.
@app.route('/friendgroup')
def friendgroup():
    email = session['email']
    #select all friendgroups that this person belongs to. Grab that friendgroup's name, owner, and description. 
    query = """SELECT DISTINCT owner_email, fg_name, description FROM Belong NATURAL JOIN Friendgroup WHERE email = %s"""
    data = run_sql(query, email, 'all')

    return render_template('friendgroup.html', groups=data, fname=session['fname'])

#Show a list of all the groups that this user is an owner of to be modified.
@app.route('/add_friend')
def add_friend(error=None):
    error = request.args.get('error')
    email = session['email']
    #select all friendgroups that this person owns. Grab that friendgroup's name and description. 
    query = """SELECT DISTINCT fg_name FROM Belong NATURAL JOIN Friendgroup WHERE owner_email = %s"""
    data = run_sql(query, email, 'all')
    return render_template('add_friend.html', groups=data, fname=session['fname'], error=error)

#Given a specific group and person, attempt to add this person to the group. Return to friendgroup page or show error.
@app.route('/add_friend_post', methods=['POST'])
def add_friend_post():
    owner_email = session['email']
    fg_name, fname, lname = request.form['fg_name'], request.form['fname'], request.form['lname']
    
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
        friend_email = friend_email[0]['email']
        run_sql_commit(query, (friend_email, owner_email, fg_name))
    #Handle error where person is already in group
    except:
        return redirect(url_for('add_friend', error= "Error: This person already exists in this group!"))

    return redirect(url_for('friendgroup'))

#Show a list of all groups that the user is an owner. Determines which group a person wants to modify
@app.route('/remove_friend')
def remove_friend():
    email = session['email']
    #select all friendgroups that this person belongs to. Grab name, owner, and description. 
    query = """SELECT DISTINCT fg_name 
            FROM Belong NATURAL JOIN Friendgroup 
            WHERE owner_email = %s"""
    data = run_sql(query, email, 'all')
    return render_template('remove_friend.html', groups=data, fname=session['fname'])

#Given a specific group, show a list of all members to be chosen for removal from group.
@app.route('/remove_friend_post', methods=['POST'])
def remove_friend_post():
    owner_email = session['email']
    fg_name = request.form['fg_name']
    #find all the members of this friendgroup besides the owner
    query = """SELECT fname, lname, email FROM 
                Person NATURAL JOIN Belong 
                WHERE owner_email = %s AND fg_name = %s AND email != %s"""
    data = run_sql(query, (owner_email, fg_name, owner_email), 'all')
    return render_template('remove_friend_2.html', members=data, fname=session['fname'], fg_name=fg_name)

#Given a specific group and specific person, attempt to delete this person from a group.
@app.route('/remove_friend_post_2', methods=['POST'])
def remove_friend_post_2():
    owner_email = session['email']
    email, fg_name = request.form['member_email'], request.form['fg_name']

    #remove this member from the friendgroup
    query = """DELETE FROM Belong WHERE email= %s AND owner_email = %s AND fg_name = %s"""
    run_sql_commit(query, (email, owner_email, fg_name))

    #remove all tags made by this person on items shared to this friendgroup
    #by grabbing all item_ids shared to this friendgroup, and then remove all 
    #instances tagged by member on those item_ids. 
    query = """DELETE FROM Tag WHERE email_tagger = %s AND 
            item_id IN 
                (SELECT item_id FROM Share WHERE owner_email = %s AND fg_name = %s)"""
    run_sql_commit(query, (email, owner_email, fg_name))

    #remove all ratings made by this person on items shared to this friendgroup
    #by grabbing all ratings that have the item_ids shared to this friendgroup, 
    #and then remove all those ratings which match the member and item_id
    query = """DELETE FROM Rate WHERE email = %s AND 
            item_id IN
                (SELECT item_id FROM Share WHERE owner_email = %s AND fg_name = %s)"""
    run_sql_commit(query, (email, owner_email, fg_name))

    #remove all comments made by this person on items shared to this friendgroup
    #by grabbing all item_ids that have the item_ids shared to group, and which match
    #the email of removed friend.
    query = """DELETE FROM Comment WHERE email = %s AND 
            item_id IN 
                (SELECT item_id FROM Share WHERE owner_email = %s AND fg_name = %s)"""
    run_sql_commit(query, (email, owner_email, fg_name))
    
    #return to the friendgroup page
    return redirect(url_for('friendgroup'))

#Create a new friendgroup and return to friendgroup page.
@app.route('/create_friendgroup', methods=['POST'])
def create_friendgroup():
    email = session['email']
    name, description = request.form['name'], request.form['description']

    #create the friendgroup
    query = """INSERT INTO Friendgroup VALUES (%s, %s, %s)"""
    run_sql_commit(query, (email, name, description))

    #add person to Belong
    query = """INSERT INTO Belong VALUES (%s, %s, %s)"""
    run_sql_commit(query, (email, email, name))

    return redirect(url_for('friendgroup'))

#Show a page to manage all of the ratings made by the user
@app.route('/rating')
def rating():
    email = session['email']
    query = """SELECT item_name, emoji, rate_time, item_id FROM 
            ContentItem NATURAL JOIN Rate 
            WHERE email = %s"""
    data = run_sql(query, email, 'all')
    return render_template('rating.html', data=data)

#Given a selected item, save the selected item and show all the ratings made on an item
@app.route('/rating_select', methods=['POST'])
def rating_select():
    session['item_id'] = request.form['item_id']
    return redirect(url_for('rating_info'))

#Show all the ratings made on an item 
@app.route('/rating_info')
def rating_info():
    item_id = session['item_id']

    error = None
    if 'error' in session:
        error = session['error']
        session.pop('error')

    #grab the information about the rating made by members
    query = """SELECT rate_time, emoji, fname, lname FROM 
            Person NATURAL JOIN Rate
            WHERE item_id = %s"""
    data = run_sql(query, item_id, 'all')

    #grab the item name 
    query = """SELECT item_name FROM ContentItem WHERE item_id = %s"""
    item_name = run_sql(query, item_id, 'one')['item_name']
    return render_template('rating_info.html', data=data, fname=session['fname'], item_name=item_name, item_id=item_id, error=error)

#Delete a rating and return the to rating page.
@app.route("/rating_delete", methods=['POST'])
def rating_delete():
    email, item_id = session['email'], request.form['item_id']
    query = """DELETE FROM Rate WHERE email = %s AND item_id = %s"""
    run_sql_commit(query, (email, item_id))
    return redirect(url_for('rating'))

#Given a specific item and rating, add a rating and return to home page
@app.route("/rating_add_post", methods=['POST'])
def rating_add_post():
    email, emoji, item_id = session['email'], request.form['emoji'], session['item_id']
    
    query = """INSERT INTO Rate VALUES (%s, %s, %s, %s)"""
    ts = time.time()
    timestamp = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')

    #Handle possible error where the person already rated this item. If so, notify the user.
    try:
        run_sql_commit(query, (email, item_id, timestamp, emoji))
        return redirect(url_for('rating_info'))
    except:
        session['error'] = 'Error: You have already rated this item'
        return redirect(url_for('rating_info'))


app.secret_key = 'some key that you will never guess'
#Run the app on localhost port 5000
#debug = True -> you don't have to restart flask
#for changes to go through, TURN OFF FOR PRODUCTION
if __name__ == "__main__":
    app.run('127.0.0.1', 5000, debug = True)

