# Create your tasks here
from __future__ import absolute_import, unicode_literals

import imaplib
import email
from dateutil import parser
import base64
import json
from .models import EmailItem

from celery import Celery, shared_task
from celery.utils.log import get_task_logger
from celery.contrib import rdb
logger = get_task_logger(__name__)


from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.core.cache import cache

channel_layer = get_channel_layer()


@shared_task
def add(channel_name, x, y):
    logger.info('{}==={}==={}'.format(channel_name, x, y))
    result = x + y
    async_to_sync(channel_layer.send)(
        channel_name, {"type": "chat.message", "message": str(result)})


@shared_task
def get_emails_task(user_email, password):
    logger.info(' before start task: username: {}, pass: {}'.format(user_email, password))
    # imaplib module implements connection based on IMAPv4 protocol
    mail = imaplib.IMAP4_SSL('imap.gmail.com')
    context = { 'status': True, 'msg': 'Get emails successfully' }
    all_emails = EmailItem.objects.all()
    logger.info('start task: username: {}, pass: {}, leng: {}'.format(user_email, password, len(all_emails)))
    try:
        mail.login(user_email, password)

        mail.list() # Lists all labels in GMail
        mail.select('inbox') # Connected to inbox.

        result, data = mail.search(None, 'FROM', 'upwork@e.upwork.com')
        logger.info('result: ')
        # search and return uids instead
        i = len(data[0].split()) # data[0] is a space separate string
        
        for x in range(3):
            latest_email_uid = data[0].split()[x] # unique ids wrt label selected
            result, email_data = mail.uid('fetch', latest_email_uid, '(RFC822)')
            # fetch the email body (RFC822) for the given ID
            if email_data is None or email_data[0] is None:
                continue

            raw_email_string = email_data[0][1]
            # converts byte literal to string removing b''
            email_message = email.message_from_string(raw_email_string)

            # this will loop through all the available multiparts in mail
            email_content = ""
            for part in email_message.walk():
                if part.get_content_type() == 'text/plain': # ignore attachments/html
                    body = part.get_payload(decode=True)
                    email_content = str(body)
                else:
                    continue

            # rdb.set_trace()
            # parse attributes and save email into db
            date_obj = email_message['Date']
            dt = parser.parse(date_obj)
            from_val = email_message['From']
            from_username=from_val.split('<')[0].strip()
            try:
                from_email = from_val.split('<')[1].strip().replace('>', '')
            except:
                from_email = from_val

            obj, created = EmailItem.objects.get_or_create(
                                    from_username=from_username,
                                    from_email=from_email,
                                    to_email=email_message['Delivered-To'],
                                    subject=email_message['Subject'],
                                    preview_text=email_message['snippet'],
                                    body_text= str(email_content),
                                    day_of_week= dt.weekday(),
                                    time_of_day=dt.time(),
                                    date_sent=dt.date())

            logger.info('{}======{}'.format(obj, created))
        return True
    except Exception as e:
        return False 