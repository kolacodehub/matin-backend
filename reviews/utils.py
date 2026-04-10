import datetime
from zoneinfo import ZoneInfo
from django.utils import timezone


def get_next_midnight_for_user(user):
    """
    Calculates the exact UTC timestamp for midnight tomorrow
    in the user's specific timezone.
    """
    # 1. Get the user's timezone string (e.g., 'Africa/Lagos' or 'UTC')
    user_tz_string = getattr(user, "timezone", "UTC")

    try:
        user_tz = ZoneInfo(user_tz_string)
    except Exception:
        user_tz = ZoneInfo("UTC")  # Fallback if React sends garbage data

    # 2. Get current time in their local timezone
    now_local = timezone.now().astimezone(user_tz)

    # 3. Add one day and snap to 00:00:00
    tomorrow_local = now_local.date() + datetime.timedelta(days=1)
    midnight_local = datetime.datetime.combine(
        tomorrow_local, datetime.time.min, tzinfo=user_tz
    )

    # 4. Convert back to UTC for safe PostgreSQL storage
    return midnight_local.astimezone(datetime.timezone.utc)
