import datetime
import json
import re
from jsonschema import validate, ValidationError
from stories.database import db, Story, is_date, retrieve_themes
from flask import request, jsonify, abort
from sqlalchemy.sql.expression import func

from flakon import SwaggerBlueprint

stories = SwaggerBlueprint('stories', 'stories', swagger_spec='./stories-specs.yaml')

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
This route returns, if the user is logged in, the list of stories of the followed writers
and a list of suggested stories that the user could be interested in.
If not logged, the anonymous user is redirected to the login page.

@stories.route('/', methods=['GET'])
def _myhome(message=''):
    if current_user.is_anonymous:
        return redirect("/login", code=302)
    followingStories= (db.session.query(Story).join(Follow, Story.author_id == Follow.user_id)
                                             .filter(Follow.followed_by_id == current_user.id)
                                             .filter(Story.published==1)
                                             .order_by(Story.date.desc())
                                             .all())
    suggestedStories=get_suggested_stories(current_user.id)
    return render_template("home.html", message=message, followingstories=followingStories, suggestedstories=suggestedStories)




This route returns, if the user is logged in, the list of all stories from all users
in the social network. The POST is used to filters those stories by user picked date.
If not logged, the anonymous user is redirected to the login page.

@stories.route('/explore', methods=['GET', 'POST'])
def _stories(message=''):
    if current_user.is_anonymous:
        return redirect("/login", code=302)

    allstories = db.session.query(Story).filter_by(published=1).order_by(Story.date.desc())
    if request.method == 'POST':
        beginDate = request.form["beginDate"]
        if beginDate == "" or not is_date(beginDate):
            beginDate = str(datetime.date.min)

        endDate = request.form["endDate"]
        if endDate == "" or not is_date(endDate):
            endDate = str(datetime.date.max)

        filteredStories = allstories.filter(Story.date.between(beginDate, endDate))
        return render_template("explore.html", message="Filtered stories", stories=filteredStories, url="/story/")
    else:
        return render_template("explore.html", message=message, stories=allstories)


This route requires the user to be logged in and returns an entire published story
with relative dice rolled and author wall link. In the view, the user will find 
options for like/dislike/delete (if authorized) options.

@stories.route('/story/<int:story_id>')
@login_required
def _story(story_id, message=''):
    story = Story.query.filter_by(id=story_id).filter_by(published=1).first()
    if story is None:
        message = 'Ooops.. Story not found!'
        return render_template("message.html", message=message)

    rolls_outcome = json.loads(story.rolls_outcome)
    return render_template("story.html", message=message, story=story,
                           url="/story/", current_user=current_user, rolls_outcome=rolls_outcome)


In this route the user must be be logged in, and deletes a published story
if the author id is the same of the user calling it.

@stories.route('/story/<story_id>/delete')
@login_required
def _delete_story(story_id):
    story = Story.query.filter_by(id=story_id).filter_by(published=1)
    if story.first() is None:
        abort(404)

    if story.first().author_id != current_user.id:
        abort(401)
    else:
        story.delete()
        db.session.commit()
        message = 'Story sucessfully deleted'
    return render_template("message.html", message=message)


This route requires the user to be logged in, and returns a random story
written from someone else user.

@stories.route('/random_story')
@login_required
def _random_story(message=''):
    story = Story.query.filter(Story.author_id != current_user.id).filter_by(published=1).order_by(func.random()).first()
    if story is None:
        message = 'Ooops.. No random story for you!'
        rolls_outcome = []
    else:
        rolls_outcome = json.loads(story.rolls_outcome)
    return render_template("story.html", message=message, story=story,
                           url="/story/", current_user=current_user, rolls_outcome=rolls_outcome)


The route can be used by a logged in user to like a published story.

@stories.route('/story/<int:story_id>/like')
@login_required
def _like(story_id):
    story = Story.query.filter_by(id=story_id).filter_by(published=1).first()
    if story is None:
        abort(404)

    async_like.delay(story_id)
    message = 'Like added!'
    return jsonify({'message' : message})


The route can be used by a logged in user to dislike a published story.

