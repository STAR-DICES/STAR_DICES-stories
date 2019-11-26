from stories.database import db, Story, Dice, retrieve_dice_set, retrieve_themes, store_dice_set
from stories.views import blueprints
from swagger_ui import api_doc
from flakon import create_app
from stories.classes.Die import Die
from stories.classes.DiceSet import DiceSet

def start(test = False):
    app = create_app(blueprints = blueprints)
    app.config['WTF_CSRF_SECRET_KEY'] = 'A SECRET KEY'
    app.config['SECRET_KEY'] = 'ANOTHER ONE'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///stories.db'
    if test:
        app.config['TESTING'] = True
        app.config['CELERY_ALWAYS_EAGER'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    api_doc(app, config_path='./stories/stories-specs.yaml', url_prefix='/api', title='API doc')
    db.init_app(app)
    db.create_all(app=app)
    
    with app.app_context():
        # TODO Initialize env to test
        story= db.session.query(Story).first()
        if story is None:
            example = Story()
            example.title = 'My first story!'
            example.rolls_outcome = '[["bike", "static/Mountain/bike.PNG"], ["bus", "static/Mountain/bus.PNG"]]'
            example.text = 'With my bike, I am faster than a bus!!!!'
            example.theme = 'Mountain'
            example.published = 1
            example.author_name= 'Pippo'
            example.likes = 42
            example.dislikes = 5
            example.author_id = 1
            db.session.add(example)
            example = Story()
            example.title = 'My second story!'
            example.rolls_outcome = '[["bike", "static/Mountain/bike.PNG"], ["bus", "static/Mountain/bus.PNG"]]'
            example.text = 'With my bike, I am faster than a bus!!!!'
            example.theme = 'Mountain'
            example.published = 1
            example.author_name= 'Pluto'
            example.likes = 42
            example.dislikes = 5
            example.author_id = 2
            db.session.add(example)
            example = Story()
            example.title = 'My third story!'
            example.rolls_outcome = '[["bike", "static/Mountain/bike.PNG"], ["bus", "static/Mountain/bus.PNG"]]'
            example.text = 'With my bike, I am faster than a bus!!!!'
            example.theme = 'Mountain'
            example.published = 1
            example.author_name= 'Pippo'
            example.likes = 42
            example.dislikes = 5
            example.author_id = 1
            db.session.add(example)
            example = Story()
            example.title = 'My fourth story!'
            example.rolls_outcome = '["bike", "bus"]'
            example.rolls_outcome = '[["bike", "static/Mountain/bike.PNG"], ["bus", "static/Mountain/bus.PNG"]]'
            example.theme = 'Mountain'
            example.author_name= 'Pippo'
            example.published = 1
            example.likes = 42
            example.dislikes = 5
            example.author_id = 1
            db.session.add(example)
            db.session.commit()

        
        # Create dice sets if missing.
        themes = retrieve_themes()
        if not themes:
            die1 = Die(
                ['angry', 'bag', 'bike', 'bird', 'crying', 'moonandstars'],
                "N/A"
            )
            die2 = Die(
                ['bus', 'coffee', 'happy', 'letter', 'paws', 'plate'],
                "N/A"
            )
            die3 = Die(
                ['caravan', 'clock', 'drink', 'mouth', 'tulip', 'whale'],
                "N/A"
            )
            die4 = Die(
                ['baloon', 'bananas', 'cat', 'icecream', 'pencil', 'phone'],
                "N/A"
            )
            dice_set = DiceSet([die1, die2, die3], "Mountain")
            store_dice_set(dice_set)
            dice_set = DiceSet([die2, die3, die4], "Late night")
            store_dice_set(dice_set)
            dice_set = DiceSet([die3, die1, die4], "Travelers")
            store_dice_set(dice_set)
            dice_set = DiceSet([die2, die1, die4], "Youth")
            store_dice_set(dice_set)
            die = Die(["1", "2", "3"], "test_theme")
            dice_set = DiceSet([die], "test_theme")
        
    return app


if __name__ == '__main__':
    app = start()
    app.run()
