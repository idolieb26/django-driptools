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
from utils.utils import get_top_ngrams, get_word_count, validate_username
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

    task_id = make_report.delay(email, password, from_email, 'collinvargo530@gmail.com')
    # task_id = make_report.delay(email, password, from_email, request.user.email)

    return JsonResponse({ 'status': True })