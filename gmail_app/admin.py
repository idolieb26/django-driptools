# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin
from .models import EmailItem, Report

# Register your models here.
@admin.register(EmailItem)
class EmailItemAdmin(admin.ModelAdmin):

    list_display = ("from_username",
                    "from_email",
                    "to_email",
                    "subject_word_count",
                    "preview_word_count",
                    "body_word_count",
                    "subject",
                    "preview_text",
                    "created",)


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):

    list_display = ("from_username",
                    "from_email",
                    "to_email",
                    "first_date",
                    "total",
                    "created",)