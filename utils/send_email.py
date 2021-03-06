import sys
import os
from os import path
import django
import json

from django.utils import timezone
from django.utils.timezone import datetime
from django.http import JsonResponse
from django.core.mail import send_mail, EmailMultiAlternatives
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags

def send_email(report, recipient_list):
    subject = 'Report for analyzing gmail'

    #email_from = settings.EMAIL_HOST_USER
    email_from = settings.EMAIL_HOST_USER

    subject_top_3 = json.loads(report.subject_top_3)
    preview_top_3 = json.loads(report.preview_top_3)
    body_top_3 = json.loads(report.body_top_3)
    html_content = render_to_string('report_email_template.html', {
            'item': report,
            'subject_top_3': subject_top_3,
            'preview_top_3': preview_top_3,
            'body_top_3': body_top_3})

    text_content = strip_tags(html_content) # Strip the html tag. So people can see the pure text at least.
    ### create the email, and attach the HTML version as well.
    msg = EmailMultiAlternatives(subject, text_content, email_from, recipient_list)
    msg.attach_alternative(html_content, "text/html")
    msg.send()

    print ("Email Sent!", recipient_list)

def send_email_with_template(template_name, context, subject, recipient_list):
    email_from = settings.EMAIL_HOST_USER

    html_content = render_to_string(template_name, context)
    text_content = strip_tags(html_content) # Strip the html tag. So people can see the pure text at least.

    ### create the email, and attach the HTML version as well.
    msg = EmailMultiAlternatives(subject, text_content, email_from, recipient_list)
    msg.attach_alternative(html_content, "text/html")
    msg.send()
