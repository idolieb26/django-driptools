# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import pickle
import os.path
from dateutil import parser
import email
import base64
import json

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

    print 'Message snippet: %s' % message['snippet']

    msg_str = base64.urlsafe_b64decode(message['raw'].encode('ASCII'))

    mime_msg = email.message_from_string(msg_str)

    return mime_msg
  except error:
    print 'An error occurred: %s' % error

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
                pdb.set_trace()
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


def dashboard(request):
    emails = get_emails(100)

    return JsonResponse({ 'status': emails })