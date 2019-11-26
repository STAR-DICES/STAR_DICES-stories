from stories.views.test.TestHelper import TestHelper
from stories.database import db, Story
import json

class TestAuth(TestHelper):


    def test_stories(self):
        
        # all stories
        reply = self.client.get("/stories?writer_id=1")
        self.assertEqual(reply.status_code, 200)
        json = reply.json
        story_list = json['stories']
        self.assertEqual(len(story_list), 1)
        
        # filter and get correct story
        reply = self.client.get("/stories?start=" + "01/01/1999" + "&end=" + "09/09/2222" + "&writer_id=1")
        self.assertEqual(reply.status_code, 200)
        
        reply = self.client.get("/stories?start=" + "01/01/2200" + "&end=" + "09/09/2222" + "&writer_id=1")
        self.assertEqual(reply.status_code, 200)
        # get also drafts
        
        reply = self.client.get("/stories?writer_id=1" + "&drafts=True")
        json = reply.json
        story_list = json['stories']
        self.assertEqual(len(story_list), 2)
        
        
    def test_get_story(self):
        
        reply = self.client.get("/story/1/1")
        self.assertEqual(reply.status_code, 200)
        story = json.loads(reply.data)
        self.assertEqual(story['id'], 1)
        
        reply = self.client.get("/story/5/1")
        self.assertEqual(reply.status_code, 404)
        
    def test_delete_story(self):
        
        reply = self.client.delete("/story/3/1")
        self.assertEqual(reply.status_code, 404) 
        
        reply = self.client.delete("/story/1/3")
        self.assertEqual(reply.status_code, 401)  
        
        reply = self.client.delete("/story/2/1")
        self.assertEqual(reply.status_code, 200)       
        
    def test_retrieve_set(self):
    
        reply = self.client.get("/retrieve-set-themes")
        themes = json.loads(reply.data)
        self.assertEqual(themes['dice_number'], 6)
        self.assertEqual(len(themes['themes']), 4)
        
    def test_random_story(self):
        
        reply = self.client.get("/random_story/1")
        self.assertEqual(reply.status_code, 200)
        
    
        
        
        
