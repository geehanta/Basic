from django import forms
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm, UserChangeForm
from django.contrib.auth.models import User
from .models import Document, UserProfile


##############################################
# USER REGISTRATION FORM
##############################################
class UserRegistration(UserCreationForm):
    email = forms.EmailField(max_length=250, help_text="Email is required.")
    first_name = forms.CharField(max_length=250, help_text="First Name is required.")
    last_name = forms.CharField(max_length=250, help_text="Last Name is required.")

    class Meta:
        model = User
        fields = ('email', 'username', 'password1', 'password2', 'first_name', 'last_name')

    # Ensure email is unique
    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError(f"The email {email} already exists!")
        return email

    # Ensure username is unique
    def clean_username(self):
        username = self.cleaned_data['username']
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError(f"The username {username} is already taken!")
        return username


##############################################
# UPDATE PROFILE FORM (WITH PROFILE IMAGE)
##############################################
class UpdateProfile(UserChangeForm):
    username = forms.CharField(max_length=250, help_text="Username is required!")
    email = forms.EmailField(max_length=250, help_text="Email is required!")
    first_name = forms.CharField(max_length=250, help_text="First Name is required!")
    last_name = forms.CharField(max_length=250, help_text="Last Name is required!")
    
    # Added image field for profile picture upload
    profile_image = forms.ImageField(
        required=False,
        label="Profile Picture",
        help_text="Upload a new profile image (optional)."
    )

    # Require user to confirm changes by entering current password
    current_password = forms.CharField(
        max_length=250,
        widget=forms.PasswordInput(),
        label="Current Password",
        help_text="Enter your current password to confirm changes."
    )

    class Meta:
        model = User
        fields = ('email', 'username', 'first_name', 'last_name')

    ##################################################
    # VALIDATION METHODS
    ##################################################
    def clean_current_password(self):
        """Validate that entered password matches the user's current password."""
        if not self.instance.check_password(self.cleaned_data['current_password']):
            raise forms.ValidationError("Password is incorrect")
        return self.cleaned_data['current_password']

    def clean_email(self):
        """Ensure updated email is unique."""
        email = self.cleaned_data['email']
        if User.objects.exclude(id=self.instance.id).filter(email=email).exists():
            raise forms.ValidationError(f"The email {email} already exists!")
        return email

    def clean_username(self):
        """Ensure updated username is unique."""
        username = self.cleaned_data['username']
        if User.objects.exclude(id=self.instance.id).filter(username=username).exists():
            raise forms.ValidationError(f"The username {username} is already taken!")
        return username

    ##################################################
    # SAVE METHOD (Handles both User and UserProfile)
    ##################################################
    def save(self, commit=True):
        """
        Override save() to handle both the User fields and
        the related UserProfile image update.
        """
        user = super().save(commit=commit)
        # Ensure the related UserProfile exists
        profile, created = UserProfile.objects.get_or_create(user=user)

        # If the user uploaded a new profile image, save it
        if self.cleaned_data.get('profile_image'):
            profile.profile_image = self.cleaned_data['profile_image']
            profile.save()

        return user


##############################################
# UPDATE PASSWORD FORM
##############################################
class UpdatePasswords(PasswordChangeForm):
    old_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control form-control-sm rounded-0'}),
        label="Old Password"
    )
    new_password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control form-control-sm rounded-0'}),
        label="New Password"
    )
    new_password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control form-control-sm rounded-0'}),
        label="Confirm New Password"
    )

    class Meta:
        model = User
        fields = ('old_password', 'new_password1', 'new_password2')


##############################################
# DOCUMENT UPLOAD FORM
##############################################
class DocumentUploadForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = ["section", "doc_type", "description", "file"]


##############################################
# DOCUMENT REVIEW FORM
##############################################
class DocumentReviewForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = ["status", "reviewer_feedback"]

