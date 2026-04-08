import requests
import jwt
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authtoken.models import Token
from .models import User


class QFAuthExchangeView(APIView):
    # This endpoint is public so unauthenticated users can log in
    permission_classes = []

    def post(self, request):
        code = request.data.get("code")
        redirect_uri = request.data.get("redirect_uri")

        # 1. Contract Validation
        if not code or not redirect_uri:
            return Response(
                {"error": "Missing 'code' or 'redirect_uri' in payload."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 2. Trading the code for tokens from the Quran Foundation
        token_url = f"{settings.QF_OAUTH_URL.rstrip('/')}/oauth2/token"

        payload = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri,
        }

        # Confidential clients are to authenticate via HTTP Basic Auth
        auth = (settings.QF_CLIENT_ID, settings.QF_CLIENT_SECRET)

        try:
            # I am using a 10-second timeout. Never let an external API hang your server indefinitely.
            qf_response = requests.post(token_url, data=payload, auth=auth, timeout=10)
            qf_response.raise_for_status()
            token_data = qf_response.json()
        except requests.exceptions.RequestException as e:
            # If the QF API rejects the code (e.g., it expired), I fail gracefully
            return Response(
                {
                    "error": "Failed to exchange token with Quran Foundation.",
                    "details": str(e),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 3. Extract the ID Token
        id_token = token_data.get("id_token")
        if not id_token:
            return Response(
                {"error": "Authentication succeeded, but no ID token was returned."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 4. Decoding the JWT to get the user's permanent ID (sub)
        # I disable signature verification because I just received this token
        # directly from the QF server via a secure backchannel server-to-server request.
        try:
            decoded_id_token = jwt.decode(
                id_token,
                options={"verify_signature": False},
                algorithms=["RS256", "HS256"],
            )
            qf_sub_id = decoded_id_token.get("sub")
        except jwt.DecodeError:
            return Response(
                {"error": "Failed to decode ID token."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 5. Create or Update the user in my local PostgreSQL database
        user, created = User.objects.update_or_create(
            qf_sub_id=qf_sub_id,
            defaults={
                "qf_access_token": token_data.get("access_token"),
                "qf_refresh_token": token_data.get("refresh_token", ""),
            },
        )

        # 6. Generate Matin's local API token for the React frontend
        matin_token, _ = Token.objects.get_or_create(user=user)

        # 7. Return the final contract
        return Response(
            {
                "token": matin_token.key,
                "user_id": user.qf_sub_id,
                "is_new_user": created,
            },
            status=status.HTTP_200_OK,
        )
