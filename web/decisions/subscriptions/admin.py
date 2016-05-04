from django.contrib import admin

from decisions.subscriptions.models import UserProfile, Subscription, SubscriptionHit

class UserProfileAdmin(admin.ModelAdmin):
    pass

class SubscriptionAdmin(admin.ModelAdmin):
    pass

class SubscriptionHitAdmin(admin.ModelAdmin):
    pass

admin.site.register(UserProfile, UserProfileAdmin)
admin.site.register(Subscription, SubscriptionAdmin)
admin.site.register(SubscriptionHit, SubscriptionHitAdmin)
