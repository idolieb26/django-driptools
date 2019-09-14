# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.contrib.auth.models import AbstractUser


# Create your models here.
class BaseUser(AbstractUser):
    ''' Custom user model used to store extra fields '''
    def __str__(self):
        return self.username

    def get_short_name(self):
        return "{}".format(self.first_name if self.first_name else self.username)

    def get_full_name(self):
        if self.first_name and self.last_name:
            return "{} {}".format(self.first_name, self.last_name)
        return self.username
