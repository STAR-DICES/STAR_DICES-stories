from stories.views.test.TestHelper import TestHelper
from stories.database import db, Story
import json

class TestAuth(TestHelper):


    def test_stories(self):
        
        # all stories
        reply = self.client.get("/stories")
        self.assertEqual(reply.status_code, 200)
        json = reply.json
        story_list = json['stories']
        self.assertEqual(len(story_list), 4)
        
        # all stories by writer
        reply = self.client.get("/stories?writer_id=1")
        self.assertEqual(reply.status_code, 200)
        json = reply.json
        story_list = json['stories']
        self.assertEqual(len(story_list), 3)
        
        # filter and get correct story
        reply = self.client.get("/stories?start=" + "1999/01/01" + "&end=" + "2222/01/01" + "&writer_id=1")
        self.assertEqual(reply.status_code, 200)
        json = reply.json
        story_list = json['stories']
        self.assertEqual(len(story_list), 3)
        
        # get also drafts
        reply = self.client.get("/stories?writer_id=1" + "&drafts=True")
        json = reply.json
        story_list = json['stories']
        self.assertEqual(len(story_list), 3)
        
        
    def test_get_story(self):
        
        reply = self.client.get("/story/1/1")
        self.assertEqual(reply.status_code, 200)
        story = json.loads(reply.data)
        self.assertEqual(story['id'], 1)
        
        reply = self.client.get("/story/5/1")
        self.assertEqual(reply.status_code, 404)
        
    def test_delete_story(self):
    
        # not existing story
        reply = self.client.delete("/story/5/1")
        self.assertEqual(reply.status_code, 404) 
        
        # not the author
        reply = self.client.delete("/story/1/5")
        self.assertEqual(reply.status_code, 401)  
        
        reply = self.client.delete("/story/3/1")
        self.assertEqual(reply.status_code, 200)       
        
    def test_retrieve_set(self):
    
        reply = self.client.get("/retrieve-set-themes")
        themes = json.loads(reply.data)
        self.assertEqual(themes['dice_number'], 6)
        self.assertEqual(len(themes['themes']), 4)
        
    def test_random_story(self):
        
        reply = self.client.get("/random-story/1")
        self.assertEqual(reply.status_code, 200)
        
    def test_get_following_stories(self):
        
        # TIMEOUT
        reply = self.client.get("/following-stories/1")
        self.assertEqual(reply.status_code, 500) 
        
        reply = self.client.get("/following-stories/beh")
        self.assertEqual(reply.status_code, 404) 
        
    def test_get_writers_last_story(self):
        
        reply = self.client.get("/writers-last-stories")
        self.assertEqual(reply.status_code, 200)
        json = reply.json
        story_list = json['stories']
        self.assertEqual(len(story_list), 2)
        
        self.assertEqual(story_list[0]['id'], 4)
        self.assertEqual(story_list[1]['id'], 2)
        
    def test_add_remove_like(self):
        
        reply = self.client.post("/like/1")
        self.assertEqual(reply.status_code, 201)
        with self.context:
            s = Story.query.filter_by(id=1).first()
            self.assertEqual(s.likes, 43)
        
        reply = self.client.post("/like/1")
        self.assertEqual(reply.status_code, 201)
        with self.context:
            s = Story.query.filter_by(id=1).first()
            self.assertEqual(s.likes, 44)
        
        reply = self.client.post("/like/5")
        self.assertEqual(reply.status_code, 404)
        
        reply = self.client.delete("/like/1")
        self.assertEqual(reply.status_code, 200)
        with self.context:
            s = Story.query.filter_by(id=1).first()
            self.assertEqual(s.likes, 43)
    
    def test_add_remove_dislike(self):
    
        reply = self.client.post("/dislike/1")
        self.assertEqual(reply.status_code, 201)
        with self.context:
            s = Story.query.filter_by(id=1).first()
            self.assertEqual(s.dislikes, 6)
        
        reply = self.client.post("/dislike/1")
        self.assertEqual(reply.status_code, 201)
        with self.context:
            s = Story.query.filter_by(id=1).first()
            self.assertEqual(s.dislikes, 7)
        
        reply = self.client.post("/dislike/5")
        self.assertEqual(reply.status_code, 404)
        
        reply = self.client.delete("/dislike/1")
        self.assertEqual(reply.status_code, 200)
        with self.context:
            s = Story.query.filter_by(id=1).first()
            self.assertEqual(s.dislikes, 6)  
        
    def test_new_draft(self):
    
        data = {'user_id' : 2, 'author_name' : 'Pippo', 'theme' : 'Montagna', 'dice_number' : 4}
        reply = self.client.post("/new-draft", json=data)
        self.assertEqual(reply.status_code, 404)
        
        data = {'user_id' : 2, 'author_name' : 'Pippo', 'theme' : 'Mountain', 'dice_number' : 4}
        reply = self.client.post("/new-draft", json=data)
        self.assertEqual(reply.status_code, 200)

    def test_write_story(self):
    
        data = {'user_id' : 2, 'author_name' : 'Pluto', 'theme' : 'Mountain', 'dice_number' : 4}
        reply = self.client.post("/new-draft", json=data)
        self.assertEqual(reply.status_code, 200)
        
        data = {'story_id' : 5, 'title' : 'EE', 'text' : 'AO', 'published' : False}
        reply = self.client.put("/write-story", json=data)
        self.assertEqual(reply.status_code, 200)
        
        data = {'story_id' : 5, 'title' : '', 'text' : 'AO', 'published' : True}
        reply = self.client.put("/write-story", json=data)
        self.assertEqual(reply.status_code, 400)



        
        
        
