# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import pickle
import os.path
from dateutil import parser

from httplib2 import Http
from googleapiclient.discovery import build
from oauth2client import file, client, tools
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

from django.shortcuts import render
from django.http.response import JsonResponse

from driptools.settings import BASE_DIR
from .models import EmailItem
import pdb

# Create your views here.
SCOPES = 'https://www.googleapis.com/auth/gmail.readonly'


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
        print "No messages found."
    else:
        print "Message snippets:"
        for message in messages[:count]:
            msg = service.users().messages().get(userId='me', id=message['id'], format='raw').execute()
            pdb.set_trace()
            date_obj = msg['payload']['headers']['Date']
            dt = parser.parse(date_obj)
            from_val =  msg['payload']['headers']['From']
            from_email = from_val.split('<')[1].strip().replae('>', '')
            if from_email == 'room_11338055278317226023464745705696@upwork.com':
                pdb.set_trace()
            # email_item = EmailItem(from_username=from_val.split('<')[0].strip(),
            #                         from_email=from_val.split('<')[1].strip().replae('>', ''),
            #                         to_email=msg['payload']['headers']['Delivered-To'],
            #                         subject=msg['payload']['headers']['Subject'],
            #                         preview_text=msg['payload']['headers']['snippet'],
            #                         body_text= '',
            #                         day_of_week= dt.weekday,
            #                         time_of_day=dt.time,
            #                         date_sent=dt.date)
            # email_item.save()

            # print(msg['snippet'], "\n")

    return True


def dashboard(request):
    emails = get_emails(1000)

    return JsonResponse({ 'status': emails })