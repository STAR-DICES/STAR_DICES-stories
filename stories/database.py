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
    author_id = db.Column(db.Integer)

    def __init__(self, *args, **kw):
        super(Story, self).__init__(*args, **kw)
        self.date = dt.datetime.now()

    def serialize(self):
        return ({'id': self.id,
                 'title': self.title,
                 'text': self.text,
                 'rolls_outcome': self.rolls_outcome,
                 'theme': self.theme,
                 'date': self.date,
                 'likes': self.likes,
                 'dislikes': self.dislikes,
                 'published': self.published,
                 'author_id': self.author_id})

"""
This function is used to check that the input string is a valid date.
"""
def is_date(string):
    try: 
        dt.datetime.strptime(string, '%Y-%m-%d')
        return True

    except ValueError:
        return False