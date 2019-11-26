# encoding: utf8
import datetime as dt
import enum
import json

from sqlalchemy.orm import relationship
from flask_sqlalchemy import SQLAlchemy
from stories.classes import Die, DiceSet

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
    author_name=  db.Column(db.Unicode(50))
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
                 'date': self.date.strftime("%d/%m/%Y %H:%M"),
                 'likes': self.likes,
                 'dislikes': self.dislikes,
                 'published': self.published,
                 'author_id': self.author_id,
                 'author_name': self.author_name})

"""
This function is used to check that the input string is a valid date.
"""
def is_date(string):
    try: 
        dt.datetime.strptime(string, '%Y-%m-%d')
        return True

    except ValueError:
        return False

#### DICE model

class Dice(db.Model):
    __tablename__ = 'dice_set'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    serialized_dice_set = db.Column(db.Unicode(1000), nullable=False)
    theme = db.Column(db.Unicode(128))

"""
This function deserializes a dice set and creates a DiceSet object.
"""
def _deserialize_dice_set(json_dice_set, theme):
    dice_set = json.loads(json_dice_set)
    test = DiceSet.DiceSet([Die.Die(dice, theme) for dice in dice_set], theme)
    return test

"""
This function returns a dice set from the database and deserializes it.
"""
def retrieve_dice_set(theme):
    dice = db.session.query(Dice).filter(Dice.theme==theme).first()
    if dice is None:
        return None

    json_dice_set = dice.serialized_dice_set
    dice_set = _deserialize_dice_set(json_dice_set, dice.theme)
    return dice_set

"""
This function returns a list of available dice set themes.
"""
def retrieve_themes():
    themes = []
    for row in db.session.query(Dice.theme.label('theme')).all():
        themes.append(row.theme)

    return themes

"""
This function serializes a new dice set and stores it into the database.
"""
def store_dice_set(dice_set):
    db_entry = Dice()
    db_entry.theme = dice_set.theme
    db_entry.serialized_dice_set = json.dumps(dice_set.serialize())
    db.session.add(db_entry)
    db.session.commit()