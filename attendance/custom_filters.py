from django import template

register = template.Library()

@register.filter
def get_work_hours(work_hours_dict, key):
    """دریافت ساعت کاری از دیکشنری با کلید tuple (user_id, date)"""
    return work_hours_dict.get(key)
