import datetime
import json
import re
import requests
from jsonschema import validate, ValidationError
from stories.database import db, Story, is_date, retrieve_themes, retrieve_dice_set
from flask import request, jsonify, abort
from sqlalchemy.sql.expression import func
from stories.background import async_like, async_dislike, async_remove_like, async_remove_dislike

from flakon import SwaggerBlueprint

stories = SwaggerBlueprint('stories', 'stories', swagger_spec='./stories/stories-specs.yaml')
follows_url= 'http://follows:5000'

"""
This API returns, if the user is logged in, the list of all stories from all users
in the social network. The POST is used to filters those stories by user picked date.
If not logged, the anonymous user is redirected to the login page.
"""

@stories.operation('filter-stories')
def getStories():
    writer_id= int_validator(request.args.get('writer_id'))
    drafts=request.args.get('drafts')
    start=request.args.get('start')
    end=request.args.get('end')
    stories=db.session.query(Story).order_by(Story.date.desc())
    if writer_id is not None:
        stories = stories.filter(Story.author_id == writer_id)
        if drafts is None or drafts != 'True':
            stories = stories.filter(Story.published==1)
    else:
        stories = stories.filter(Story.published==1)

    if (start and end) is not None:
        if start == "" or start is None or not is_date(start):
            start = str(datetime.date.min)
        if end == "" or end is None or not is_date(end):
            end = str(datetime.date.max)
        stories = stories.filter(Story.date.between(start, end))
    return jsonify({'stories': [obj.serialize() for obj in stories]})

"""
This API returns the story by ID (given)
"""

@stories.operation('get_story_by_id')
def getStoryById(user_id, story_id):
    user_id = int_validator(user_id)
    story_id = int_validator(story_id)
    if (user_id or story_id) is None:
        return "Not Found!", 404

    story = Story.query.filter_by(id=story_id).first()
    if story is None or (user_id != story.author_id and story.published==0):
        return "Not Found!", 404
    return jsonify(story.serialize())

"""
This API deletes the story identified by the given ID
"""

@stories.operation('delete_story_by_id')
def deleteStoryById(user_id, story_id):
    user_id = int_validator(user_id)
    story_id = int_validator(story_id)
    if (user_id or story_id) is None:
        return "Not Found!", 404 

    story = Story.query.filter_by(id=story_id).first()
    if story is None:
        return "Not Found!", 404
    elif (user_id != story.author_id) or (story.published==0):
        return "Not Authorized", 401
    db.session.delete(story)
    db.session.commit()
    return "Story correctly deleted", 200


"""
This API return all the themes available in the system, and the maximum number of dices that can be rolled.
"""
@stories.operation('retrieve-set-themes')
def retrieveSetThemes():
    return jsonify({'themes' : retrieve_themes(), 'dice_number' : 6})


"""
This API returns the last story of each writer (writer id and name included)
"""
@stories.operation('writers-last-stories')
def getWritersLastStories():
    stories=db.session.query(Story).filter_by(published=1).group_by(Story.author_id)
    return jsonify({'stories': [obj.serialize() for obj in stories]})


"""
This API return a random story (exluded own stories, given by the user id)
"""
@stories.operation('get-random-story')
def getRandomStory(user_id):
    user_id = int_validator(user_id)
    if user_id  is None:
        return "Not Found!", 404 
    story = Story.query.filter(Story.author_id != user_id).filter_by(published=1).order_by(func.random()).first()
    if story is None:
        return "Not Found!", 404
    else:
        return jsonify(story.serialize())

"""
This API get a list of the stories of the following authors after asked them to /following-list in followers
"""
@stories.operation('following-stories')
def getFollowingStories(user_id):
    user_id = int_validator(user_id)
    if user_id  is None:
        return "Not Found!", 404 
    try:
        r = requests.get(follows_url + "/following-list/" + str(user_id))
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
        abort(500)
    json_data = r.json()['following_ids']
    following_stories= db.session.query(Story).filter(Story.published==1).filter(Story.author_id.in_(json_data)).order_by(Story.date.desc()).all()
    return jsonify({'stories': [obj.serialize() for obj in following_stories]})

"""
The following  API are used by celery 
"""
@stories.operation('like')
def addLike(story_id):
    story_id = int_validator(story_id)
    if story_id is not None:
        story = Story.query.filter_by(id=story_id).filter_by(published=1).first()
        if story is not None:
            async_like(story_id)
            # Use asynch celery
            #story.likes+=1
            #db.session.commit()
            return "Like added", 201
    return "Not Found!", 404

