##### LIBRARY IMPORTS #######
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.utils import timezone
from django.contrib import messages
from django.urls import reverse
from django.http import HttpResponse, JsonResponse
from fms_django.settings import MEDIA_ROOT, MEDIA_URL
from .models import UserProfile

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
            #  Ensure user has a profile immediately upon login
            UserProfile.objects.get_or_create(user=user)

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
    # Ensure profile exists (safety check)
    profile, created = UserProfile.objects.get_or_create(user=request.user)

    context = {
        "page_title": "Profile",
        "profile": profile
    }
    return render(request, 'user_auth/profile.html', context)

@login_required
@user_passes_test(lambda u: u.groups.filter(name__in=['staff', 'reviewer']).exists())
def update_profile(request):
    user = request.user  # current logged-in user
    # Ensure user has a profile (created automatically by signal, but this is safe)
    profile, created = UserProfile.objects.get_or_create(user=user)

    context = {
        "page_title": "Update Profile",
        "profile": profile  # so template can access {{ profile.profile_image.url }}
    }

    if request.method == 'POST':
        # Include request.FILES to process uploaded images
        form = UpdateProfile(request.POST, request.FILES, instance=user)

        if form.is_valid():
            form.save()  # form handles both User and UserProfile
            messages.success(request, " Your profile has been updated successfully.")
            return redirect("profile")
        else:
            messages.error(request, " Please correct the errors below.")
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
        files = request.FILES.getlist("file")  # multiple files allowed

        # Validation
        if not section or not doc_type:
            messages.error(request, "Please select a section and document type.")
            return redirect("review_document")

        # Redirect user back to same section tab
        redirect_url = f"{reverse('review_document')}#{section}"

        # --- UPDATE MODE (editing existing one) ---
        if doc_id:
            doc = get_object_or_404(Document, pk=doc_id, uploaded_by=request.user)
            doc.section = section
            doc.doc_type = doc_type
            doc.description = description
            if files:
                doc.file = files[0]  # update file if a new one is provided
            doc.save()
            messages.success(request, f" '{doc.doc_type}' Update successful!.")
            return redirect(redirect_url)

        # --- CREATE NEW DOCUMENT(S) ---
        if files:
            new_docs = []
            for f in files:
                new_docs.append(
                    Document(
                        section=section,
                        doc_type=doc_type,
                        description=description,
                        file=f,
                        uploaded_by=request.user,
                        status="pending",
                    )
                )
            Document.objects.bulk_create(new_docs)
            messages.success(
                request,
                f" {len(files)} new document(s) uploaded under '{doc_type}' — pending review.",
            )
        else:
            messages.error(request, "Please select at least one file to upload.")

        return redirect(redirect_url)

    # Non-POST fallback
    return redirect("review_document")



@login_required
def delete_document(request, doc_id):
    doc = get_object_or_404(Document, pk=doc_id, uploaded_by=request.user)
    doc_name = doc.doc_type

    doc.delete()
    messages.success(request, f"Document '{doc_name}' deleted successfully.")
    return redirect("review_document")

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

        if staff_docs.exclude(status="pending").exists():
            messages.info(request, "You have reviewed files. Please check their status!")

    if not roles:
        roles.append("none")

    # Group documents by section for easy rendering
    section_docs = {
        "section1": documents.filter(section="section1"),
        "section2": documents.filter(section="section2"),
        "section3": documents.filter(section="section3"),
    }

    # --- Compute badge counts for each document type ---
    doc_counts = {}
    for section, docs in section_docs.items():
        doc_counts[section] = {}
        for doc in docs:
            doc_counts[section][doc.doc_type] = doc_counts[section].get(doc.doc_type, 0) + 1

    # --- Section document definitions ---
    section_items = {
        "section1": [
            {"num": 1, "name": "Privacy Act Statement", "tooltip": "Required document for upload"},
            {"num": 2, "name": "Curriculum Vitae (CV)", "tooltip": "Required document for upload"},
            {"num": 3, "name": "Job Description", "tooltip": "Required document for upload"},
            {"num": 4, "name": "Additional Duty Appointment Orders", "tooltip": "Optional supporting document"},
            {"num": 5, "name": "CLIP Testing Qualification Form", "tooltip": "Optional supporting document"},
            {"num": 6, "name": "College or Technical School Diploma", "tooltip": "Required education proof"},
            {"num": 7, "name": "Registration or Board Certification", "tooltip": "Required professional proof"},
            {"num": 8, "name": "Other Personnel Documentation", "tooltip": "Optional document"},
        ],
        "section2": [
            {"num": 1, "name": "Statement of Department Mission", "tooltip": "Required orientation document"},
            {"num": 2, "name": "Orientation Checklist", "tooltip": "Required document for upload"},
            {"num": 3, "name": "Initial SOP Training Checklist", "tooltip": "Required training checklist"},
            {"num": 4, "name": "Initial Competency Testing Results", "tooltip": "Required testing document"},
            {"num": 5, "name": "Other Orientation Docs", "tooltip": "Required supporting document"},
        ],
        "section3": [
            {
                "num": 1,
                "name": "Short Course Documentation",
                "tooltip": "Required training proof",
                "categories": {
                    "CITI Category": [
                        {"name": "Human Research", "tooltip": "Required CITI training document"},
                        {"name": "Safety / Biosafety", "tooltip": "Priority biosafety training"},
                    ],
                    "ICT Category": [
                        {"name": "JKO Cyberawareness", "tooltip": "Required cybersecurity document"},
                        {"name": "HIPAA", "tooltip": "Priority patient privacy training"},
                        {"name": "Anti-terrorism Training", "tooltip": "Optional awareness course"},
                    ],
                },
            },
            {"num": 2, "name": "Other Training Docs", "tooltip": "Optional training docs"},
            {"num": 3, "name": "Annual SOP Training Docs", "tooltip": "Priority training documentation"},
            {"num": 4, "name": "Weekly Training Docs", "tooltip": "Optional ongoing training docs"},
            {"num": 5, "name": "Routine Competency Records", "tooltip": "Priority competency records"},
            {"num": 6, "name": "Publications", "tooltip": "Optional publications"},
            {"num": 7, "name": "Vaccination records", "tooltip": "Optional internal training docs"},
        ],
    }

    # --- Inject counts into section_items (handles nested categories too) ---
    for section, items in section_items.items():
        for item in items:
            # Top-level item count
            item_name = item["name"]
            item["count"] = doc_counts.get(section, {}).get(item_name, 0)

            # If the item has categories, inject counts for subitems too
            if "categories" in item:
                for category, subitems in item["categories"].items():
                    for sub in subitems:
                        sub_name = sub["name"]
                        sub["count"] = doc_counts.get(section, {}).get(sub_name, 0)

    # --- Render Template ---
    return render(
        request,
        "training_docs/review.html",
        {
            "documents": documents.distinct(),
            "roles": roles,
            "section_docs": section_docs,
            "doc_counts": doc_counts,
            "section_items": section_items,
        },
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
            messages.info(request, f"⌛ '{doc.doc_type}'  pending review.")

        return redirect("review_document")

    messages.error(request, "Invalid request.")
    return redirect("review_document")







