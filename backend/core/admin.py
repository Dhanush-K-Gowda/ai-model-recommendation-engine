from django.contrib import admin
from .models import Provider, AIModel, Pricing


class PricingInline(admin.TabularInline):
    model = Pricing
    extra = 0


@admin.register(Provider)
class ProviderAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'is_active', 'model_count', 'created_at']
    list_filter = ['is_active']
    search_fields = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}

    def model_count(self, obj):
        return obj.models.count()
    model_count.short_description = 'Models'


@admin.register(AIModel)
class AIModelAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'provider', 'model_type', 'context_window',
        'has_reasoning', 'supports_image_input', 'supports_tools', 'is_active'
    ]
    list_filter = [
        'provider', 'model_type', 'is_active',
        'has_reasoning', 'supports_image_input', 'supports_tools',
        'supports_audio', 'supports_cache_control'
    ]
    search_fields = ['name', 'slug', 'provider__name']
    prepopulated_fields = {'slug': ('name',)}
    inlines = [PricingInline]
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Pricing)
class PricingAdmin(admin.ModelAdmin):
    list_display = [
        'model', 'currency', 'request_token_price', 'response_token_price',
        'cache_read_input_token_price'
    ]
    list_filter = ['currency', 'model__provider']
    search_fields = ['model__name', 'model__provider__name']
