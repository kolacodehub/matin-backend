import requests
import datetime
import traceback
from django.db.models import Sum, F
from django.conf import settings  # Needed to grab your QF_CLIENT_ID
from datetime import timedelta
from zoneinfo import ZoneInfo
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from django.utils import timezone
from django.shortcuts import get_object_or_404
from .serializers import ReflectionIngestionSerializer, ReflectionQueueSerializer
from .utils import get_next_midnight_for_user
from .models import Reflection, ReviewLog


class IngestReflectionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # 1. Validate using your original serializer
        serializer = ReflectionIngestionSerializer(data=request.data)

        if not serializer.is_valid():
            print("🚨 SERIALIZER ERRORS:", serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        ayah_key = serializer.validated_data["ayah_key"]
        reflection_text = serializer.validated_data["reflection_text"]

        # 2. Parse the ayah_key for the QF API before saving
        try:
            chapter_id, verse_number = ayah_key.split(":")
            chapter_id = int(chapter_id)
            verse_number = int(verse_number)
        except ValueError:
            return Response(
                {"error": "Invalid ayah_key format. Must be 'chapter:verse'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        INGESTION_REWARD = 5

        # 3. Your Original Spaced Repetition & Gamification Engine
        try:
            with transaction.atomic():
                # Create the Reflection (state machine)
                reflection = Reflection.objects.create(
                    user=request.user,
                    ayah_key=ayah_key,
                    reflection_text=reflection_text,
                    next_review_date=get_next_midnight_for_user(request.user),
                    total_points_earned=INGESTION_REWARD,
                )

                # Create the immutable ledger entry
                ReviewLog.objects.create(
                    user=request.user,
                    reflection=reflection,
                    grade=None,  # No grade for ingestion
                    points_awarded=INGESTION_REWARD,
                    was_in_grace_period=False,
                )
        except Exception:
            traceback.print_exc()  # prints full traceback to terminal
            return Response(
                {"error": "Database transaction failed."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # 4. The Hackathon Magic: Sync to Quran Foundation
        qf_post_url = "https://apis-prelive.quran.foundation/quran-reflect/v1/posts"
        headers = {
            "x-auth-token": request.user.qf_access_token,
            "x-client-id": settings.QF_CLIENT_ID,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        payload = {
            "post": {
                "body": reflection_text,
                "draft": False,
                "references": [
                    {"chapterId": chapter_id, "from": verse_number, "to": verse_number}
                ],
            }
        }

        try:
            # Fire the request to QF (Notice this happens AFTER the database is safely updated)
            qf_response = requests.post(
                qf_post_url, json=payload, headers=headers, timeout=30
            )
            qf_response.raise_for_status()
            sync_status = "Synced to Quran Foundation."
        except requests.exceptions.RequestException as e:
            print(f"[QF SYNC ERROR] {str(e)}")
            sync_status = "Saved locally, but failed to sync to Quran Foundation."

        # 5. Return the merged response (Points + Sync Status!)
        return Response(
            {
                "message": "Reflection ingested successfully.",
                "sync_status": sync_status,
                "reflection_id": reflection.id,
                "points_earned": INGESTION_REWARD,
                "next_review_date": reflection.next_review_date,
            },
            status=status.HTTP_201_CREATED,
        )


class ReflectionListView(ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ReflectionQueueSerializer

    def get_queryset(self):
        # Fetch ALL active reflections for this user, newest first
        return Reflection.objects.filter(
            user=self.request.user, is_active=True
        ).order_by("-created_at")


class GradeReviewView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        item_id = request.data.get("item_id")
        grade = request.data.get("grade")

        if grade not in [0, 1, 2, 3]:
            return Response(
                {"error": "Grade must be exactly 0, 1, 2, or 3."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        item = get_object_or_404(Reflection, id=item_id, user=request.user)

        # 1. Base Economy Setup
        BASE_REWARD = 2
        points_earned = BASE_REWARD * grade if grade > 0 else 0

        # 2. The SuperMemo-2 (SM-2) Algorithm (Fixed 'interval_days' to 'interval')
        if grade == 0:
            item.repetitions = 0
            item.interval = 0
            item.ease_factor = max(1.3, item.ease_factor - 0.2)
        elif grade == 1:
            item.repetitions = 0
            item.interval = 1
            item.ease_factor = max(1.3, item.ease_factor - 0.15)
        else:
            if item.repetitions == 0:
                item.interval = 1
            elif item.repetitions == 1:
                item.interval = 6
            else:
                item.interval = round(item.interval * item.ease_factor)

            item.repetitions += 1

            if grade == 3:
                item.ease_factor += 0.15

        # 3. Timezone-Aware Scheduling
        user_tz_string = getattr(request.user, "timezone", "UTC")
        try:
            user_tz = ZoneInfo(user_tz_string)
        except Exception:
            user_tz = ZoneInfo("UTC")

        now_local = timezone.now().astimezone(user_tz)
        target_local_date = now_local.date() + datetime.timedelta(
            days=max(1, item.interval)
        )
        new_midnight_local = datetime.datetime.combine(
            target_local_date, datetime.time.min, tzinfo=user_tz
        )

        item.next_review_date = new_midnight_local.astimezone(datetime.timezone.utc)
        item.total_points_earned += points_earned

        # 4. Atomic Database Execution
        try:
            with transaction.atomic():
                item.save()

                ReviewLog.objects.create(
                    user=request.user,
                    reflection=item,
                    grade=grade,
                    points_awarded=points_earned,
                    was_in_grace_period=False,
                )
        except Exception:
            traceback.print_exc()
            return Response(
                {"error": "Database transaction failed."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(
            {
                "message": "Grade processed successfully.",
                "new_interval": item.interval,
                "next_review_date": item.next_review_date,
                "points_awarded": points_earned,
            },
            status=status.HTTP_200_OK,
        )


class ReviewQueueView(ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ReflectionQueueSerializer

    def get_queryset(self):
        user = self.request.user

        # 1. Grab the user's timezone string (defaults to UTC if missing)
        tz_string = getattr(user, "timezone", "UTC")
        user_tz = ZoneInfo(tz_string)

        # 2. Convert current UTC time to the user's exact local time
        local_now = timezone.localtime(timezone.now(), timezone=user_tz)

        # 3. Filter using the local time
        return Reflection.objects.filter(
            user=user,
            is_active=True,
            # IMPORTANT: If next_review_date is a models.DateField(), use local_now.date()
            # If it is a models.DateTimeField(), use local_now
            next_review_date__lte=local_now,
        ).order_by("next_review_date")


class BuyGracePeriodView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        GRACE_PERIOD_COST = 500

        # 1. Calculate the user's real-time wallet balance from the ledger
        wallet_balance = (
            ReviewLog.objects.filter(user=request.user).aggregate(
                Sum("points_awarded")
            )["points_awarded__sum"]
            or 0
        )

        # 2. Check for sufficient funds
        if wallet_balance < GRACE_PERIOD_COST:
            return Response(
                {
                    "error": f"Insufficient funds. You need {GRACE_PERIOD_COST} points, but have {wallet_balance}."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            with transaction.atomic():
                # 3. Bulk-shift every active item's due date forward by exactly 24 hours
                Reflection.objects.filter(user=request.user, is_active=True).update(
                    next_review_date=F("next_review_date") + timedelta(days=1)
                )

                # 4. Charge the user by writing a negative transaction to the Ledger
                ReviewLog.objects.create(
                    user=request.user,
                    reflection=None,  # This is a global purchase, so it doesn't tie to a single flashcard
                    grade=None,
                    points_awarded=-GRACE_PERIOD_COST,
                    was_in_grace_period=False,
                )

        except Exception:
            traceback.print_exc()
            return Response(
                {"error": "Database transaction failed."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(
            {
                "message": "Grace period activated. All due dates pushed back by 24 hours.",
                "new_balance": wallet_balance - GRACE_PERIOD_COST,
            },
            status=status.HTTP_200_OK,
        )


class BalanceView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        balance = (
            ReviewLog.objects.filter(user=request.user).aggregate(
                total=Sum("points_awarded")
            )["total"]
            or 0
        )

        return Response({"balance": balance})
