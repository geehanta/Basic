from django import forms
from django.contrib.auth.forms import UserCreationForm,PasswordChangeForm, UserChangeForm
from django.contrib.auth.models import User
from .models import Post
from .models import TrainingRecord

class UserRegistration(UserCreationForm):
    email = forms.EmailField(max_length=250,help_text="Email is required.")
    first_name = forms.CharField(max_length=250,help_text="First Name  is required.")
    last_name = forms.CharField(max_length=250,help_text="Last Name is required.")

    class Meta:
        model = User
        fields = ('email', 'username', 'password1', 'password2', 'first_name', 'last_name')
    

    def clean_email(self):
        email = self.cleaned_data['email']
        try:
            user = User.objects.get(email = email)
        except Exception as e:
            return email
        raise forms.ValidationError(f"The {user.email} mail already exists! ")

    def clean_username(self):
        username = self.cleaned_data['username']
        try:
            user = User.objects.get(username = username)
        except Exception as e:
            return username
        raise forms.ValidationError(f"The {user.username} username already exists/taken")


class UpdateProfile(UserChangeForm):
    username = forms.CharField(max_length=250,help_text="Username is required!")
    email = forms.EmailField(max_length=250,help_text="Email is required!")
    first_name = forms.CharField(max_length=250,help_text="First Name  is required!")
    last_name = forms.CharField(max_length=250,help_text="The Last Name  is required!")
    current_password = forms.CharField(max_length=250)

    class Meta:
        model = User
        fields = ('email', 'username','first_name', 'last_name')

    def clean_current_password(self):
        if not self.instance.check_password(self.cleaned_data['current_password']):
            raise forms.ValidationError(f"Password is Incorrect")

    def clean_email(self):
        email = self.cleaned_data['email']
        try:
            user = User.objects.exclude(id=self.cleaned_data['id']).get(email = email)
        except Exception as e:
            return email
        raise forms.ValidationError(f"The {user.email} mail already exists")

    def clean_username(self):
        username = self.cleaned_data['username']
        try:
            user = User.objects.exclude(id=self.cleaned_data['id']).get(username = username)
        except Exception as e:
            return username
        raise forms.ValidationError(f"The {user.username} username already exists")

class UpdatePasswords(PasswordChangeForm):
    old_password = forms.CharField(widget=forms.PasswordInput(attrs={'class':'form-control form-control-sm rounded-0'}), label="Old Password")
    new_password1 = forms.CharField(widget=forms.PasswordInput(attrs={'class':'form-control form-control-sm rounded-0'}), label="New Password")
    new_password2 = forms.CharField(widget=forms.PasswordInput(attrs={'class':'form-control form-control-sm rounded-0'}), label="Confirm New Password")
    class Meta:
        model = User
        fields = ('old_password','new_password1', 'new_password2')

class SavePost(forms.ModelForm):
    user = forms.IntegerField(help_text = "User Field is required.")
    title = forms.CharField(max_length=250,help_text = "Title Field is required.")
    description = forms.Textarea()

    class Meta:
        model= Post
        fields = ('user','title','description','file_path')
    
    def clean_title(self):
        id = self.instance.id if not self.instance == None else 0
        try:
            if id.isnumeric():
                 post = Post.objects.exclude(id = id).get(title = self.cleaned_data['title'])
            else:
                 post = Post.objects.get(title = self.cleaned_data['title'])
        except:
            return self.cleaned_data['title']
        raise forms.ValidationError(f'{post.title} post Already Exists.')

    def clean_user(self):
        user_id = self.cleaned_data['user']
        print("USER: "+ str(user_id))
        try:
            user = User.objects.get(id = user_id)
            return user
        except:
            raise forms.ValidationError("User ID is unrecognized.")
class TrainingRecordStaffForm(forms.ModelForm):
    class Meta:
        model = TrainingRecord
        exclude = ['employee', 'qa_review_date', 'qa_printed_name', 'qa_signature', 'date_reviewed','created_at', 'updated_at']

        widgets = {
            'supervisor_date': forms.DateInput(attrs={'type': 'date'}),
            'records_maintenance_date': forms.DateInput(attrs={'type': 'date'}),
        }

class TrainingRecordReviewerForm(forms.ModelForm):
    class Meta:
        model = TrainingRecord
        fields = ['qa_review_date', 'qa_signature']

        widgets = {
            'qa_review_date': forms.DateInput(attrs={'type': 'date'}),
        }