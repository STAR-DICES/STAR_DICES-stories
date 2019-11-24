from stories.views.test.TestHelper import TestHelper
from stories.database import db, Story

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
        
        # get also drafts
        
        
        
        
        
