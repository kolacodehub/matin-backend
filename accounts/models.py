from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager


class UserManager(BaseUserManager):
    def create_user(self, qf_sub_id, password=None, **extra_fields):
        if not qf_sub_id:
            raise ValueError("The QF Subject ID must be set")
        user = self.model(qf_sub_id=qf_sub_id, **extra_fields)

        if password:
            user.set_password(password)
        else:
            # This is for your regular Quran Foundation users
            user.set_unusable_password()

        user.save(using=self._db)
        return user

    def create_superuser(self, qf_sub_id, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(qf_sub_id, **extra_fields)


class User(AbstractBaseUser):
    timezone = models.CharField(max_length=50, default="UTC")
    # The 'sub' claim from the Quran Foundation ID Token
    qf_sub_id = models.CharField(max_length=255, unique=True, primary_key=True)

    # Store these to make API calls to QF on their behalf
    qf_access_token = models.TextField(blank=True, null=True)
    qf_refresh_token = models.TextField(blank=True, null=True)

    # Cached economy variable
    total_points = models.IntegerField(default=0)

    # Required fields for Django admin/permissions if you use them
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    USERNAME_FIELD = "qf_sub_id"
    objects = UserManager()

    def __str__(self):
        return f"QF_User: {self.qf_sub_id}"

    # Required permission methods for AbstractBaseUser
    def has_perm(self, perm, obj=None):
        return self.is_superuser

    def has_module_perms(self, app_label):
        return self.is_superuser
