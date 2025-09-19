from django.urls import path
from django.views.generic import RedirectView
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    ## User Authentication and Profile Management ##
    path('redirect-admin/', RedirectView.as_view(url="/admin"), name="redirect-admin"),
    path('login/', auth_views.LoginView.as_view(
        template_name="user_auth/login.html",
        redirect_authenticated_user=True
    ), name='login'),
    path('userlogin/', views.login_user, name="login-user"),
    path('user-register/', views.registerUser, name="register-user"),
    path('logout/', views.logoutuser, name='logout'),
    path('profile/', views.profile, name='profile'),
    path('update-profile/', views.update_profile, name='update-profile'),
    path('update-password/', views.update_password, name='update-password'),

    ## Application Views ##
    path('', views.home, name='home'),  # Home page
    path('studies-dashboard/', views.studies_dashboard, name='studies_dashboard'),
    path('documents/', views.review_document, name='review_document'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path("documents/update/<int:doc_id>/", views.update_document, name="update_document"),
    path("documents/delete/<int:doc_id>/", views.delete_document, name="delete_document"),
]
