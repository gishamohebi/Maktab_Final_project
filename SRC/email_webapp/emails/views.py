from django.http import HttpResponse, HttpResponseRedirect
from django.utils.encoding import uri_to_iri
from django.views import View
from django.views.generic import ListView, DetailView, FormView
from django.template import loader
from django.shortcuts import render
from datetime import datetime

import logging


# Create your views here.

