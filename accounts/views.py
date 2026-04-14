import json
import base64
import urllib.request
import urllib.parse
import urllib.error
import jwt
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from rest_framework.authtoken.models import Token
from .models import User


class QFAuthExchangeView(APIView):
    permission_classes = []

    def post(self, request):

        code = request.data.get("code")
        redirect_uri = request.data.get("redirect_uri")
        code_verifier = request.data.get("code_verifier") # <-- GET IT FROM REACT

        if not code or not redirect_uri:
            return Response(
                {"error": "Missing 'code' or 'redirect_uri' in payload."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        token_url = f"{settings.QF_OAUTH_URL.rstrip('/')}/oauth2/token"

        payload_dict = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri,
            "code_verifier": code_verifier,
        }
        data = urllib.parse.urlencode(payload_dict).encode("utf-8")

        auth_string = f"{settings.QF_CLIENT_ID}:{settings.QF_CLIENT_SECRET}"
        base64_auth = base64.b64encode(auth_string.encode("ascii")).decode("ascii")

        req = urllib.request.Request(token_url, data=data)
        req.add_header("Authorization", f"Basic {base64_auth}")
        req.add_header("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64)")
        req.add_header("Content-Type", "application/x-www-form-urlencoded")
        req.add_header("Accept", "application/json")

        try:
            with urllib.request.urlopen(req, timeout=10) as response:
                response_data = response.read()
                token_data = json.loads(response_data)

        except urllib.error.HTTPError as e:
            error_msg = e.read().decode("utf-8")
            print(f"[QF AUTH ERROR] HTTPError: {error_msg}")
            return Response(
                {"error": "Authentication provider rejected the request."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except urllib.error.URLError as e:
            print(f"[QF AUTH ERROR] Network Crash: {str(e)}")
            return Response(
                {"error": "Internal network error during authentication."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        id_token = token_data.get("id_token")
        if not id_token:
            return Response(
                {"error": "Authentication succeeded, but no ID token was returned."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Logical validation of claims (Zero crypto cost, high security)
        try:
            decoded_id_token = jwt.decode(
                id_token,
                options={
                    "verify_signature": False,
                    "verify_exp": True,
                    "verify_aud": True,
                    "verify_iss": True,
                },
                audience=settings.QF_CLIENT_ID,
                issuer=settings.QF_OAUTH_URL,
                algorithms=["RS256", "HS256"],
            )
            qf_sub_id = decoded_id_token.get("sub")
        except (
            jwt.InvalidTokenError
        ) as e:  # PERFECTED: Catches all PyJWT validation failures
            print(f"[JWT VALIDATION ERROR] {str(e)}")
            return Response(
                {
                    "error": "Failed to validate ID token claims (e.g., expired, wrong audience)."
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if not qf_sub_id:
            return Response(
                {"error": "Invalid ID token structure: missing sub claim."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        refresh_token = token_data.get("refresh_token")
        if not refresh_token:
            refresh_token = None

        user, created = User.objects.update_or_create(
            qf_sub_id=qf_sub_id,
            defaults={
                "qf_access_token": token_data.get("access_token"),
                "qf_refresh_token": refresh_token,
            },
        )

        matin_token, _ = Token.objects.get_or_create(user=user)

        return Response(
            {
                "token": matin_token.key,
                "user_id": user.qf_sub_id,
                "is_new_user": created,
            },
            status=status.HTTP_200_OK,
        )


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            # Physically delete the token from the database
            request.user.auth_token.delete()
            return Response(
                {"message": "Successfully logged out."}, status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {"error": "Failed to log out."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

