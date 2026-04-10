from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from django.utils import timezone
from datetime import timedelta
from .models import Reflection, ReviewLog
from .serializers import ReflectionIngestionSerializer


class IngestReflectionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ReflectionIngestionSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        INGESTION_REWARD = 5

        try:
            with transaction.atomic():
                # 1. Create the Reflection (state machine)
                reflection = Reflection.objects.create(
                    user=request.user,
                    ayah_key=serializer.validated_data["ayah_key"],
                    reflection_text=serializer.validated_data["reflection_text"],
                    next_review_date=timezone.now() + timedelta(hours=24),
                    total_points_earned=INGESTION_REWARD,
                )

                # 2. Create the immutable ledger entry
                ReviewLog.objects.create(
                    user=request.user,
                    reflection=reflection,
                    grade=None,  # No grade for ingestion
                    points_awarded=INGESTION_REWARD,
                    was_in_grace_period=False,
                )

        except Exception as e:
            import traceback
            traceback.print_exc()  # prints full traceback to terminal
            return Response(
                {"error": "Database transaction failed."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        return Response(
            {
                "message": "Reflection ingested successfully.",
                "reflection_id": reflection.id,
                "points_earned": INGESTION_REWARD,
                "next_review_date": reflection.next_review_date,
            },
            status=status.HTTP_201_CREATED,
        )
