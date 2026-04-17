from django.dispatch import receiver
from django.urls import reverse
from django_rest_passwordreset.signals import reset_password_token_created


@receiver(reset_password_token_created)
def password_reset_token_created(
    sender, instance, reset_password_token, *args, **kwargs
):
    # In production, this would be my React frontend URL.
    # I will print it to the console so I can test it locally.
    reset_url = f"https://matin-frontend.vercel.app/reset-password?token={reset_password_token.key}"
    print(f"\n=== PASSWORD RESET EMAIL ===")
    print(f"Send to: {reset_password_token.user.email}")
    print(f"Reset Link: {reset_url}")
    print(f"============================\n")
