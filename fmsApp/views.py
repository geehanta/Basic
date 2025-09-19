##### LIBRARY IMPORTS #######
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.utils import timezone
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from fms_django.settings import MEDIA_ROOT, MEDIA_URL

import json
import base64
from cryptography.fernet import Fernet

from .models import Document
from .forms import DocumentUploadForm, DocumentReviewForm, UserRegistration, UpdateProfile, UpdatePasswords


######### VIEW FUNCTIONS FOR ACCESS, AUTHENTICATION, AND PROFILE ###########

def login_user(request):
    logout(request)
    resp = {"status": 'failed', 'msg': ''}
    username = ''
    password = ''
    next_url = request.GET.get('next', '')  # Get the 'next' parameter from the URL

    if request.POST:
        username = request.POST['username']
        password = request.POST['password']

        user = authenticate(username=username, password=password)
        if user is not None and user.is_active:
            login(request, user)
            resp['status'] = 'success'
            # Redirect to the 'next' URL if it exists, otherwise redirect to studies_dashboard
            resp['redirect'] = next_url if next_url else '/studies-dashboard/'
        else:
            resp['msg'] = "Incorrect username or password"

    return HttpResponse(json.dumps(resp), content_type='application/json')


def logoutuser(request):
    logout(request)
    return redirect('/login')


def home(request):
    context = {"page_title": "Home"}
    return render(request, 'partials/landing.html', context)


def registerUser(request):
    if request.user.is_authenticated:
        return redirect('home')

    context = {"page_title": "Register User"}
    if request.method == 'POST':
        form = UserRegistration(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            pwd = form.cleaned_data.get('password1')
            loginUser = authenticate(username=username, password=pwd)
            login(request, loginUser)
            return redirect('home')
        else:
            context['reg_form'] = form
    else:
        context['reg_form'] = UserRegistration()

    return render(request, 'user_auth/register.html', context)


@login_required
def profile(request):
    context = {"page_title": "Profile"}
    return render(request, 'user_auth/profile.html', context)


@login_required
@user_passes_test(lambda u: u.groups.filter(name='staff').exists())
def update_profile(request):
    user = User.objects.get(id=request.user.id)
    context = {"page_title": "Update Profile"}

    if request.method == 'POST':
        form = UpdateProfile(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile has been updated")
            return redirect("profile")
        else:
            context['form'] = form
    else:
        form = UpdateProfile(instance=user)
        context['form'] = form

    return render(request, 'user_auth/manage_profile.html', context)


@login_required
@user_passes_test(lambda u: u.groups.filter(name='staff').exists())
def update_password(request):
    context = {"page_title": "Update Password"}
    if request.method == 'POST':
        form = UpdatePasswords(user=request.user, data=request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Your Account Password has been updated successfully")
            update_session_auth_hash(request, form.user)
            return redirect("profile")
        else:
            context['form'] = form
    else:
        form = UpdatePasswords(user=request.user)
        context['form'] = form

    return render(request, 'user_auth/update_password.html', context)


######### PAGES THAT REQUIRE LOGIN ###########

@login_required
def studies_dashboard(request):
    context = {"page_title": "BSL"}
    return render(request, 'commons/studies_dashboard.html', context)


@login_required
def dashboard(request):
    documents = Document.objects.all().order_by("-uploaded_at")

    if request.method == "POST" and "upload" in request.POST:
        form = DocumentUploadForm(request.POST, request.FILES)
        if form.is_valid():
            doc = form.save(commit=False)
            doc.uploaded_by = request.user
            doc.save()
            messages.success(request, "Document uploaded successfully and pending review.")
            return redirect("dashboard")
    else:
        form = DocumentUploadForm()

    return render(request, "dashboard.html", {
        "form": form,
        "documents": documents,
    })


@login_required
def review_document(request):
    user = request.user

    if user.groups.filter(name="reviewer").exists():
        documents = Document.objects.all()
        role = "reviewer"
    elif user.groups.filter(name="staff").exists():
        documents = Document.objects.filter(uploaded_by=user)
        role = "staff"
    else:
        documents = Document.objects.none()
        role = "none"

    return render(request, "training_docs/review_document.html", {
        "documents": documents,
        "role": role,
    })
@login_required
@user_passes_test(lambda u: u.groups.filter(name="staff").exists())
def update_document(request, doc_id):
    doc = get_object_or_404(Document, id=doc_id, uploaded_by=request.user)

    if request.method == "POST":
        form = DocumentUploadForm(request.POST, request.FILES, instance=doc)
        if form.is_valid():
            form.save()
            messages.success(request, "Document updated successfully.")
            return redirect("review_document")
    else:
        form = DocumentUploadForm(instance=doc)

    return render(request, "training_docs/update_document.html", {
        "form": form,
        "doc": doc,
    })


@login_required
@user_passes_test(lambda u: u.groups.filter(name="staff").exists())
def delete_document(request, doc_id):
    doc = get_object_or_404(Document, id=doc_id, uploaded_by=request.user)
    if request.method == "POST":
        doc.delete()
        messages.success(request, "Document deleted successfully.")
        return redirect("review_document")

    return render(request, "training_docs/confirm_delete.html", {
        "doc": doc,
    })








