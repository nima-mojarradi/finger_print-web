from django import template
from datetime import timedelta

register = template.Library()

@register.filter
def get_work_hours(work_hours_dict, key):
    """دریافت ساعت کاری از دیکشنری با کلید tuple (user_id, date)"""
    return work_hours_dict.get(key)


@register.filter
def get_item(dictionary, key):
    """
    برای دسترسی به آیتم‌های یک دیکشنری یا لیست با استفاده از یک کلید متغیر در قالب جنگو.
    استفاده: {{ my_dictionary|get_item:key_variable }}
    """
    if isinstance(dictionary, dict):
        return dictionary.get(key)
    try:
        return dictionary[key]
    except (KeyError, IndexError, TypeError):
        return None

@register.filter(name='split')
def split(value, arg):
    """Split a string by the given delimiter"""
    return value.split(arg)


@register.filter
def get_daily_hours(work_hours_dict, event):
    key = (event.user.nationality_number, event.timestamp.date())
    total_seconds = work_hours_dict.get(key, timedelta()).total_seconds()
    hours = total_seconds / 3600
    return round(hours, 2) if hours > 0 else None