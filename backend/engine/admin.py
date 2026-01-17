from django.contrib import admin
from .models import (
    Provider, AIModel, Pricing,
    Application, LLMTrace, UsageAnalysis, Recommendation, ModelNameAlias
)


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


# ============================================================================
# Recommendation Engine Admin
# ============================================================================

@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ['application_id', 'name', 'is_active', 'trace_count', 'created_at']
    list_filter = ['is_active']
    search_fields = ['application_id', 'name']
    readonly_fields = ['created_at', 'updated_at']

    def trace_count(self, obj):
        return obj.traces.count()
    trace_count.short_description = 'Traces'


@admin.register(LLMTrace)
class LLMTraceAdmin(admin.ModelAdmin):
    list_display = [
        'external_id', 'application', 'raw_model_name', 'status',
        'total_token_count', 'total_cost', 'tool_used', 'traced_at'
    ]
    list_filter = ['status', 'tool_used', 'category', 'application']
    search_fields = ['external_id', 'raw_model_name', 'application__application_id']
    readonly_fields = ['created_at']
    raw_id_fields = ['application', 'model']
    date_hierarchy = 'traced_at'


@admin.register(UsageAnalysis)
class UsageAnalysisAdmin(admin.ModelAdmin):
    list_display = [
        'application', 'raw_model_name', 'total_requests',
        'max_total_tokens', 'avg_cost_per_request', 'requires_tools',
        'analysis_period_end'
    ]
    list_filter = ['requires_tools', 'application']
    search_fields = ['application__application_id', 'raw_model_name']
    readonly_fields = ['created_at', 'updated_at']
    raw_id_fields = ['application', 'model']


@admin.register(Recommendation)
class RecommendationAdmin(admin.ModelAdmin):
    list_display = [
        'application', 'current_model_name', 'recommended_model',
        'recommendation_type', 'estimated_cost_savings_percent',
        'confidence_score', 'is_active', 'created_at'
    ]
    list_filter = ['recommendation_type', 'is_active', 'is_dismissed', 'application']
    search_fields = [
        'application__application_id', 'current_model_name',
        'recommended_model__name'
    ]
    readonly_fields = ['created_at']
    raw_id_fields = ['application', 'usage_analysis', 'recommended_model']


@admin.register(ModelNameAlias)
class ModelNameAliasAdmin(admin.ModelAdmin):
    list_display = ['alias', 'canonical_model', 'created_at']
    search_fields = ['alias', 'canonical_model__name']
    raw_id_fields = ['canonical_model']
