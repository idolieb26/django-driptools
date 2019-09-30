# Create your tasks here
from __future__ import absolute_import, unicode_literals

import imaplib
import email
from dateutil import parser
import base64
import json
from datetime import datetime
from decimal import *
import string
import nltk
from nltk import bigrams, trigrams, ngrams, word_tokenize, FreqDist

from celery import Celery, shared_task
from celery.utils.log import get_task_logger
from celery.contrib import rdb

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.core.cache import cache

from utils.send_email import send_email
from utils.utils import get_top_ngrams, get_word_count, validate_username
from gmail_app.models import Report, EmailItem

channel_layer = get_channel_layer()
logger = get_task_logger(__name__)


def analyze(email=None):
    if email:
        filtered_emails = EmailItem.objects.filter(from_email=email)
    else:
        filtered_emails = EmailItem.objects.all()

    total_count = len(filtered_emails)

    report = dict()
    last_date = None
    max_interval_between_emails = 0 # days
    subject_ngram_hash = {'unigram': {}, 'bigram': {}, 'trigram': {} }
    preview_ngram_hash = {'unigram': {}, 'bigram': {}, 'trigram': {} }
    body_ngram_hash = {'unigram': {}, 'bigram': {}, 'trigram': {} }
    report['total'] = len(filtered_emails)

    for entry in filtered_emails:
        report['first_date'] = filtered_emails[total_count-1].created
        email_sent_time = {}
        email_sent_day = {}
        try:
            report['from_username'] = entry.from_username
            report['from_email'] = entry.from_email
            report['to_email'] = entry.to_email
            report['body_word_count'] = entry.body_word_count
            entry_hour = entry.created.strftime("%-I_%p")
            entry_week_day = entry.created.strftime("%A")
            if entry_hour in email_sent_time:
                email_sent_time[entry_hour] = email_sent_time[entry_hour] + 1
            else:
                email_sent_time[entry_hour] = 1
            if entry_week_day in email_sent_day:
                email_sent_day[entry_week_day] = email_sent_day[entry_week_day] + 1
            else:
                email_sent_day[entry_week_day] = 1

            if last_date is not None:
                delta = entry.created.date() - last_date.date()
                delta_day = abs(delta.days)
                if delta_day > max_interval_between_emails:
                    max_interval_between_emails = delta_day

            last_date = entry.created
        except Exception as e:
            logger.info(e.message)

    for key in email_sent_time:
        email_sent_time[key] = '{0:2f}'.format(
            Decimal(email_sent_time[key] / total_count * 100))
    
    for key in email_sent_day:
        email_sent_day[key] = '{0:2f}'.format(
            Decimal(email_sent_day[key] / total_count * 100))

    report['email_sent_day'] = email_sent_day
    report['email_sent_time'] = email_sent_time

    report_item = Report(from_username=report['from_username'],
                        from_email=report['from_email'],
                        to_email=report['to_email'],
                        total=report['total'],
                        email_sent_time=json.dumps(email_sent_time),
                        email_sent_day=json.dumps(email_sent_day),
                        first_date=report['first_date'])
    report_item.save()

    return report

def get_emails_with_imap(user_email, password, search_email='upwork@e.upwork.com'):
    mail = imaplib.IMAP4_SSL('imap.gmail.com')
    context = { 'status': True, 'msg': 'Get emails successfully' }
    # try:
    mail.login(user_email, password)

    mail.list() # Lists all labels in GMail
    mail.select('inbox') # Connected to inbox.

    # result, data = mail.search(None, ('Reply-to: "{}"'.format(search_email)))
    result, data = mail.uid('search', '(HEADER From "{}")'.format(search_email))
    # search and return uids instead
    try:
        i = len(data[0].split()) # data[0] is a space separate string
    except Exception as e:
        raise Exception(e)

    # get emails
    for x in range(i):
        raw_email_string = None
        latest_email_uid = data[0].split()[x] # unique ids wrt label selected
        res, email_data = mail.uid('fetch', latest_email_uid, '(RFC822)')
        # fetch the email body (RFC822) for the given ID
        if email_data is None or email_data[0] is None:
            continue

        raw_email_string = email_data[0][1]
        # converts byte literal to string removing b''
        email_message = email.message_from_string(raw_email_string.decode('utf-8'))

        # this will loop through all the available multiparts in mail
        email_content = ""
        for part in email_message.walk():
            print('type: ', part.get_content_type())
            if part.get_content_type() == 'text/plain': # ignore attachments/html
                body = part.get_payload(decode=True)
                email_content = email_content + str(body)
            else:
                continue
        
        # parse attributes and save email into db
        date_obj = email_message['Date']
        dt = parser.parse(date_obj)
        from_val = email_message['From']
        from_username=from_val.split('<')[0].strip()

        try:
            from_email = from_val.split('<')[1].strip().replace('>', '')
        except:
            from_email = from_val

        # uni_words, bi_words, tri_words = get_top_ngrams(email_content)
        try:
            obj, created = EmailItem.objects.get_or_create(
                                    from_username=from_username,
                                    from_email=from_email,
                                    to_email=email_message['Delivered-To'],
                                    subject=email_message['Subject'],
                                    preview_text=email_message['snippet'],
                                    body_text= email_content,
                                    day_of_week= dt.weekday(),
                                    time_of_day=dt.time(),
                                    subject_word_count = get_word_count(email_message['Subject']),
                                    preview_word_count = get_word_count(email_message['snippet']),
                                    body_word_count = get_word_count(email_content),
                                    date_sent=dt.date())
        except Exception as e:
            print('Error get email: ', e)
            raise Exception(e)
    
    return True

@shared_task
def add(channel_name, x, y):
    logger.info('{}==={}==={}'.format(channel_name, x, y))
    result = x + y
    async_to_sync(channel_layer.send)(
        channel_name, {"type": "chat.message", "message": str(result)})


@shared_task
def make_report(email, password, from_email, to):
    try:
        get_emails_with_imap(email, password, from_email)
        report_item = analyze(from_email)
        recipient_list = [to]
        if report_item:
            report_context = {
                'sender': report_item['from_username'],
                'from_email': report_item['from_email'],
                'to_email': report_item['to_email'],
            }

            send_email(report_item, recipient_list)
            logger.info('Sent email!!')
    except Exception as e:

        logger.info('Gmail_app task: {}'.format(e))
        return False 