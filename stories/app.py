from stories.database import db, Story
from stories.views import blueprints
from swagger_ui import api_doc
from flakon import create_app

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
    
    api_doc(app, config_path='./stories-specs.yaml', url_prefix='/api', title='API doc')
    db.init_app(app)
    db.create_all(app=app)
    
    with app.app_context():
        # TODO Initialize env to test
        story= db.session.query(Story).first()
        if story is None:
            example = Story()
            example.title = 'My first story!'
            example.rolls_outcome = '["bike", "bus"]'
            example.text = 'With my bike, I am faster than a bus!!!!'
            example.theme = 'Mountain'
            example.published = 0
            example.likes = 42
            example.dislikes = 5
            example.author_id = 1
            db.session.add(example)
            example = Story()
            example.title = 'My second story!'
            example.rolls_outcome = '["bike", "bus"]'
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
