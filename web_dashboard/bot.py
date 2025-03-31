import praw
import time
import logging
from datetime import datetime

class EvilRedditBot:
    def __init__(self):
        self.config = {
            'reddit': {},
            'bots': [{
                'subreddit': '',
                'protected_users': []
            }]
        }
        self.running = False
        self.reddit = None
        self.current_subreddit = None
        self.protected_users = []
        self.activity_log = []
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger('RedditBot')

    def authenticate(self):
        try:
            self.reddit = praw.Reddit(
                username=self.config['reddit']['username'],
                password=self.config['reddit']['password'],
                client_id=self.config['reddit']['client_id'],
                client_secret=self.config['reddit']['client_secret'],
                user_agent=self.config['reddit']['user_agent']
            )
            self.logger.info(f"Authenticated as {self.config['reddit']['username']}")
            return True
        except Exception as e:
            self.logger.error(f"Authentication failed: {str(e)}")
            return False

    def is_authenticated(self):
        return self.reddit is not None

    def process_submission(self, submission):
        if submission.author and submission.author.name in self.protected_users:
            return

        try:
            submission.upvote()
            self.logger.info(f"Upvoted submission: {submission.id}")
            
            if self.config['bots'][0]['actions']['comment']:
                response = self.config['bots'][0]['actions']['response_message']
                if response:
                    submission.reply(response)
                    self.logger.info(f"Commented on submission: {submission.id}")
        except Exception as e:
            self.logger.error(f"Error processing submission {submission.id}: {str(e)}")

    def run(self):
        if not self.authenticate():
            return False

        self.running = True
        self.current_subreddit = self.config['bots'][0]['subreddit']
        self.protected_users = self.config['bots'][0]['protected_users']
        self.logger.info(f"Bot started monitoring r/{self.current_subreddit}")

        while self.running:
            try:
                subreddit = self.reddit.subreddit(self.current_subreddit)
                for submission in subreddit.new(limit=5):
                    self.process_submission(submission)
                time.sleep(60)
            except Exception as e:
                self.logger.error(f"Error in main loop: {str(e)}")
                time.sleep(60)

        return True

    def stop(self):
        self.running = False
        self.logger.info("Bot stopped")