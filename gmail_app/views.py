# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import pickle
import os.path
from dateutil import parser
import email
import base64
import json
import copy
from datetime import datetime
from decimal import *

from httplib2 import Http
from googleapiclient.discovery import build
from oauth2client import file, client, tools
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

from django.shortcuts import render
from django.http.response import JsonResponse, HttpResponse
from django.contrib.auth.decorators import login_required

from driptools.settings import BASE_DIR
from .models import EmailItem, Event, Report
from .tasks import add, make_report
from utils.utils import get_top_ngrams, get_word_count, validate_username
from utils.send_email import send_email

import imaplib
import string
import nltk
from nltk import bigrams, trigrams, ngrams, word_tokenize, FreqDist

DAYS =(
    'Mon',
    'Tue',
    'Wed',
    'Thu',
    'Fri',
    'Sat',
    'Sun',
)


import pdb

# Create your views here.
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.metadata'
]

def get_emails(count):
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                BASE_DIR + '/credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open(BASE_DIR + '/token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('gmail', 'v1', credentials=creds)
    
    # Call the Gmail API to fetch INBOX
    results = service.users().messages().list(userId='me', labelIds = ['INBOX']).execute()
    messages = results.get('messages', [])

    if not messages:
        print("No messages found.")
    else:
        print("Message snippets:")
        for message in messages[:count]:
            msg = service.users().messages().get(userId='me',
                                                id=message['id'],
                                                metadataHeaders=[
                                                    'Date',
                                                    'From',
                                                    'Delivered-To',
                                                    'snippet'
                                                ]).execute()
            headers = dict()
            for header in msg['payload']['headers']:
                headers[header['name']] = header['value']

            date_obj = headers['Date']
            dt = parser.parse(date_obj)
            from_val = headers['From']
            from_username=from_val.split('<')[0].strip()
            try:
                from_email = from_val.split('<')[1].strip().replace('>', '')
            except:
                from_email = from_val

            try:
                detail_msg = service.users().messages().get(userId='me',
                                                id=message['id'],
                                                format="raw").execute()
                message_body = ''
                msg_str = base64.urlsafe_b64decode(detail_msg['raw'].encode('ASCII'))

                mime_msg = email.message_from_string(msg_str)
                for parts in mime_msg.walk():
                      # mime_msg.get_payload()
                      # if parts.get_content_type() == 'application/xml':
                      #   mytext= base64.urlsafe_b64decode(parts.get_payload().encode('UTF-8'))
                      if parts.get_content_type() == 'text/plain':
                        parsed_msg=base64.urlsafe_b64decode(parts.get_payload().encode('UTF-8'))
                        try:
                            message_body = parsed_msg.encode()
                        except:
                            message_body = ''

            except Exception as e:
                print('Error when parsing: ', e)
                message_body = ""

            print('@@@@: ', message_body)
            # obj, created = EmailItem.objects.get_or_create(
            #                     from_username=from_val.split('<')[0].strip(),
            #                     from_email=from_email,
            #                     to_email=headers['Delivered-To'],
            #                     subject=headers['Subject'],
            #                     preview_text=msg['snippet'],
            #                     body_text= str(message_body),
            #                     day_of_week= dt.weekday(),
            #                     time_of_day=dt.time(),
            #                     date_sent=dt.date())

    return True

@login_required
def dashboard(request):
    reports = Report.objects.all()
    return render(request, 'dashboard.html', { 'reports': reports })


@login_required
def get_detail_report(request, id):
    try:
        report = Report.objects.get(pk=id)
        return render(request, 'report_detail.html', { 'report': report })
    except:
        return render(request, 'report_detail.html',
                        { 'error_msg': 'No report data with id: {}'.format(id) })


def create_report(request):
    email = request.POST.get('email', None)
    password = request.POST.get('password', None)
    from_email = request.POST.get('from_email', None)
    error_context = { 'status': False }

    if not email:
        error_context['error'] = { 'msg': "Email field is required!" }
        return JsonResponse(error_context, status=400)

    if not password:
        error_context['error'] = { 'msg': "Password field is required!" }
        return JsonResponse(error_context, status=400)

    mail = imaplib.IMAP4_SSL('imap.gmail.com')
    try:
        mail.login(email, password)
    except Exception as e:
        error_context['error'] = { 'msg': "Please check your email or password to search!" }
        return JsonResponse(error_context, status=400)

    # task_id = make_report.delay(email, password, from_email, 'collinvargo530@gmail.com')
    task_id = make_report.delay(email, password, from_email, request.user.email)

    return JsonResponse({ 'status': True })

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
        try:
            report['from_username'] = entry.from_username
            report['from_email'] = entry.from_email
            report['to_email'] = entry.to_email
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

        except Exception as e:
            print(e)
            pdb.set_trace()

    for key in email_sent_time:
        email_sent_time[key] = '{0:2f}'.format(
            float(email_sent_time[key] / total_count * 100))
    
    for key in email_sent_day:
        email_sent_day[key] = '{0:2f}'.format(
            float(email_sent_day[key] / total_count * 100))

    report['email_sent_day'] = email_sent_day
    report['email_sent_time'] = email_sent_time

    print(subject_top_uni_words)
    try:
        subject_ngram_hash['unigram'] = validate_ngrams(subject_top_uni_words)
        subject_ngram_hash['bigram'] = validate_ngrams(subject_top_bi_words)
        subject_ngram_hash['trigram'] = validate_ngrams(subject_top_tri_words)
    except Exception as e:
        print(e)
        pdb.set_trace()
    try:
        preview_ngram_hash['unigram'] = validate_ngrams(preview_top_uni_words)
        preview_ngram_hash['bigram'] = validate_ngrams(preview_top_bi_words)
        preview_ngram_hash['trigram'] = validate_ngrams(preview_top_tri_words)
    except:
        pdb.set_trace()

    try:
        body_ngram_hash['unigram'] = validate_ngrams(body_top_uni_words)
        body_ngram_hash['bigram'] = validate_ngrams(body_top_bi_words)
        body_ngram_hash['trigram'] = validate_ngrams(body_top_tri_words)
    except:
        pdb.set_trace()


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

    report_item, result = Report.objects.get_or_create(from_username=report['from_username'],
                        from_email=report['from_email'],
                        to_email=report['to_email'],
                        total=report['total'],
                        email_sent_time=json.dumps(email_sent_time),
                        email_sent_day=json.dumps(email_sent_day),
                        subject_top_3=json.dumps(subject_ngram_hash),
                        preview_top_3=json.dumps(preview_ngram_hash),
                        body_top_3=json.dumps(body_ngram_hash),
                        average_word_count=average_word_count,
                        median_word_count=median_word_count,
                        high_word_count=high_word_count,
                        low_word_count=low_word_count,
                        longest_interval=max_interval_between_emails,
                        average_interval=int(total_intervals/report['total']),
                        first_date=report['first_date'])

    return report_item