@stories.route('/story/<int:story_id>/dislike')
@login_required
def _dislike(story_id):
    story = Story.query.filter_by(id=story_id).filter_by(published=1).first()
    if story is None:
        abort(404)
        
    async_dislike.delay(story_id)
    message = 'Dislike added!'
    return jsonify({'message' : message})


The route can be used by a logged in user to remove a like
from a published story.

@stories.route('/story/<int:story_id>/remove_like')
@login_required
def _remove_like(story_id):
    story = Story.query.filter_by(id=story_id).first()
    if story is None:
        abort(404)
    
    async_remove_like.delay(story_id)
    message = 'You removed your like'
    return jsonify({'message' : message})
    

The route can be used by a logged in user and to remove a dislike
from a published story.

@stories.route('/story/<int:story_id>/remove_dislike')
@login_required
def _remove_dislike(story_id):
    story = Story.query.filter_by(id=story_id).first()
    if story is None:
        abort(404)

    async_remove_dislike.delay(story_id)
    message = 'You removed your dislike!'
    return jsonify({'message' : message})


This route requires the user to be logged in and lets the user select the dice set theme
and the number of dice to be rolled.
If no pending drafts are present with the same selected dice set theme, it redirects 
to /write_story displaying the dice roll outcome. 
Otherwise it redirects to /write_story of the pending draft.

@stories.route('/stories/new_story', methods=['GET', 'POST'])
@login_required
def new_stories():
    if request.method == 'GET':
        dice_themes = retrieve_themes()
        return render_template("new_story.html", themes=dice_themes)
    else:
        stry = Story.query.filter(Story.author_id == current_user.id).filter(
            Story.published == 0).filter(Story.theme == request.form["theme"]).first()
        if stry != None:
            return redirect("/write_story/"+str(stry.id), code=302)

        dice_set = retrieve_dice_set(request.form["theme"])
        face_set = dice_set.throw()[:int(request.form["dice_number"])]
        new_story = Story()
        new_story.author_id = current_user.id
        new_story.theme = request.form["theme"]
        new_story.rolls_outcome = json.dumps(face_set)
        db.session.add(new_story)
        db.session.flush()
        db.session.commit()
        db.session.refresh(new_story)
        return redirect('/write_story/'+str(new_story.id), code=302)


This route requires the user to be logged in and lets the user write a story or modify 
a draft while diplaying the related dice roll outcome.
In both cases the used will be able to save it as draft or publish it.

@stories.route('/write_story/<story_id>', methods=['POST', 'GET'])
@login_required
def write_story(story_id):
    story = Story.query.filter_by(id=story_id).filter_by(published=0).first()
    if story is None:
        abort(404)

    if current_user.id != story.author_id:
        abort(401)

    rolls_outcome = json.loads(story.rolls_outcome)
    faces = _throw_to_faces(rolls_outcome)

    if request.method == 'POST':
        story.text = request.form["text"]
        story.title = request.form["title"]
        story.published = 1 if request.form["store_story"] == "1" else 0

        if story.published == 1 and (story.title == "" or story.title == "None"):
            db.session.rollback()
            message = "You must complete the title in order to publish the story"
            return render_template("/write_story.html", theme=story.theme, outcome=rolls_outcome,
                                   title=story.title, text=story.text, message=message)

        if story.published and not is_story_valid(story.text, faces):
            db.session.rollback()
            message = "You must use all the words of the outcome!"
            return render_template("/write_story.html", theme=story.theme, outcome=rolls_outcome, title=story.title, text=story.text, message=message)
        
        if story.published == 0 and (story.title == "None" or len(story.title.replace(" ", ""))==0):
            story.title="Draft("+str(story.theme)+")" 
        db.session.commit()

        if story.published == 1:
            return redirect("../story/"+str(story.id), code=302)
        elif story.published == 0:
            return redirect("../", code=302)

    return render_template("/write_story.html", theme=story.theme, outcome=rolls_outcome, title=story.title, text=story.text, message="")


Function to be called during story publishing that checks if the story
contains the rolled dice faces.
If it return False, stop publishing and return an error message.

def is_story_valid(story_text, dice_roll):
    split_story_text = re.findall(r"[\w']+|[.,!?;]", story_text.lower())
    for word in dice_roll:
        if word.lower() not in split_story_text:
            return False
    return True

"""