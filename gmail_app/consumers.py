import json

from channels.generic.websocket import WebsocketConsumer
from .tasks import add, get_emails_task

class ChatConsumer(WebsocketConsumer):
    groups = ["events"]

    def receive(self, text_data):
        # Here we receive some data from the client
        text_data_json = json.loads(text_data)
        message = text_data_json['message']
        task_type = text_data_json['type']
        if task_type and task_type == 'get_emails':
            add.delay(self.channel_name, 5,4)

        # Here we can process client data and send result back directly
        # to the client (by using his unique channel name - `self.channel_name`)
      
        # And send some result back to that client immediately
        self.send(text_data=json.dumps({'message': 'Your request was received!'}))

    def chat_message(self, event):
        message = event['message']

        # Send message to WebSocket
        self.send(text_data=json.dumps({
            'message': '[bot]: {}'.format(message)
        }))