import datetime
import json
import re
import requests
from jsonschema import validate, ValidationError
from stories.database import db, Story, is_date, retrieve_themes, retrieve_dice_set
from flask import request, jsonify, abort
from sqlalchemy.sql.expression import func

from flakon import SwaggerBlueprint

stories = SwaggerBlueprint('stories', 'stories', swagger_spec='./stories/stories-specs.yaml')
follows_url= 'http://127.0.0.1:5000'

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

@stories.operation('retrieve-set-themes')
def retrieveSetThemes():
    return jsonify({'themes' : retrieve_themes(), 'dice_number' : 6})

@stories.operation('writers-last-stories')
def getWritersLastStories():
    stories=db.session.query(Story).filter_by(published=1).group_by(Story.author_id)
    return jsonify({'stories': [obj.serialize() for obj in stories]})

def int_validator(string):
    try:
        value= int(string)
    except (ValueError, TypeError):
        return None
    return value

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

@stories.operation('following-stories')
def getFollowingStories(user_id):
    user_id = int_validator(user_id)
    try:
        r = requests.get(follows_url + "/following-list/" + str(user_id))
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
        abort(500)
    json_data = r.json()['following_ids']
    following_stories= db.session.query(Story).filter(Story.published==1).filter(Story.author_id.in_(json_data)).order_by(Story.date.desc()).all()
    return jsonify({'stories': [obj.serialize() for obj in following_stories]})

@stories.operation('like')
def addLike(story_id):
    story_id = int_validator(story_id)
    if story_id is not None:
        story = Story.query.filter_by(id=story_id).filter_by(published=1).first()
        if story is not None:
            story.likes+=1
            db.session.commit()
            return "Like added", 201
    return "Not Found!", 404

@stories.operation('remove_like')
def removeLike(story_id):
    story_id = int_validator(story_id)
    if story_id is not None:
        story = Story.query.filter_by(id=story_id).filter_by(published=1).first()
        if story is not None:
            story.likes-=1
            db.session.commit()
            return "Like removed", 200
    return "Not Found!", 404

@stories.operation('dislike')
def addDislike(story_id):
    story_id = int_validator(story_id)
    if story_id is not None:
        story = Story.query.filter_by(id=story_id).filter_by(published=1).first()
        if story is not None:
            story.dislikes+=1
            db.session.commit()
            return "Dislike added", 200
    return "Not Found!", 404

@stories.operation('remove_like')
def removeDislike(story_id):
    story_id = int_validator(story_id)
    if story_id is not None:
        story = Story.query.filter_by(id=story_id).filter_by(published=1).first()
        if story is not None:
            story.dislikes-=1
            db.session.commit()
            return "Dislike removed", 200
    return "Not Found!", 404

@stories.operation('new-draft')
def newDraft():
    if general_validator('new-draft', request):
        json_data= request.get_json()
        user_id= json_data['user_id']
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
        new_story.rolls_outcome = json.dumps(face_set)
        db.session.add(new_story)
        db.session.flush()
        db.session.commit()
        db.session.refresh(new_story)
        return jsonify({'story_id': new_story.id})
    else:
        return abort(400)

#Not tested yet
@stories.operation('write-story')
def writeStory():
    if general_validator('write-story', request):
        json_data= request.get_json()
        story_id= json_data['story_id']
        title= json_data['title']
        text= json_data['text']
        published= json_data['published']
        author_name= json_data['author_name']
        story = Story.query.filter_by(id=story_id).filter_by(published=0).first()
        if story is None:
            abort(404)
        story.text = text
        story.title = title
        story.published = 1 if published == True else 0
        if story.published == 1 and (story.title == "" or story.title == "None"):
            db.session.rollback()
            abort(400, description="You must complete the title in order to publish the story")

        if story.published and not is_story_valid(story.text, story.rolls_outcome):
            db.session.rollback()
            abort(400, description="You must use all the words of the outcome!")
        
        if story.published == 0 and (story.title == "None" or len(story.title.replace(" ", ""))==0):
            story.title="Draft("+str(story.theme)+")" 

        db.session.commit()

        return "", 200
    else:
        return abort(400)


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

def is_story_valid(story_text, dice_roll):
    split_story_text = re.findall(r"[\w']+|[.,!?;]", story_text.lower())
    for word in dice_roll:
        if word.lower() not in split_story_text:
            return False
    return True