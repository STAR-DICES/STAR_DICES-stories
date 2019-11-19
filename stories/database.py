# encoding: utf8
import datetime as dt
import enum
import json

from sqlalchemy.orm import relationship
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Story(db.Model):
    __tablename__ = 'story'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title= db.Column(db.Text(50))
    text = db.Column(db.Text(1000), nullable=True)  # around 200 (English) words
    rolls_outcome = db.Column(db.Unicode(1000))
    theme = db.Column(db.Unicode(128))
    date = db.Column(db.DateTime)
    likes = db.Column(db.Integer, default=0)
    dislikes = db.Column(db.Integer, default=0)
    published = db.Column(db.Boolean, default=False)
    # define foreign key 
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    author = relationship('User', foreign_keys='Story.author_id')

    def __init__(self, *args, **kw):
        super(Story, self).__init__(*args, **kw)
        self.date = dt.datetime.now()

"""
This function is used to check that the input string is a valid date.
"""
def is_date(string):
    try: 
        dt.datetime.strptime(string, '%Y-%m-%d')
        return True

    except ValueError:
        return False
"""
This function is used to return the top 5 most liked stories that the user could be interested in.
Returned stories are the ones that the user did not like/dislike yet and that are written with the same themes
of the last 3 published stories of the user.
"""
def get_suggested_stories(user_id):
    lastUsedThemes= [story.theme for story in db.session.query(Story).filter(Story.author_id == user_id).distinct()]
    likedStories= [like.story_id for like in db.session.query(Like).filter(Like.liker_id==user_id)]
    dislikedStories= [dislike.story_id for dislike in db.session.query(Dislike).filter(Dislike.disliker_id==user_id)]
    suggestedStories= (db.session.query(Story).filter(Story.author_id != user_id)
                                              .filter(Story.published==1)
                                              .order_by(Story.likes.desc())
                                              .all())
    suggestedStories = [story for story in suggestedStories if story.id not in likedStories]
    suggestedStories = [story for story in suggestedStories if story.id not in dislikedStories]
    suggestedStories = [story for story in suggestedStories if story.theme in lastUsedThemes][:5]
    return suggestedStories
