#Database-Project
Creators: Max Kim, Sofiia Barysheva, Yu Zhang

##a. Describe the project
This project is a website that allows users to share pdf files with their friends. Each user
can sign up an account and invite other users to their groups to share pdf files. Users can
also control who has access to their content and leave ratings/comments on each item for other users to see. 

##b. List your optional features, along with all of the items about each of them that were mentioned in the assignment

1) Add comments - Sofiia Barysheva
Users can add comments about content that is visible to them. We store this information in a new table called "Comment", which stores information on the commenter's email, the actual comment, the time that the comment was made, and what item_id the comment was made on. Naturally, the comments are filtered so that a user can only see the comments on items that they have access to because the only way to make or read a comment is from the home page, which lists all of the items that the user has access to.


2) Defriend - Max Kim
Users can remove other users from their friendgroups provided that they are the owners of that group. When a user is unfriended, the following steps occur. First, the friend is removed from the Belong table. Then, all tags and ratings made by the friend on items shared to the group are removed. This is accomplished by selecting all of the item_ids of items shared in the group, and removing all instances from the Tag/Rating table where the item_id and email of friend match. No additional schemas nor attributes required.


3) Control Ratings - Max Kim
Users have the ability to view, delete, and add ratings. Users can view the ratings made by other users on an item that they have access to. Users can view a list of all of their ratings made and delete their ratings. Finally, users can add ratings to items that they have access to. No additional schemas nor attributes required.



4) Extra data about pdf files - Yu Zhang
Users have the ability to view extra details about the content items that they can view. Users can view information about the size/page length of pdf files. Users have ways to utilize this data on other websites.


##c. Specify the contributions of each team member

Max Kim: 
    Front-end design of website
    Managing Tags,
    Everything with Ratings
    Creating Friendgroups
    Adding friends
    View shared content item
    Final writeup

Sofiia Barysheva: 
    Posting a content item
    Tagging items
    Comments
    View shared content item
    Login page
    View public content

Yu Zhang:
    View shared contnet item
    View public content
    Extra data about content
    Final writeup


