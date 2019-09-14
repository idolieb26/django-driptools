# GlassFrogg/forms.py

from django import forms
from django.forms import ModelForm
from django.contrib.auth import authenticate
from base.models import BaseUser


class BaseSignupForm(ModelForm):
    password = forms.CharField(widget=forms.TextInput(attrs={"type": "password"}), required=True)
    confirm_password = forms.CharField(widget=forms.TextInput(attrs={"type": "password"}), required=True)

    class Meta:
        model = BaseUser
        fields = ['username', 'email', 'first_name', 'last_name', 'password',]

    def clean_username(self):
        username = self.cleaned_data['username']
        if BaseUser.objects.exclude(pk=self.instance.pk).filter(username=username).exists():
            raise forms.ValidationError(u'Username "%s" is already in use.' % username)
        return username

    def clean_email(self):
        email = self.cleaned_data['email']
        if BaseUser.objects.exclude(pk=self.instance.pk).filter(email=email).exists():
            raise forms.ValidationError(u'Email "%s" is already in use.' % email)
        return email

    def clean(self):
        password = self.cleaned_data['password']
        confirm_password = self.cleaned_data['confirm_password']
        required_fields = ['first_name', 'last_name']

        for field in required_fields:
            if not self.cleaned_data.get(field):
                self.add_error(field, u'"%s" shouldn\'t be empty' % field)

        if len(password) < 8:
            self.add_error('password', u'Password should be 8 characters.')

        if password != confirm_password:
            self.add_error('confirm_password', u'Password is not matched.')

    def save(self, password=None):
        instance = super(BaseSignupForm, self).save()
        if password:
            instance.set_password(password)
        instance.username = instance.email
        instance.save()

        return instance


class BaseLoginForm(forms.Form):
    email = forms.EmailField(required=True)
    password = forms.CharField(widget=forms.TextInput(attrs={"type": "password"}), required=True)

    def clean(self):
        password = self.cleaned_data['password']

        if len(password) < 8:
            self.add_error('password', u'Password should be 8 characters.')
