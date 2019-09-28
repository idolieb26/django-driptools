# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import pickle
import os.path
from dateutil import parser
import email
import base64
import json
from datetime import datetime
from decimal import *

from httplib2 import Http
from googleapiclient.discovery import build
from oauth2client import file, client, tools
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

from django.shortcuts import render
from django.http.response import JsonResponse
from django.contrib.auth.decorators import login_required

from driptools.settings import BASE_DIR
from .models import EmailItem, Event, Report
from .tasks import add, make_report
from utils.utils import get_top_ngrams, get_word_count
from utils.send_email import send_email

import imaplib
import string
import nltk
from nltk import bigrams, trigrams, ngrams, word_tokenize, FreqDist


import pdb

# Create your views here.
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.metadata'
]

def GetMimeMessage(service, user_id, msg_id):
  """Get a Message and use it to create a MIME Message.

  Args:
    service: Authorized Gmail API service instance.
    user_id: User's email address. The special value "me"
    can be used to indicate the authenticated user.
    msg_id: The ID of the Message required.

  Returns:
    A MIME Message, consisting of data from Message.
  """
  try:
    message = service.users().messages().get(userId=user_id, id=msg_id,
                                             format='raw').execute()

    print ('Message snippet: %s' % message['snippet'])

    msg_str = base64.urlsafe_b64decode(message['raw'].encode('ASCII'))

    mime_msg = email.message_from_string(msg_str)

    return mime_msg
  except error:
    print ('An error occurred: %s' % error)

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

def analyze():
    # filtered_emails = EmailItem.objects.filter(from_email=search_email)
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
            print(e, 'calculation_error')
            pdb.set_trace()

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
    # mail = imaplib.IMAP4_SSL('imap.gmail.com')
    # context = { 'status': True, 'msg': 'Get emails successfully' }
    # # try:
    # mail.login(user_email, password)

    # mail.list() # Lists all labels in GMail
    # mail.select('inbox') # Connected to inbox.

    # result, data = mail.search(None, 'FROM', search_email)
    # # search and return uids instead
    # i = len(data[0].split()) # data[0] is a space separate string

    # # get emails
    # for x in range(10):
    #     raw_email_string = None
    #     latest_email_uid = data[0].split()[x] # unique ids wrt label selected
    #     result, email_data = mail.uid('fetch', latest_email_uid, '(RFC822)')
    #     # fetch the email body (RFC822) for the given ID
    #     if email_data is None or email_data[0] is None:
    #         continue

    #     print('== new stage == \n')
    #     raw_email_string = email_data[0][1]
    #     # converts byte literal to string removing b''
    #     email_message = email.message_from_string(raw_email_string.decode('utf-8'))

    #     # this will loop through all the available multiparts in mail
    #     email_content = ""
    #     for part in email_message.walk():
    #         print('type: ', part.get_content_type())
    #         if part.get_content_type() == 'text/plain': # ignore attachments/html
    #             body = part.get_payload(decode=True)
    #             email_content = email_content + str(body)
    #         else:
    #             continue
        
    #     # parse attributes and save email into db
    #     date_obj = email_message['Date']
    #     dt = parser.parse(date_obj)
    #     from_val = email_message['From']
    #     from_username=from_val.split('<')[0].strip()
    #     try:
    #         from_email = from_val.split('<')[1].strip().replace('>', '')
    #     except:
    #         from_email = from_val

    #     # uni_words, bi_words, tri_words = get_top_ngrams(email_content)
    #     try:
    #         obj, created = EmailItem.objects.get_or_create(
    #                                 from_username=from_username,
    #                                 from_email=from_email,
    #                                 to_email=email_message['Delivered-To'],
    #                                 subject=email_message['Subject'],
    #                                 preview_text=email_message['snippet'],
    #                                 body_text= str(email_content),
    #                                 day_of_week= dt.weekday(),
    #                                 time_of_day=dt.time(),
    #                                 subject_word_count = get_word_count(email_message['Subject']),
    #                                 preview_word_count = get_word_count(email_message['snippet']),
    #                                 body_word_count = get_word_count(email_content),
    #                                 date_sent=dt.date())
    #     except Exception as e:
    #         print('Error get email: ', e)
    #         raise Exception(e)
    #     if created == False:
    #         break
    
    # Analyze emails
    # filtered_emails = EmailItem.objects.filter(from_email=search_email)
    report_item = analyze()
    print(report_item)
    report_context = {
        'sender': report_item['from_username'],
        'from_email': report_item['from_email'],
        'to_email': report_item['to_email'],
    }

    send_email(report_item)

    return {}
    # except Exception as e:
    #     context['status'] = False
    #     print(e)
    #     # context['msg'] = e.message 

    return context

@login_required
def dashboard(request):
    reports = Report.objects.all()

    from_address = 'newdavid5836@gmail.com'
    password = 'welcome8536'
    # get_emails_with_imap(from_address, password)


    return render(request, 'dashboard.html', { 'reports': reports })


@login_required
def get_emails_by_from(request):
    # from_address = request.POST.get('from', None)
    # password = request.POST.get('password', None)
    from_address = 'newdavid5836@gmail.com'
    password = 'welcome8536'
    res = { 'status': True }

    task_id = make_report.delay(from_address, password)
    # obj, created = Event.objects.get_or_create(name='save emails to db',
    #                                             uuid=task_id)

    # if res['status'] == False:
    #     return JsonResponse(res)

    # filterd_emails = EmailItem.objects.filter(from_email=from_address)
    # res['emails'] = list(filterd_emails)

    return JsonResponse(res)

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

    if not email:
        error_context['error'] = { 'msg': "Email field is required!" }
        return Response(error_context,
                        status=status.HTTP_400_BAD_REQUEST,
                        content_type="application/json")

    if not password:
        error_context['error'] = { 'msg': "Password field is required!" }
        return Response(error_context,
                        status=status.HTTP_400_BAD_REQUEST,
                        content_type="application/json")

    task_id = make_report.delay(email, password)

    return JsonResponse({ 'status': True })