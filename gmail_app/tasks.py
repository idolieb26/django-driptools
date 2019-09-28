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
from utils.utils import get_top_ngrams, get_word_count
from gmail_app.models import Report, EmailItem

channel_layer = get_channel_layer()
logger = get_task_logger(__name__)


def analyze(email=None):
    if email:
        filtered_emails = EmailItem.objects.filter(from_email=email)
    else:
        filtered_emails = EmailItem.objects.all()

    report = dict()
    last_date = None
    max_interval_between_emails = 0 # days
    subject_ngram_hash = {'unigram': {}, 'bigram': {}, 'trigram': {} }
    preview_ngram_hash = {'unigram': {}, 'bigram': {}, 'trigram': {} }
    body_ngram_hash = {'unigram': {}, 'bigram': {}, 'trigram': {} }

    total_count = len(filtered_emails)
    report['total'] = len(filtered_emails)
    report['first_date'] = filtered_emails[total_count-1].created
    email_sent_time = {}
    email_sent_day = {}

    for entry in filtered_emails:
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

@shared_task
def add(channel_name, x, y):
    logger.info('{}==={}==={}'.format(channel_name, x, y))
    result = x + y
    async_to_sync(channel_layer.send)(
        channel_name, {"type": "chat.message", "message": str(result)})


@shared_task
def make_report(email, password):
    try:
        report_item = analyze(email)
        if report_item:
            report_context = {
                'sender': report_item['from_username'],
                'from_email': report_item['from_email'],
                'to_email': report_item['to_email'],
            }

            send_email(report_item)
    except Exception as e:
        logger.info('Gmail_app task: {}'.format(e.message))
        return False 