from __future__ import unicode_literals
#-*- coding: utf-8 -*-

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
from .tasks import add, make_report, make_report_for_gmail
from utils.utils import get_top_ngrams, get_word_count, validate_username
from utils.send_email import send_email

import imaplib
import oauth2
import string
import nltk
from nltk import bigrams, trigrams, ngrams, word_tokenize, FreqDist

import pdb

DAYS =(
    'Mon',
    'Tue',
    'Wed',
    'Thu',
    'Fri',
    'Sat',
    'Sun',
)


# Create your views here.
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://mail.google.com/'
]

def get_emails(search_email, count):
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    # if os.path.exists('token.pickle'):
    #     with open('token.pickle', 'rb') as token:
    #         creds = pickle.load(token)
    # # If there are no (valid) credentials available, let the user log in.
    # if not creds or not creds.valid:
    #     if creds and creds.expired and creds.refresh_token:
    #         creds.refresh(Request())
    #     else:
    #         flow = InstalledAppFlow.from_client_secrets_file(
    #             BASE_DIR + '/credentials.json', SCOPES)
    #         creds = flow.run_local_server(port=0)
    #     # Save the credentials for the next run
    #     with open(BASE_DIR + '/token.pickle', 'wb') as token:
    #         pickle.dump(creds, token)

    flow = InstalledAppFlow.from_client_secrets_file(
        BASE_DIR + '/credentials.json', SCOPES)
    creds = flow.run_local_server(port=0)
    service = build('gmail', 'v1', credentials=creds)
    
    # Call the Gmail API to fetch INBOX
    results = service.users().messages().list(userId='me', 
                                            labelIds = ['INBOX'],
                                            q=search_email).execute()
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

                email_message = email.message_from_string(msg_str.decode())
                for parts in email_message.walk():
                      if parts.get_content_type() == 'text/plain':
                        parsed_msg = parts.get_payload(decode=True)
                        try:
                            message_body = message_body + parsed_msg.decode()
                        except:
                            message_body = message_body

            except Exception as e:
                print('Error when parsing: ', e)
                message_body = ""

            try:
                obj, created = EmailItem.objects.get_or_create(
                                        from_username=from_username,
                                        from_email=from_email,
                                        to_email=email_message['Delivered-To'],
                                        subject=email_message['Subject'],
                                        preview_text=email_message['snippet'],
                                        body_text= message_body,
                                        day_of_week= dt.weekday(),
                                        time_of_day=dt.time(),
                                        subject_word_count = get_word_count(email_message['Subject']),
                                        preview_word_count = get_word_count(email_message['snippet']),
                                        body_word_count = get_word_count(message_body),
                                        date_sent=dt.date())
            except Exception as e:
                print('Error get email: ', e)
                raise Exception(e)


    return True


def get_token():
    flow = InstalledAppFlow.from_client_secrets_file(
        BASE_DIR + '/credentials.json', SCOPES)
    creds = flow.run_local_server(port=0)
    token = creds.token
    return token

def xoauth_authenticate(email, access_token):
    def _auth(*args, **kwargs):
        return 'user=%s\1auth=Bearer %s\1\1' % (email, access_token)
    return 'XOAUTH2', _auth

def GenerateOAuth2String(username, access_token, base64_encode=True):
  """Generates an IMAP OAuth2 authentication string.

  See https://developers.google.com/google-apps/gmail/oauth2_overview

  Args:
    username: the username (email address) of the account to authenticate
    access_token: An OAuth2 access token.
    base64_encode: Whether to base64-encode the output.

  Returns:
    The SASL argument for the OAuth2 mechanism.
  """
  auth_string = 'user=%s\1auth=Bearer %s\1\1' % (username, access_token)
  if base64_encode:
    auth_string = base64.b64encode(auth_string)
  return auth_string

@login_required
def dashboard(request):
    # get_emails('newsdigest@insideapple.apple.com', 20)
    return render(request, 'dashboard.html')

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

    # if not email:
    #     error_context['error'] = { 'msg': "Email field is required!" }
    #     return JsonResponse(error_context, status=400)

    #  For gmail services
    flow = InstalledAppFlow.from_client_secrets_file(
        BASE_DIR + '/credentials.json', SCOPES)
    creds = flow.run_local_server(host='localhost',
                                port=0,
                                authorization_prompt_message='Please visit this URL: {url}', 
                                success_message='The auth flow is complete; you may close this window.',
                                open_browser=True)

    service = build('gmail', 'v1', credentials=creds)

    make_report_for_gmail(from_email, request.user.email, service)


    ## For other email services
    # try:
    #     # auth_string = GenerateOAuth2String(email, token, base64_encode=False)
    #     # mail.authenticate(*xoauth_authenticate(email, token))
    #     # mail.authenticate('XOAUTH2', lambda x: auth_string)

    # except Exception as e:
    #     print(e)
    #     error_context['error'] = { 'msg': "Please check your email or password to search!" }
    #     return JsonResponse(error_context, status=400)

    # task_id = make_report.delay(email, password, from_email, 'collinvargo530@gmail.com', mail)

    return JsonResponse({ 'status': True })