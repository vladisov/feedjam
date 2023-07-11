import time
from model.model import Subscription
from typing import Callable


class SubscriptionListener:
    def __init__(self, subscription: Subscription,
                 handle_data: Callable[[str, str], None]
                 ) -> None:
        self.subscription = subscription
        self.last_checked = time.time()
        self.handle_data = handle_data

    def listen(self):
        subscription = self.subscription
        url, user_id = subscription.resource_url, subscription.user_id
        # while True:
        #     self.handle_data(url, user_id)
        #     time.sleep(600)  # Check every 10 minutes
        #     self.last_checked = time.time()
