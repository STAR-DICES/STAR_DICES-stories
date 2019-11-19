from monolith.database import db, Story
from stories.views import blueprints
from stories import celeryApp

from flakon import create_app

def start(test = False):
    app = create_app(blueprints = blueprints)
    app.config['WTF_CSRF_SECRET_KEY'] = 'A SECRET KEY'
    app.config['SECRET_KEY'] = 'ANOTHER ONE'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///auth.db'
    if test:
        app.config['TESTING'] = True
        app.config['CELERY_ALWAYS_EAGER'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db.init_app(app)
    db.create_all(app=app)
    
    celery = celeryApp.make_celery(app)
    celeryApp.celery = celery
    
    with app.app_context():
        # TODO Initialize env to test
        example = Story()
        example.title = 'My first story!'
        example.rolls_outcome = '[["bike", "static/Mountain/bike.PNG"], ["bus", "static/Mountain/bus.PNG"]]'
        example.text = 'With my bike, I am faster than a bus!!!!'
        example.theme = 'Mountain'
        example.published = 1
        example.likes = 42
        example.dislikes = 5
        example.author_id = 1
        db.session.add(example)
        db.session.commit()
        
    return app


if __name__ == '__main__':
    app = start()
    app.run()
