# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf.urls import url, include
from django.conf import settings
from base import views


urlpatterns = [
    url(r'^signup/', views.auth_signup, name="auth_signup"),
    url(r'^login/', views.auth_login, name="auth_login"),
]
