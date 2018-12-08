# **Database-Project**
# **Creators: Max Kim, Sofiia Barysheva, Yu Zhang**

---

---


## ATTENTION ALL TA/GRADER READ THIS!!!!!

## there are two branches: "master" and "ta-use-this-for-test-no-extra-feature". master contains extra features, the other does not. in the root of each branch, there is a file called "projtabledefs.sql". the master branch will include extra table definitions, but the other will not.

---

---

## a. Describe the project
This project is a website that allows users to share pdf files with their friends. Each user
can sign up an account and invite other users to their groups to share pdf files. Users can
also control who has access to their content and leave ratings/comments on each item for other users to see. 


---

## b. List your optional features, along with all of the items about each of them that were mentioned in the assignment

Note: Pictures also include line numbers to help graders find the code.

1. Add comments - Sofiia Barysheva

Users can add comments about content that is visible to them. We store this information in a new table called "Comment", which stores information on the commenter's email, the actual comment, the time that the comment was made, and what item_id the comment was made on. Naturally, the comments are filtered so that a user can only see the comments on items that they have access to because the only way to make or read a comment is from the home page, which lists all of the items that the user has access to. This feature is great for PriCoSha because it promotes more interaction between users.


![Comment Page](/photos/comment.png)

The first query will grab information about the item selected from the home screen. The second query will grab comment information about that item. 

![Comment Post](/photos/comment_2.png)

![Comment Table Definition](/photos/comment_3.png)

![Comment Example](/photos/comment_example.png)

![Comment Example 2](/photos/comment_example_2.png)

After the comment is create, it is added to the "Comment" table (see table definition above) with the correct email and item_id. 

![Comment Example 3](/photos/comment_example_3.png)

Please note that deleting comments is not supported. You can only delete comments on a private group by removing the commenter from the group, which will remove all of their comments on a group's private items.

---

2. Defriend - Max Kim

Users can remove other users from their friendgroups provided that they are the owners of that group. When a user is unfriended, the following steps occur. First, the friend is removed from the Belong table. Then, all tags and ratings made by the friend on items shared to the group are removed. This is accomplished by selecting all of the item_ids of items shared in the group, and removing all instances from the Tag/Rating table where the item_id and email of friend match. No additional schemas nor attributes required. This feature is great for PriCoSha because it gives more control to the users.


![Remove Friend Page](/photos/remove_friend.png)

Show a page that has a list of all groups that the user owns. User may select one group and click next. 

![Remove Friend Post](/photos/remove_friend_post.png)

Show a page showing a list of all members of that group. User may select one person to remove. 

![Remove Friend Post 2](/photos/remove_friend_post_2.png)

Now that we have the specific friendgroup and person, we will delete that person from the belong table, the tag table, and rate table on anything associated with that group. See comments in code. 

![Remove Friend Example](/photos/remove_friend_example.png)

![Remove Friend Example 2](/photos/remove_friend_example_2.png)

After removing the friend, the "select a friend to be deleted" will now show nobody because the only friend was removed. The same is reflected in the table "Belong". Any tags/ratings made by the friend on items shared in group in the corresponding table will also be deleted.

![After Remove Friend](/photos/after_remove_friend.png)

---

3. Control Ratings - Max Kim

Users have the ability to view, delete, and add ratings. Users can view the ratings made by other users on an item that they have access to. Users can view a list of all of their ratings made and delete their ratings. Finally, users can add ratings to items that they have access to. No additional schemas nor attributes required. This feature is great for PriCoSha because it allows more control to the users.

![Rating Page](/photos/rating.png)
Show a page allowing users to manage all of their ratings

![Rating Post Select](/photos/rating_2.png)
Post method that will select an item to show later

![Rating Selected Page](/photos/rating_3.png)
Show a page with all of the ratings on a specific item

![Rating Post Delete](/photos/rating_4.png)
Post method that will delete a specific rating

![Rating Post Add](/photos/rating_5.png)
Post method that will add a rating on a specific item

![Rating Example](/photos/rating_example.png)

![Rating Example 2](/photos/rating_example_2.png)

![Rating Example 3](/photos/rating_example_3.png)

After removing a rating, the rating will no longer by included in the "Rate" table. After adding a rating, the rating will be added to the "Rate" table.

![Rating Example 4](/photos/rating_example_4.png)


---

4. Extra data about pdf files - Yu Zhang

Users have the ability to view extra details about the content items that they can view. Users can view information about the size/page length of pdf files. Users have ways to utilize this data on other websites. This feature is great for PriCoSha because it gives more information to users.

b. It allows the user to get extra information about the pdf file, last modified time, number of pages. In future, extra information could be provided are color/BW, resolution of pages, the size of the pages, etc. 

c. Because it offers important details of the pdf file at a glance. The user wouldn't need to downloading/opening the file to access such information. 

d. We have one extra table named PdfDetail. It has three columns, file_id, last_modified_time and num_of_pages. The primary key is the file_id. 

e. Regarding queries, we need to insert the PdfDetails into the table while user post the content, and we need queries while the user is accessing the PdfDetail. 
    
    Insertion: 
        
        First we need to get the item_id so that we can insert a new row into PdfDetail. 
            
            query = """SELECT item_id 
                FROM ContentItem 
                WHERE email_post = %s AND post_time = %s AND file_path = %s AND item_name = %s"""
            itemId = run_sql(query, (email, timestamp, file_path, item_name), 'one' )
        
        Second we need to do the actual insertion
               
               query = """INSERT INTO PdfDetail
                    (item_id, last_modified, num_of_pages) 
                    VALUES(%s, %s, %s)"""
                run_sql_commit(query, (itemId["item_id"], info["last_modified"], info["num_of_pages"]))

    Query: 
        We need to query the DB with the itemID passed as a parameter. 
            query = """SELECT item_id, last_modified, num_of_pages 
                FROM PdfDetail
                WHERE item_id = %s"""
            file_detail = run_sql(query, item_id, "one")


f. 

Source code is in ProjectPart3.py around line 360. 

Front end html page is in the file named pdf_detail.html

So, when user hit the post button, the details regarding the pdf page will be extracted, (around line 160)
and written into the SQL table. 

Around line 360, under the route (/pdf_detail), the backend will query the DB with the Item ID and render the page to display pdf-detail to our users. 

g. 

The DB Table looks like this 

![pdf detail db](/photos/pdf_detail_db.png)

The page rendered after the user click to the pdf detail looks like this

![pdf detail](/photos/pdf_detail.png)

---

## c. Specify the contributions of each team member

### Max Kim: 
    - Front-end design of website
    - Managing Tags,
    - Everything with Ratings
    - Creating Friendgroups
    - Adding friends
    - View shared content item
    - Final writeup

### Sofiia Barysheva: 
    - Posting a content item
    - Tagging items
    - Comments
    - View shared content item
    - Login page
    - View public content

### Yu Zhang:
    - View shared contnet item
    - View public content
    - Extra data about content
    - Final writeup


