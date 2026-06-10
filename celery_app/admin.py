from django.contrib import admin
from unfold.admin import ModelAdmin

from django_celery_beat.models import (
    PeriodicTask,
    IntervalSchedule,
    CrontabSchedule,
    SolarSchedule,
    ClockedSchedule,
)

from django_celery_beat.admin import (
    PeriodicTaskAdmin as BasePeriodicTaskAdmin,
    CrontabScheduleAdmin as BaseCrontabScheduleAdmin,
    ClockedScheduleAdmin as BaseClockedScheduleAdmin,
)


# Unregister default admins
admin.site.unregister(PeriodicTask)
admin.site.unregister(IntervalSchedule)
admin.site.unregister(CrontabSchedule)
admin.site.unregister(SolarSchedule)
admin.site.unregister(ClockedSchedule)


@admin.register(PeriodicTask)
class PeriodicTaskAdmin(ModelAdmin, BasePeriodicTaskAdmin):
    list_display = ('name', 'task', 'interval', 'crontab', 'enabled', 'last_run_at', 'total_run_count')
    list_filter = ('enabled', 'task', 'interval', 'crontab', 'solar')
    search_fields = ('name', 'task')
    
    list_fullwidth = True
    compressed_fields = True
    warn_unsaved_form = True


@admin.register(IntervalSchedule)
class IntervalScheduleAdmin(ModelAdmin):
    list_display = ('every', 'period')
    list_fullwidth = True


@admin.register(CrontabSchedule)
class CrontabScheduleAdmin(ModelAdmin, BaseCrontabScheduleAdmin):
    list_display = ('__str__', 'minute', 'hour', 'day_of_week', 'day_of_month', 'month_of_year')
    list_fullwidth = True


@admin.register(SolarSchedule)
class SolarScheduleAdmin(ModelAdmin):
    list_display = ('event', 'latitude', 'longitude')
    list_fullwidth = True


@admin.register(ClockedSchedule)
class ClockedScheduleAdmin(ModelAdmin, BaseClockedScheduleAdmin):
    list_display = ('clocked_time',)
    list_fullwidth = True