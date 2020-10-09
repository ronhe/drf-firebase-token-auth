from django.contrib import admin

from . import models


@admin.register(models.FirebaseUser)
class FirebaseUserAdmin(admin.ModelAdmin):
    list_display = (
        lambda obj: obj.user.email,
        lambda obj: obj.user.first_name,
        lambda obj: obj.user.last_name,
    )
    search_fields = (
        'user__username',
        'user__email',
        'user__first_name',
        'user__last_name',
        'uid',
    )
