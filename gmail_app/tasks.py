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
import copy
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

DAYS =(
    'Mon',
    'Tue',
    'Wed',
    'Thu',
    'Fri',
    'Sat',
    'Sun',
)

# take second element for sort
def take_count(elem):
    try:
        return elem['count']
    except Exception as e:
        raise Exception(e)

def validate_ngrams(new_hash):
    if new_hash is not None and len(new_hash.keys()) > 0:
        arr = [{'text': key, 'count': new_hash[key]} for key in new_hash]
        arr.sort(key=take_count, reverse=True)
        return arr[:3]
    else:
        return []

def sum_arrays_without_duplicate(hash, arr):
    new_hash = copy.deepcopy(hash)
    for item in arr:
        hash_key = item['text'].replace(' ', '_')
        if hash_key not in new_hash and item['count'] != 0:
            new_hash[hash_key] = item['count']

    return new_hash


def analyze(email=None):
    if email:
        filtered_emails = EmailItem.objects.filter(from_email=email)
    else:
        filtered_emails = EmailItem.objects.all()

    total_count = len(filtered_emails)

    report = dict()
    last_date = None
    max_interval_between_emails = 0 # days
    subject_ngram_hash = {'unigram': None, 'bigram': None, 'trigram': None }
    preview_ngram_hash = {'unigram': None, 'bigram': None, 'trigram': None }
    body_ngram_hash = {'unigram': None, 'bigram': None, 'trigram': None }
    report = {
        'total': len(filtered_emails),
        'body_word_count': 0
    }

    email_sent_time = {}
    email_sent_day = {}
    subject_top_uni_words = {}
    subject_top_bi_words = {}
    subject_top_tri_words = {}
    preview_top_uni_words = {}
    preview_top_bi_words = {}
    preview_top_tri_words = {}
    body_top_uni_words = {}
    body_top_bi_words = {}
    body_top_tri_words = {}
    word_counts = []
    total_intervals = 0

    for entry in filtered_emails:
        report['first_date'] = filtered_emails[total_count-1].created
        report['from_username'] = entry.from_username
        report['from_email'] = entry.from_email
        report['to_email'] = entry.to_email
        try:
            if entry.body_word_count:
                report['body_word_count'] = report['body_word_count'] + \
                                            entry.body_word_count
            word_counts.append(entry.body_word_count)
            entry_hour = entry.time_of_day.strftime("%-I_%p")
            entry_week_day = DAYS[entry.day_of_week]

            if entry_hour in email_sent_time:
                email_sent_time[entry_hour] = email_sent_time[entry_hour] + 1
            else:
                email_sent_time[entry_hour] = 1

            if entry_week_day in email_sent_day:
                email_sent_day[entry_week_day] = email_sent_day[entry_week_day] + 1
            else:
                email_sent_day[entry_week_day] = 1

            if last_date is not None:
                delta = entry.date_sent - last_date
                delta_day = abs(delta.days)
                if delta_day > max_interval_between_emails:
                    max_interval_between_emails = delta_day

                total_intervals = total_intervals + delta_day

            last_date = entry.date_sent
            
            top_uni_words, top_bi_words, top_tri_words = get_top_ngrams(entry.subject)
            # subject_top_uni_words = subject_top_uni_words + top_uni_words
            # subject_top_bi_words = subject_top_bi_words + top_bi_words
            # subject_top_tri_words = subject_top_tri_words + top_tri_words
            subject_top_uni_words = sum_arrays_without_duplicate(
                subject_top_uni_words,
                top_uni_words)
            subject_top_bi_words = sum_arrays_without_duplicate(
                subject_top_bi_words,
                top_bi_words)
            subject_top_tri_words = sum_arrays_without_duplicate(
                subject_top_tri_words,
                top_tri_words)

            top_uni_words, top_bi_words, top_tri_words = get_top_ngrams(entry.preview_text)
            # preview_top_uni_words = preview_top_uni_words + top_uni_words
            # preview_top_bi_words = preview_top_bi_words + top_bi_words
            # preview_top_tri_words = preview_top_tri_words + top_tri_words
            preview_top_uni_words = sum_arrays_without_duplicate(
                preview_top_uni_words, top_uni_words)
            preview_top_bi_words = sum_arrays_without_duplicate(
                preview_top_bi_words, top_bi_words)
            preview_top_tri_words = sum_arrays_without_duplicate(
                preview_top_tri_words, top_tri_words)

            top_uni_words, top_bi_words, top_tri_words = get_top_ngrams(entry.body_text)
            # body_top_uni_words = body_top_uni_words + top_uni_words
            # body_top_bi_words = body_top_bi_words + top_bi_words
            # body_top_tri_words = body_top_tri_words + top_tri_words

            body_top_uni_words = sum_arrays_without_duplicate(
                body_top_uni_words, top_uni_words)
            body_top_bi_words = sum_arrays_without_duplicate(
                body_top_bi_words, top_bi_words)
            body_top_tri_words = sum_arrays_without_duplicate(
                body_top_tri_words, top_tri_words)

            last_date = entry.date_sent
        except Exception as e:
            logger.info(e)

    for key in email_sent_time:
        email_sent_time[key] = '{0:2f}'.format(
            float(email_sent_time[key] / total_count * 100))
    
    for key in email_sent_day:
        email_sent_day[key] = '{0:2f}'.format(
            float(email_sent_day[key] / total_count * 100))

    report['email_sent_day'] = email_sent_day
    report['email_sent_time'] = email_sent_time

    subject_ngram_hash['unigram'] = validate_ngrams(subject_top_uni_words)
    subject_ngram_hash['bigram'] = validate_ngrams(subject_top_bi_words)
    subject_ngram_hash['trigram'] = validate_ngrams(subject_top_tri_words)
    preview_ngram_hash['unigram'] = validate_ngrams(preview_top_uni_words)
    preview_ngram_hash['bigram'] = validate_ngrams(preview_top_bi_words)
    preview_ngram_hash['trigram'] = validate_ngrams(preview_top_tri_words)
    body_ngram_hash['unigram'] = validate_ngrams(body_top_uni_words)
    body_ngram_hash['bigram'] = validate_ngrams(body_top_bi_words)
    body_ngram_hash['trigram'] = validate_ngrams(body_top_tri_words)

    average_word_count = 0
    median_word_count = 0
    high_word_count = 0
    low_word_count = 0

    if word_counts and len(word_counts) > 0:
        word_counts.sort()
        average_word_count=report['body_word_count']/report['total']
        median_word_count=word_counts[int(len(word_counts)/2)-1]
        high_word_count=word_counts[len(word_counts)-1]
        low_word_count=word_counts[0]

    report_item, created = Report.objects.get_or_create(from_username=report['from_username'],
                        from_email=report['from_email'],
                        to_email=report['to_email'],
                        total=report['total'],
                        email_sent_time=json.dumps(email_sent_time),
                        email_sent_day=json.dumps(email_sent_day),
                        subject_top_3=json.dumps(subject_ngram_hash),
                        preview_top_3=json.dumps(preview_ngram_hash),
                        body_top_3=json.dumps(body_ngram_hash),
                        average_word_count=int(average_word_count),
                        median_word_count=median_word_count,
                        high_word_count=high_word_count,
                        low_word_count=low_word_count,
                        longest_interval=max_interval_between_emails,
                        average_interval=int(total_intervals/report['total']),
                        first_date=report['first_date'])

    return report_item

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

            send_email(report_item, recipient_list)
            logger.info('Sent email!!')
    except Exception as e:

        logger.info('Gmail_app task: {}'.format(e))
        return False 