@stories.operation('remove_like')
def removeLike(story_id):
    story_id = int_validator(story_id)
    if story_id is not None:
        story = Story.query.filter_by(id=story_id).filter_by(published=1).first()
        if story is not None:
            async_remove_like(story_id)
            # Use asynch celery
            #story.likes-=1
            #db.session.commit()
            return "Like removed", 201
    return "Not Found!", 404

@stories.operation('dislike')
def addDislike(story_id):
    story_id = int_validator(story_id)
    if story_id is not None:
        story = Story.query.filter_by(id=story_id).filter_by(published=1).first()
        if story is not None:
            async_dislike(story_id)
            # Use asynch celery
            #story.dislikes+=1
            #db.session.commit()
            return "Dislike added", 201
    return "Not Found!", 404

@stories.operation('remove_dislike')
def removeDislike(story_id):
    story_id = int_validator(story_id)
    if story_id is not None:
        story = Story.query.filter_by(id=story_id).filter_by(published=1).first()
        if story is not None:
            async_remove_dislike(story_id)
            # Use asynch celery
            #story.dislikes-=1
            #db.session.commit()
            return "Dislike removed", 201
    return "Not Found!", 404

""" End Celery API """


"""
This API initialize a new draft in the database and return the id
"""
@stories.operation('new-draft')
def newDraft():
    if general_validator('new-draft', request):
        json_data= request.get_json()
        user_id= json_data['user_id']
        author_name= json_data['author_name']
        theme= json_data['theme']
        dice_number= json_data['dice_number']
        if theme not in retrieve_themes():
            return abort(404, description="Theme not found")
        story = Story.query.filter(Story.author_id == user_id).filter(Story.published == 0).filter(Story.theme == theme).first()
        if story is not None:
            return jsonify({'story_id': story.id})

        dice_set = retrieve_dice_set(theme)
        face_set = dice_set.throw()[:dice_number]
        new_story = Story()
        new_story.author_id = user_id
        new_story.theme = theme
        new_story.author_name = author_name
        new_story.rolls_outcome = json.dumps(face_set)
        db.session.add(new_story)
        db.session.flush()
        db.session.commit()
        db.session.refresh(new_story)
        return jsonify({'story_id': new_story.id})
    else:
        return abort(400)


"""
This API update the story with the given id, saving it as draft or publishing it
"""
@stories.operation('write-story')
def writeStory():
    if general_validator('write-story', request):
        json_data= request.get_json()
        story_id= json_data['story_id']
        title= json_data['title']
        text= json_data['text']
        published= json_data['published']
        story = Story.query.filter_by(id=story_id).filter_by(published=0).first()
        if story is None:
            abort(404)
        story.text = text
        story.title = title
        story.published = 1 if published == True else 0
        if story.published == 1 and (story.title == "" or story.title == "None"):
            db.session.rollback()
            abort(400, description="You must complete the title in order to publish the story")
        rolls_outcome = json.loads(story.rolls_outcome)
        faces = [roll[0] for roll in rolls_outcome]
        if story.published == 1 and not is_story_valid(story.text, faces):
            db.session.rollback()
            abort(400, description="You must use all the words of the outcome!")
        
        if story.published == 0 and (story.title == "None" or len(story.title.replace(" ", ""))==0):
            story.title="Draft("+str(story.theme)+")" 

        db.session.commit()

        return "", 200
    else:
        return abort(400)

"""
Function used to import and validate the json schema defined in OpenAPI Yaml file
"""
def general_validator(op_id, request):
    schema= stories.spec['paths']
    for endpoint in schema.keys():
        for method in schema[endpoint].keys():
            if schema[endpoint][method]['operationId']==op_id:
                op_schema= schema[endpoint][method]['parameters'][0]
                if 'schema' in op_schema:
                    definition= op_schema['schema']['$ref'].split("/")[2]
                    schema= stories.spec['definitions'][definition]
                    try:
                        validate(request.get_json(), schema=schema)
                        return True
                    except ValidationError as error:
                        return False
                else:
                     return True

"""
Check if the string is an integer, return the integer, otherwise thorw an exception
"""
def int_validator(string):
    try:
        value= int(string)
    except (ValueError, TypeError):
        return None
    return value


"""
Check if the story text is valid with respect to the dice outcome
"""
def is_story_valid(story_text, dice_roll):
    split_story_text = re.findall(r"[\w']+|[.,!?;]", story_text.lower())
    for word in dice_roll:
        if word.lower() not in split_story_text:
            return False
    return True
