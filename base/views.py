# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging
logger = logging.getLogger(__name__)

from django.shortcuts import render, redirect
from django.conf import settings
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import authenticate, login
from .forms import BaseLoginForm, BaseSignupForm
from .models import BaseUser

# Create your views here.
def auth_login (request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        context = dict()
        login_form = BaseLoginForm(request.POST)
        context['form'] = login_form

        if login_form.is_valid():
            try:
                user = BaseUser.objects.get(email=email)
            except:
                context['error'] = 'User doesn\'t exists with given email!'
                return render(request, 'login.html', context)

            user = authenticate(username=email, password=password)
            context['error'] = 'Password is wrong!'

            if user is not None:
                login(request, user)
                return redirect('/gmail/dashboard')

        return render(request, 'login.html', context)

    login_form = BaseLoginForm()
    return render(request, 'login.html', {'form': login_form})

def auth_signup (request):
    context = dict()
    if request.method == 'POST':
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

        signup_form = BaseSignupForm(request.POST)
        context['form'] = signup_form
        if signup_form.is_valid():
            model_instance = signup_form.save(password)

            return redirect('auth_login')

        return render(request, 'signup.html', context)

    signup_form = BaseSignupForm()
    return render(request, 'signup.html', {'form': signup_form})
