#####LIBRARY IMPORTS #######
from django.shortcuts import render,redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.models import AnonymousUser
from django.contrib.auth.decorators import login_required, user_passes_test
from fms_django.settings import MEDIA_ROOT, MEDIA_URL
import json
from django.contrib.auth.models import Group
from django.utils import timezone
from django.contrib import messages
from django.contrib.auth.models import User
from django.http import HttpResponse, JsonResponse
from fmsApp.forms import UserRegistration, SavePost, UpdateProfile, UpdatePasswords, TrainingRecordStaffForm, TrainingRecordReviewerForm
from fmsApp.models import Post, TrainingRecord 
from cryptography.fernet import Fernet
from django.conf import settings
import base64

# Create your views here.
context = {
    'page_title' : 'BSL',
    'page_title' : 'BSL',
}

#########VIEW FUNCTIONS FOR  ACCESS, AUTHENTICATION  AND PROFILE PAGES ###########
########LOGIN###########
def login_user(request):
    logout(request)
    resp = {"status":'failed','msg':''}
    username = ''
    password = ''
    next_url = request.GET.get('next', '')  # Get the 'next' parameter from the URL

    if request.POST:
        username = request.POST['username']
        password = request.POST['password']

        user = authenticate(username=username, password=password)
        if user is not None:
            if user.is_active:
                login(request, user)
                resp['status']='success'
                # Redirect to the 'next' URL if it exists, otherwise redirect to the home page
                if next_url:
                    resp['redirect'] = next_url
                else:
                    resp['redirect'] = '/studies_dashboard' 
            else:
                resp['msg'] = "Incorrect username or password"
        else:
            resp['msg'] = "Incorrect username or password"
    return HttpResponse(json.dumps(resp),content_type='application/json')

#### LOGOUT ####
def logoutuser(request):
    logout(request)
    return redirect('/login')


def home(request):
    if isinstance(request.user, AnonymousUser):
        # Handle the case where the user is not authenticated
        context = {
            'page_title': 'Home',
            'posts': [],
            'postsLen': 0
        }
    else:
        context = {
            'page_title': 'Home',
            'posts': Post.objects.filter(user=request.user) if not request.user.is_superuser else Post.objects.all(),
            'postsLen': Post.objects.filter(user=request.user).count() if not request.user.is_superuser else Post.objects.count()
        }
    print(request.build_absolute_uri())
    return render(request, 'home.html', context)

def registerUser(request):
    user = request.user
    if user.is_authenticated:
        return redirect('home-page')
    context['page_title'] = "Register User"
    if request.method == 'POST':
        data = request.POST
        form = UserRegistration(data)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            pwd = form.cleaned_data.get('password1')
            loginUser = authenticate(username= username, password = pwd)
            login(request, loginUser)
            return redirect('home-page')
        else:
            context['reg_form'] = form

    return render(request,'register.html',context)

@login_required
def profile(request):
    context['page_title'] = 'Profile'
    return render(request, 'profile.html',context)
