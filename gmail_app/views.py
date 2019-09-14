# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import pickle
import os.path
from django.shortcuts import render
from django.http.response import JsonResponse

from httplib2 import Http
from googleapiclient.discovery import build
from oauth2client import file, client, tools
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

from driptools.settings import BASE_DIR

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
    results = service.users().messages().list(userId='me',labelIds = ['INBOX']).execute()
    messages = results.get('messages', [])
    import pdb

    if not messages:
        print "No messages found."
    else:
        print "Message snippets:"
        for message in messages[:count]:
            msg = service.users().messages().get(userId='me', id=message['id']).execute()
            pdb.set_trace()
            print msg['snippet']

    return True


def dashboard(request):
    emails = get_emails(1)

    return JsonResponse({ 'status': emails })