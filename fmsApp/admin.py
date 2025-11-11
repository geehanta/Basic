from django.contrib import admin
from .models import Document
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import UserProfile

from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import UserProfile


# --- Define an inline admin for UserProfile ---
class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'
    fk_name = 'user'
    extra = 0  # Don’t show extra empty forms


# --- Extend the built-in User admin to include UserProfile inline ---
class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)

    # Optional: make profile image visible in list view
    list_display = ('username', 'email', 'first_name', 'last_name', 'get_profile_image')
    list_select_related = ('profile',)

    def get_profile_image(self, instance):
        if hasattr(instance, 'profile') and instance.profile.profile_image:
            return f"✅ Yes"
        return "—"
    get_profile_image.short_description = "Has Profile Image"

    def get_inline_instances(self, request, obj=None):
        # Avoid error when adding a new user
        if not obj:
            return []
        return super().get_inline_instances(request, obj)


# --- Unregister the original User admin and register the new one ---
admin.site.unregister(User)
admin.site.register(User, UserAdmin)
admin.site.register(Document)

# Optionally also register the profile model directly (for standalone access)
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'profile_image')

