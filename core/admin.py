from django.contrib import admin
from .models import SiteSettings, Currency, DeliveryTracking, DeliveryTrackingHistory, AdvertisingBanner


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    fieldsets = (
        ('Branding', {
            'fields': ('site_name', 'site_tagline', 'logo', 'favicon')
        }),
        ('Banner/Hero Section', {
            'fields': ('banner_image', 'banner_title', 'banner_subtitle',
                       'banner_video', 'banner_video_url', 'show_video_on_homepage')
        }),
        ('Contact Information', {
            'fields': ('contact_email', 'contact_phone', 'contact_address', 'whatsapp_number')
        }),
        ('Social Media', {
            'fields': ('facebook_url', 'twitter_url', 'instagram_url', 'linkedin_url')
        }),
        ('Business Settings', {
            'fields': ('tax_rate', 'standard_delivery_cost', 'express_delivery_cost',
                       'free_delivery_threshold')
        }),
    )

    def has_add_permission(self, request):
        # Only allow one instance
        return not SiteSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Currency)
class CurrencyAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'symbol', 'exchange_rate', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('code', 'name')
    list_editable = ('exchange_rate', 'is_active')


class DeliveryTrackingHistoryInline(admin.TabularInline):
    model = DeliveryTrackingHistory
    extra = 0
    readonly_fields = ('recorded_at',)


@admin.register(DeliveryTracking)
class DeliveryTrackingAdmin(admin.ModelAdmin):
    list_display = ('order', 'status', 'driver_name', 'estimated_delivery', 'updated_at')
    list_filter = ('status',)
    search_fields = ('order__id', 'driver_name', 'vehicle_number')
    raw_id_fields = ('order',)
    inlines = [DeliveryTrackingHistoryInline]

    fieldsets = (
        ('Order Information', {
            'fields': ('order', 'status')
        }),
        ('Driver Information', {
            'fields': ('driver_name', 'driver_phone', 'vehicle_number')
        }),
        ('GPS Location', {
            'fields': (('current_latitude', 'current_longitude'),
                       ('destination_latitude', 'destination_longitude'))
        }),
        ('Timing', {
            'fields': ('estimated_delivery', 'picked_up_at', 'delivered_at')
        }),
        ('Notes', {
            'fields': ('notes',)
        }),
    )


@admin.register(AdvertisingBanner)
class AdvertisingBannerAdmin(admin.ModelAdmin):
    list_display = ('title', 'position', 'is_active', 'display_order', 'start_date', 'end_date')
    list_filter = ('is_active', 'position')
    list_editable = ('is_active', 'display_order')
    search_fields = ('title',)
