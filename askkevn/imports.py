from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.sessions.backends.db import SessionStore
from django.contrib.sessions.models import Session
from .forms import RegistrationForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.http import JsonResponse
from django.urls import reverse
from .forms import InventoryUploadForm
from .models import InventoryItem, determine_expertise, UploadedFile
from django.db.models import Q
from django.core.cache import cache
from .prompts import get_prompt
import pandas as pd
import openpyxl
import shutil
import json
import openai
import os
import string
import logging
from dotenv import load_dotenv
from django.views.generic import TemplateView
from django.http import HttpResponseForbidden
from django.contrib.auth.models import Permission, ContentType
from django.contrib.auth.decorators import permission_required
from django.template.response import TemplateResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import user_passes_test
from django.core.cache import cache

BASE_DIR = settings.BASE_DIR

load_dotenv()

api_key = os.getenv("OPENAI_KEY", None)

logger = logging.getLogger(__name__)