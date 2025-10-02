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



#### Document Upload/Update View ###
@login_required
def upload_document(request):
    if request.method == "POST":
        doc_id = request.POST.get("doc_id")
        section = request.POST.get("section")
        doc_type = request.POST.get("doc_type")
        description = request.POST.get("description")
        file = request.FILES.get("file")

        if doc_id:  # update
            doc = get_object_or_404(Document, pk=doc_id, uploaded_by=request.user)
            doc.section = section
            doc.doc_type = doc_type
            doc.description = description
            if file:
                doc.file = file
            doc.save()
            messages.success(request, f"Document '{doc.doc_type}' updated successfully.")
        else:  # new upload
            if file:
                Document.objects.create(
                    section=section,
                    doc_type=doc_type,
                    description=description,
                    file=file,
                    uploaded_by=request.user,
                    status="pending"
                )
                messages.success(request, "Document uploaded successfully and is pending review.")
            else:
                messages.error(request, "Please select a file to upload.")

        return redirect("review_document")

    return redirect("review_document")

@login_required
def delete_document(request, doc_id):
    doc = get_object_or_404(Document, pk=doc_id, uploaded_by=request.user)
    doc_name = doc.doc_type

    doc.delete()
    messages.success(request, f"Document '{doc_name}' deleted successfully.")
    return redirect("review_document")

#### Document Review View ###
# @login_required
# def review_document(request):
#     user = request.user

#     if user.groups.filter(name="reviewer").exists():
#         # reviewers see all files, grouped by user
#         documents = Document.objects.select_related("uploaded_by").all()
#         role = "reviewer"

#     elif user.groups.filter(name="staff").exists():
#         # staff only see their own files
#         documents = Document.objects.filter(uploaded_by=user)
#         role = "staff"

#         # 🔔 alert staff if any of their docs have been reviewed
#         reviewed = documents.exclude(status="pending").exists()
#         if reviewed:
#             messages.info(
#                 request,
#                 "You have reviewed files. Please check their status!"
#             )

#     else:
#         documents = Document.objects.none()
#         role = "none"

#     return render(
#         request,
#         "training_docs/review.html",
#         {"documents": documents, "role": role},
#     )
@login_required
def review_document(request):
    user = request.user
    documents = Document.objects.none()
    roles = []

    if user.groups.filter(name="reviewer").exists():
        documents = documents | Document.objects.select_related("uploaded_by").all()
        roles.append("reviewer")

    if user.groups.filter(name="staff").exists():
        staff_docs = Document.objects.filter(uploaded_by=user)
        documents = documents | staff_docs
        roles.append("staff")

        # Notify staff if any of their docs have been reviewed
        if staff_docs.exclude(status="pending").exists():
            messages.info(
                request,
                "You have reviewed files. Please check their status!"
            )

    if not roles:
        roles.append("none")

    return render(
        request,
        "training_docs/review.html",
        {"documents": documents.distinct(), "roles": roles},
    )


@login_required
def review_document_submit(request, pk):
    doc = get_object_or_404(Document, pk=pk)

    if request.method == "POST":
        verdict = request.POST.get("status")
        feedback = request.POST.get("reviewer_feedback")

        # Default safeguard
        if verdict not in dict(Document.STATUS_CHOICES).keys():
            messages.error(request, "Invalid status.")
            return redirect("review_document")

        # Update
        doc.status = verdict
        doc.reviewer_feedback = feedback or ""
        doc.save()

        # Feedback for reviewer
        if verdict == "approved":
            messages.success(request, f"Congratulations '{doc.doc_type}' approved.")
        elif verdict == "rejected":
            messages.error(request, f"Oops '{doc.doc_type}' rejected.")
        elif verdict == "expired":
            messages.warning(request, f"⚠️ Warning '{doc.doc_type}' marked expired.")
        elif verdict == "invalid":
            messages.warning(request, f"⚠️ Warning '{doc.doc_type}' marked invalid.")
        else:
            messages.info(request, f"⌛ '{doc.doc_type}' is pending review.")

        return redirect("review_document")

    messages.error(request, "Invalid request.")
    return redirect("review_document")







