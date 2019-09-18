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

import imaplib
import email

# imaplib module implements connection based on IMAPv4 protocol
mail = imaplib.IMAP4_SSL('imap.gmail.com')

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



def get_emails_with_imap(user_email, password):
    context = { 'status': True, 'msg': 'Get emails successfully' }
    try:
        mail.login(user_email, password)

        mail.list() # Lists all labels in GMail
        mail.select('inbox') # Connected to inbox.

        result, data = mail.search(None, 'FROM', 'upwork@e.upwork.com')
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

            print(obj, created)
    except Exception as e:
        context['status'] = False
        context['msg'] = e.message 

    return context


def dashboard(request):
    emails = []
    # emails = get_emails(100)
    all_emails = EmailItem.objects.all()
    for email in all_emails:
        emails.append({
            'from_username': email.from_username,
            'from_email': email.from_email,
            'to_email': email.to_email,
            'subject': email.subject,
            'preview_text': email.preview_text,
            'body_text': email.body_text,
            'day_of_week': email.day_of_week,
            'time_of_day': email.time_of_day,
            'date_sent': email.date_sent
        })

    return JsonResponse({ 'status': True, 'emails': emails })


def get_emails_by_from(request):
    # from_address = request.POST.get('from', None)
    # password = request.POST.get('password', None)
    from_address = 'newdavid5836@gmail.com'
    password = 'welcome8536'
    res = get_emails_with_imap(from_address, password)

    if res['status'] == False:
        return JsonResponse(res)

    filterd_emails = EmailItem.objects.filter(from_email=from_address)
    res['emails'] = list(filterd_emails)

    return JsonResponse(res)