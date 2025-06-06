from django.contrib import admin
from django.urls import path
from django.conf.urls.static import static
from . import views
from django.contrib.auth import views as auth_views
from django.views.generic.base import RedirectView
#######THESE URLS ARE IN THE ORDER THEY ARE CALLED ON THE VIEWS.PY PAGE ###########
urlpatterns = [
    path('redirect-admin', RedirectView.as_view(url="/admin"),name="redirect-admin"), #Admin-access
    path('login',auth_views.LoginView.as_view(template_name="login.html",redirect_authenticated_user = True),name='login'),
    path('userlogin', views.login_user, name="login-user"),
    path('user-register', views.registerUser, name="register-user"),
    path('logout',views.logoutuser,name='logout'),
    path('profile',views.profile,name='profile'),
    path('update-profile',views.update_profile,name='update-profile'),
    # path('update-avatar',views.update_avatar,name='update-avatar'),
    path('update-password',views.update_password,name='update-password'),
    #########PAGES THAT DONT REQUIRE LOGIN###########
    path('tools', views.tools, name='tools'), # No login required
    path('calendar', views.calendar, name='calendar'), # No login required
    path('home', views.home, name='home'),  # Map the root URL to the home view
    #########PAGES THAT REQUIRE LOGIN###########
    path('', views.studies_dashboard, name='studies_dashboard'), # Login required
    path('enter_training_record', views.create_training_record, name='enter_training_record'), # Staff enters training record
    path('Upload_files', views.upload_files, name='upload_files'), # staff uploads files
    path('uploaded_files', views.uploaded_files, name='uploaded_files'), #staff view uploaded files
    #path('review_training_records', views.training_record_review, name='review_training_records'), # lists all records
    path('review_training_records/<int:record_id>/', views.training_record_review, name='review_training_records'),#reviewer adds/view training records
    path('reviewer_dashboard', views.reviewer_dashboard, name='reviewer_dashboard'), # reviewer dashboard
    path('inventory', views.inventory, name='inventory'), # login required
    path('reports', views.reports, name='reports'), # login required    
    path('save_post', views.save_post, name='save-post'),
    #path('my_posts', views.posts_mgt, name='posts-page'), # login required
    path('reviewer/', views.reviewer_dashboard, name='reviewer_dashboard'),
    path('update-status/<int:post_id>/', views.update_status, name='update_status'),
    path('manage_post', views.manage_post, name='manage-post'),
    path('manage_post/<int:pk>', views.manage_post, name='manage-post'),
    path('delet_post', views.delete_post, name='delete-post'),
    path(r'shareF/<str:id>', views.shareF, name='share-file-id'),
    path('shareF/', views.shareF, name='share-file'),
]
