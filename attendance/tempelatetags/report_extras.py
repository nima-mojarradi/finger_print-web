from django import template
from datetime import timedelta

register = template.Library()

@register.filter
def get_daily_hours(work_hours_dict, event):
    key = (event.user.id, event.timestamp.date())
    total_seconds = work_hours_dict.get(key, timedelta()).total_seconds()
    hours = total_seconds / 3600
    return round(hours, 2) if hours > 0 else None