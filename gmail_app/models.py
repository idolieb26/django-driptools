# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
import uuid

DAY_STATUS =(
    (0, 'Mon'),
    (1, 'Tue'),
    (2, 'Wed'),
    (3, 'Thu'),
    (4, 'Fri'),
    (5, 'Sat'),
    (6, 'Sun'),
)


# Create your models here.
class EmailItem(models.Model):
    from_username = models.CharField(max_length=255, default="", blank=True, null=True)
    from_email = models.CharField(max_length=128, default="", blank=True, null=True)
    to_email = models.CharField(max_length=128, default="", blank=True, null=True)
    subject = models.CharField(max_length=255, default="", blank=True, null=True)
    preview_text = models.TextField(default="", blank=True, null=True)
    body_text = models.TextField(default="", blank=True, null=True)
    day_of_week = models.IntegerField(choices=DAY_STATUS, default=0)
    time_of_day = models.TimeField(blank=True, null=True)
    image_count = models.IntegerField(blank=True, null=True)
    subject_word_count = models.IntegerField(blank=True, null=True)
    preview_word_count = models.IntegerField(blank=True, null=True)
    body_word_count = models.IntegerField(blank=True, null=True)
    date_sent = models.DateField(default="", blank=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True, null=True)


class Event(models.Model):
    name = models.CharField(max_length=255, default="", blank=True, null=True)
    event_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    status = models.BooleanField(default=False, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True, null=True)