@login_required
@user_passes_test(lambda u: u.groups.filter(name='staff').exists())
def update_profile(request):
    context['page_title'] = 'Update Profile'
    user = User.objects.get(id = request.user.id)
    if not request.method == 'POST':
        form = UpdateProfile(instance=user)
        context['form'] = form
        print(form)
    else:
        form = UpdateProfile(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile has been updated")
            return redirect("profile")
        else:
            context['form'] = form
            
    return render(request, 'manage_profile.html',context)


@login_required
@user_passes_test(lambda u: u.groups.filter(name='staff').exists())
def update_password(request):
    context['page_title'] = "Update Password"
    if request.method == 'POST':
        form = UpdatePasswords(user = request.user, data= request.POST)
        if form.is_valid():
            form.save()
            messages.success(request,"Your Account Password has been updated successfully")
            update_session_auth_hash(request, form.user)
            return redirect("profile")
        else:
            context['form'] = form
    else:
        form = UpdatePasswords(request.POST)
        context['form'] = form
    return render(request,'update_password.html',context)

#########VIEW FUNCTIONS FOR PAGES THAT DONT REQUIRE LOGIN###########


def tools(request):
    return render(request,'tools.html',context)
def calendar(request):
    return render(request,'calendar.html',context)
def home(request):
    return render(request, 'home.html',context)


#########VIEW FUNCTIONS FOR PAGES THAT REQUIRE LOGIN###########

@login_required
def studies_dashboard(request):
    return render(request, 'studies_dashboard.html',context)
@login_required
def inventory(request):
    return render(request, 'inventory.html')
@login_required
def reports(request):
    return render(request, 'reports.html')
@login_required
def new_training(request):
    return render(request, 'training.html')

#######VIEW FUNCTIONS FOR TRAINING RECORDS###########
## STAFF ####
@login_required
def create_training_record(request):
    context = {
        'employee_id': request.user.id,
        'is_staff': request.user.groups.filter(name='staff').exists(),
        'today': timezone.now().date(),
    }

    if not context['is_staff']:
        messages.error(request, "You do not have permission to access this page.")
        context['status'] = 'error'
        return render(request, 'add_view_training_record.html', context)

    if request.method == 'POST':
        try:
            record = TrainingRecord.objects.create(
                employee=request.user,
                facility_assigned=request.POST.get('facility_assigned'),
                section_assigned=request.POST.get('section_assigned'),
                supervisor_name=request.POST.get('supervisor_name'),
                supervisor_date=request.POST.get('supervisor_date'),
                records_maintenance_personnel=request.POST.get('records_maintenance_personnel'),
                records_maintenance_date=request.POST.get('records_maintenance_date'),
                date_reviewed=timezone.now().date(),
                printed_name=request.user.get_full_name() or request.user.username,
                signature=request.POST.get('signature'),
                # QA fields remain blank or null for staff
            )
            messages.success(request, 'Training record saved successfully.')
            context['status'] = 'success'
        except Exception as e:
            print(f"Error saving record: {e}")
            messages.error(request, "There was an error saving the training record.")
            context['status'] = 'error'

    # Fetch existing records to show in the table
    context['posts'] = TrainingRecord.objects.filter(employee=request.user).order_by('-date_reviewed')
    return render(request, 'add_view_training_record.html', context)
###REVIEWER####



@login_required
def training_record_review(request, record_id):
    if not request.user.groups.filter(name='reviewer').exists():
        messages.error(request, "Access denied. Reviewer permission required.")
        return redirect('unauthorized')
    

    record = get_object_or_404(TrainingRecord, id=record_id)

    if request.method == 'POST':
        form = TrainingRecordReviewerForm(request.POST, instance=record)
        if form.is_valid():
            qa_record = form.save(commit=False)
            qa_record.qa_printed_name = request.user
            qa_record.save()
            messages.success(request, "Review submitted successfully.")
            return redirect('review_form', record_id=record.id)
        else:
            messages.error(request, "There was an error submitting your review.")
    else:
        form = TrainingRecordReviewerForm(instance=record)

    # Adding logic to fetch other records needing review
    unreviewed_records = TrainingRecord.objects.filter(qa_review_date__isnull=True).exclude(id=record.id)

    return render(request, 'reviewer_training_record.html', {
        'form': form,
        'record': record,
        'is_reviewer': True,
        'reviewed_records': TrainingRecord.objects.filter(qa_printed_name=request.user),
        'unreviewed_records': unreviewed_records,  
    })
@login_required
def training_record_list(request):
    if not request.user.groups.filter(name='reviewer').exists():
        return redirect('unauthorized')
    
    records = TrainingRecord.objects.all()  # Filter as needed
    return render(request, 'review_record_list.html', {'records': records})

@login_required
@user_passes_test(lambda u: u.groups.filter(name='reviewer').exists())
def reviewer_dashboard(request):
    posts = Post.objects.all()
    return render(request, 'reviewer_dashboard.html', {'posts': posts})



##########VIEW FUNCTIONS FOR POSTS###########
@login_required
@user_passes_test(lambda u: u.groups.filter(name='staff').exists())
def upload_files(request):
    context = {'page_title': 'Uploads'}
    posts = Post.objects.filter(user=request.user).order_by('title', '-date_created')
    context['posts'] = posts
    messages.success(request, "File list loaded successfully.")
    context['status'] = 'success'
    return render(request, 'upload_files.html', context)


@login_required
def uploaded_files(request):
    context = {'page_title': 'Training'}
    if request.user.is_superuser:
        posts = Post.objects.all()
    else:
        posts = Post.objects.filter(user=request.user)

    context['posts'] = posts
    context['postsLen'] = posts.count()
    context['status'] = 'success'

    messages.success(request, "Uploaded files loaded successfully.")
    print(request.build_absolute_uri())
    return render(request, 'uploaded_files.html', context)
@login_required
@user_passes_test(lambda u: u.groups.filter(name='staff').exists())
def save_post(request):
    resp = {'status': 'failed', 'msg': ''}
    if request.method == 'POST':
        try:
            # Debug: Log all POST data
            print("POST data:", request.POST)

            # Get form data
            title = request.POST.get('title')
            description = request.POST.get('description', '')  # Default to empty string if not provided
            file_path = request.FILES.get('file_path')  # Optional file upload
            user_id = request.user.id  # Get user_id from the form
            post_id = request.POST.get('id')
            default_title = request.POST.get('default_title')  # Get default_title from the form

            # Debug: Log user_id and default_title
            print("User ID from form:", user_id)
            print("Default Title from form:", default_title)

            # Use default_title if title is not provided
            if not title and default_title:
                title = default_title

            # Validate required fields
            if not title:
                resp['msg'] = "Title is required."
                return JsonResponse(resp)

            # Ensure user_id is provided
            if not user_id:
                resp['msg'] = "User ID is missing."
                return JsonResponse(resp)

            # Check if updating an existing post
            if post_id:
                post = Post.objects.get(id=post_id)
                if post.user != request.user:  # Ensure staff can only update their own posts
                    resp['msg'] = "You do not have permission to update this post."
                    return JsonResponse(resp)
                post.title = title
                post.description = description
                if file_path:  # Update file only if a new file is provided
                    post.file_path = file_path
                post.save()
            else:
                # Create a new post
                post = Post(
                    title=title,
                    description=description,
                    file_path=file_path,
                    user=request.user  # Assign the user_id
                )
                post.save()

            messages.success(request, 'File has been saved successfully.')
            resp['status'] = 'success'
        except Exception as e:
            # Log any unexpected errors
            print("Error:", str(e))
            resp['msg'] = str(e)
    else:
        resp['msg'] = "No Data sent."
    return JsonResponse(resp)
@login_required
@user_passes_test(lambda u: u.groups.filter(name='staff').exists())
def manage_post(request, pk=None):
    context['page_title'] = 'Manage Post'
    context['post'] = {}
    # Get the default title from the URL parameter
    default_title = request.GET.get('default_title', '')
    if not pk is None:
        post = get_object_or_404(Post, id=pk)
        if post.user != request.user:  # Ensure staff can only manage their own posts
            messages.error(request, "You do not have permission to manage this post.")
            return redirect('posts_mgt')
        context['post'] = post
    else:
        # Pre-fill the form with the default title if provided
        context['post'] = {'title': default_title}
    return render(request, 'manage_post.html', context)

@login_required
@user_passes_test(lambda u: u.groups.filter(name='staff').exists())
@user_passes_test(lambda u: u.groups.filter(name='staff').exists())
def delete_post(request):
    resp = {'status':'failed', 'msg':''}
    if request.method == 'POST':
        try:
            post = Post.objects.get(id=request.POST['id'])
            if post.user != request.user:  # Ensure staff can only delete their own posts
                resp['msg'] = "You do not have permission to delete this post."
                return HttpResponse(json.dumps(resp), content_type="application/json")
            post = Post.objects.get(id=request.POST['id'])
            if post.user != request.user:  # Ensure staff can only delete their own posts
                resp['msg'] = "You do not have permission to delete this post."
                return HttpResponse(json.dumps(resp), content_type="application/json")
            post.delete()
            resp['status'] = 'success'
            messages.success(request, 'Post has been deleted successfully')
        except:
            resp['msg'] = "Undefined Post ID"
    return HttpResponse(json.dumps(resp), content_type="application/json")
def shareF(request,id=None):
    # print(str("b'UdhnfelTxqj3q6BbPe7H86sfQnboSBzb0irm2atoFUw='").encode())
    context['page_title'] = 'Shared File'
    if not id is None:
        key = settings.ID_ENCRYPTION_KEY
        fernet = Fernet(key)
        id = base64.urlsafe_b64decode(id)
        id = fernet.decrypt(id).decode()
        post = Post.objects.get(id = id)
        context['post'] = post
        context['page_title'] += str(" - " + post.title)
   
    return render(request, 'share-file.html',context)

@login_required
@user_passes_test(lambda u: u.groups.filter(name='reviewer').exists())
def update_status(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if request.method == 'POST':
        status = request.POST.get('status')
        post.status = status
        post.reviewer = request.user
        post.save()
        return JsonResponse({'success': True})
    return JsonResponse({'success': False})



