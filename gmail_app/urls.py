# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf.urls import url, include
from django.conf import settings
from gmail_app import views


urlpatterns = [
    url(r'^dashboard/', views.dashboard, name="gmail_dashboard"),
    url(r'^report/(?P<id>[\d]+)/', views.get_detail_report, name="get_detail_report"),
    url(r'^create_report/', views.create_report, name="create_report"),
]
