from django.db import models
from django.core.validators import MinValueValidator


class Provider(models.Model):
    """
    Represents an AI model provider (e.g., OpenAI, Anthropic, Google).
    One provider has multiple models.
    """
    name = models.CharField(max_length=100, unique=True, db_index=True)
    slug = models.SlugField(max_length=100, unique=True, db_index=True)
    description = models.TextField(blank=True, default="")
    default_params = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class ModelType(models.TextChoices):
    CHAT = 'chat', 'Chat'
    TEXT = 'text', 'Text Completion'
    EMBEDDING = 'embedding', 'Embedding'
    AUDIO = 'audio', 'Audio'
    IMAGE = 'image', 'Image Generation'
    MODERATION = 'moderation', 'Moderation'


class ApplicationCategory(models.TextChoices):
    """
    Real-world use case categories for LLM applications.
    Based on common production patterns and industry standards.
    """
    GENERAL = 'general', 'General Purpose'
    CODING = 'coding', 'Code Generation & Development'
    CODE_REVIEW = 'code_review', 'Code Review & Analysis'
    DOCUMENTATION = 'documentation', 'Technical Documentation'
    CUSTOMER_SUPPORT = 'customer_support', 'Customer Support & Helpdesk'
    CHATBOT = 'chatbot', 'Conversational AI & Chatbots'
    FAQ = 'faq', 'FAQ & Knowledge Base'
    CONTENT_CREATION = 'content_creation', 'Content Writing & Blogging'
    MARKETING = 'marketing', 'Marketing Copy & Campaigns'
    SOCIAL_MEDIA = 'social_media', 'Social Media Content'
    EMAIL = 'email', 'Email Composition & Responses'
    DATA_ANALYSIS = 'data_analysis', 'Data Analysis & Insights'
    BUSINESS_INTELLIGENCE = 'business_intelligence', 'Business Intelligence'
    REPORTING = 'reporting', 'Report Generation'
    FINANCE = 'finance', 'Financial Analysis & Trading'
    ACCOUNTING = 'accounting', 'Accounting & Bookkeeping'
    RISK_ASSESSMENT = 'risk_assessment', 'Risk Analysis'
    HEALTHCARE = 'healthcare', 'Healthcare & Medical'
    CLINICAL = 'clinical', 'Clinical Documentation'
    RESEARCH = 'research', 'Medical Research'
    LEGAL = 'legal', 'Legal Research & Analysis'
    COMPLIANCE = 'compliance', 'Compliance & Regulatory'
    CONTRACT = 'contract', 'Contract Analysis'
    EDUCATION = 'education', 'Education & E-Learning'
    TUTORING = 'tutoring', 'Tutoring & Learning Assistant'
    TRAINING = 'training', 'Corporate Training'
    SALES = 'sales', 'Sales & Lead Generation'
    CRM = 'crm', 'CRM & Customer Management'
    TRANSLATION = 'translation', 'Translation & Localization'
    MULTILINGUAL = 'multilingual', 'Multilingual Support'
    SEARCH = 'search', 'Search & Information Retrieval'
    RAG = 'rag', 'RAG (Retrieval Augmented Generation)'
    CREATIVE = 'creative', 'Creative Writing & Storytelling'
    MEDIA = 'media', 'Media & Entertainment'
    MODERATION = 'moderation', 'Content Moderation'
    SECURITY = 'security', 'Security & Threat Detection'
    ECOMMERCE = 'ecommerce', 'E-commerce & Product Descriptions'
    RECOMMENDATION = 'recommendation', 'Product Recommendations'
    HR = 'hr', 'Human Resources & Recruiting'
    RECRUITMENT = 'recruitment', 'Recruitment & Screening'
    REASONING = 'reasoning', 'Advanced Reasoning & Problem Solving'
    OTHER = 'other', 'Other / Custom Use Case'


class AIModel(models.Model):
    """
    Represents a specific AI model offered by a provider.
    """
    provider = models.ForeignKey(
        Provider,
        on_delete=models.CASCADE,
        related_name='models',
        db_index=True
    )

    name = models.CharField(max_length=200, db_index=True)
    slug = models.SlugField(max_length=200, db_index=True)
    display_name = models.CharField(max_length=200, blank=True)
    description = models.TextField(blank=True, default="")

    model_type = models.CharField(
        max_length=20,
        choices=ModelType.choices,
        default=ModelType.CHAT,
        db_index=True
    )

    # Context window / max tokens
    context_window = models.PositiveIntegerField(
        null=True,
        blank=True,
        db_index=True,
        help_text="Maximum output tokens (max_tokens parameter)"
    )
    max_completion_tokens = models.PositiveIntegerField(
        null=True,
        blank=True,
        db_index=True,
        help_text="Maximum completion tokens (for reasoning models)"
    )

    # Capabilities - indexed boolean fields for fast queries
    supports_image_input = models.BooleanField(default=False, db_index=True)
    supports_tools = models.BooleanField(default=False, db_index=True)
    supports_audio = models.BooleanField(default=False, db_index=True)
    supports_pdf = models.BooleanField(default=False, db_index=True)
    supports_doc = models.BooleanField(default=False, db_index=True)
    has_reasoning = models.BooleanField(default=False, db_index=True)
    supports_cache_control = models.BooleanField(default=False, db_index=True)
    
    # Status flags
    is_deprecated = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Model has been deprecated by the provider and is no longer available"
    )

    # JSON field for additional/uncommon capabilities
    additional_capabilities = models.JSONField(default=dict, blank=True)

    # Categories - models can belong to multiple categories
    categories = models.JSONField(
        null=True,
        blank=True,
        help_text="List of categories this model is suitable for (e.g., ['coding', 'general', 'finance'])",
        db_index=True
    )

    # Full parameter configuration
    parameter_config = models.JSONField(default=dict, blank=True)

    # Thinking/Reasoning budget (for reasoning models)
    thinking_budget_min = models.PositiveIntegerField(null=True, blank=True)
    thinking_budget_max = models.PositiveIntegerField(null=True, blank=True)

    # Metadata
    is_active = models.BooleanField(default=True, db_index=True)
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['provider', 'name']
        unique_together = [['provider', 'name']]
        indexes = [
            models.Index(fields=['model_type', 'is_active'], name='idx_model_type_active'),
            models.Index(fields=['context_window', 'is_active'], name='idx_context_active'),
            models.Index(fields=['has_reasoning', 'is_active'], name='idx_reasoning_active'),
            models.Index(fields=['provider', 'model_type'], name='idx_provider_type'),
            models.Index(
                fields=['supports_image_input', 'supports_tools', 'has_reasoning'],
                name='idx_capabilities'
            ),
        ]

    def __str__(self):
        return f"{self.provider.name} - {self.name}"

    @property
    def effective_max_tokens(self):
        return self.max_completion_tokens or self.context_window


class Pricing(models.Model):
    """
    Pricing information for a model.
    All prices are per 1 million tokens.
    """
    model = models.OneToOneField(
        AIModel,
        on_delete=models.CASCADE,
        related_name='pricing',
        primary_key=True
    )

    currency = models.CharField(max_length=3, default='USD')

    # Text token pricing (per 1M tokens)
    request_token_price = models.DecimalField(
        max_digits=12,
        decimal_places=8,
        default=0,
        validators=[MinValueValidator(0)],
        db_index=True,
        help_text="Price per 1M input tokens"
    )
    response_token_price = models.DecimalField(
        max_digits=12,
        decimal_places=8,
        default=0,
        validators=[MinValueValidator(0)],
        db_index=True,
        help_text="Price per 1M output tokens"
    )

    # Cache token pricing
    cache_write_input_token_price = models.DecimalField(
        max_digits=12,
        decimal_places=8,
        default=0,
        validators=[MinValueValidator(0)]
    )
    cache_read_input_token_price = models.DecimalField(
        max_digits=12,
        decimal_places=8,
        default=0,
        validators=[MinValueValidator(0)]
    )

    # Audio token pricing
    request_audio_token_price = models.DecimalField(
        max_digits=12,
        decimal_places=8,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)]
    )
    response_audio_token_price = models.DecimalField(
        max_digits=12,
        decimal_places=8,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)]
    )

    # Image and additional pricing (JSON for flexibility)
    image_pricing = models.JSONField(default=dict, blank=True)
    additional_units = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Pricing"
        indexes = [
            models.Index(fields=['request_token_price'], name='idx_request_price'),
            models.Index(fields=['response_token_price'], name='idx_response_price'),
            models.Index(
                fields=['request_token_price', 'response_token_price'],
                name='idx_token_prices'
            ),
        ]

    def __str__(self):
        return f"Pricing for {self.model.name}"


# ============================================================================
# Recommendation Engine Models
# ============================================================================

class Application(models.Model):
    """
    Represents a user's service/application that uses LLM models.
    Traces are grouped by application for analysis.
    """
    application_id = models.CharField(max_length=100, unique=True, db_index=True)
    name = models.CharField(max_length=200, blank=True)
    is_active = models.BooleanField(default=True, db_index=True)
    
    # Application categories (1-2 categories derived from assigned_model)
    categories = models.JSONField(
        default=list,
        blank=True,
        help_text="List of categories this application belongs to (derived from assigned_model, 1-2 categories)",
        db_index=True
    )
    
    # Assigned model for this application
    assigned_model = models.ForeignKey(
        AIModel,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='applications',
        db_index=True,
        help_text="The primary model assigned to this application"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['application_id']

    def __str__(self):
        return self.name or self.application_id


class LLMTrace(models.Model):
    """
    Individual LLM usage trace record.
    Stores each API call with its metadata, tokens, and costs.
    """
    application = models.ForeignKey(
        Application,
        on_delete=models.CASCADE,
        related_name='traces',
        db_index=True
    )

    external_id = models.CharField(max_length=100, blank=True, db_index=True)

    # Model reference - nullable FK with raw name fallback
    model = models.ForeignKey(
        AIModel,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='traces',
        db_index=True
    )
    raw_model_name = models.CharField(max_length=200, db_index=True)

    # Request/Response content
    prompt = models.TextField(blank=True)
    response = models.TextField(blank=True)

    # Token counts
    input_token_count = models.PositiveIntegerField(default=0, db_index=True)
    output_token_count = models.PositiveIntegerField(default=0, db_index=True)
    total_token_count = models.PositiveIntegerField(default=0, db_index=True)

    # Usage metadata
    tool_used = models.BooleanField(default=False, db_index=True)
    status = models.CharField(max_length=50, default='success', db_index=True)
    category = models.CharField(max_length=50, blank=True, db_index=True)

    # Performance and cost
    estimated_latency_sec = models.FloatField(null=True, blank=True)
    input_cost = models.DecimalField(
        max_digits=12, decimal_places=10, default=0
    )
    output_cost = models.DecimalField(
        max_digits=12, decimal_places=10, default=0
    )
    total_cost = models.DecimalField(
        max_digits=12, decimal_places=10, default=0, db_index=True
    )

    # Timestamps
    traced_at = models.DateTimeField(db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-traced_at']
        indexes = [
            models.Index(fields=['application', 'raw_model_name'], name='idx_trace_app_model'),
            models.Index(fields=['application', 'traced_at'], name='idx_trace_app_date'),
            models.Index(fields=['tool_used', 'application'], name='idx_trace_tool_app'),
            models.Index(fields=['category', 'application'], name='idx_trace_cat_app'),
        ]

    def __str__(self):
        return f"{self.application.application_id} - {self.raw_model_name} @ {self.traced_at}"


class UsageAnalysis(models.Model):
    """
    Aggregated usage statistics for an application's model usage.
    Computed periodically by the analysis cron job.
    """
    application = models.ForeignKey(
        Application,
        on_delete=models.CASCADE,
        related_name='usage_analyses',
        db_index=True
    )

    # Model reference - can link to resolved AIModel or raw name
    model = models.ForeignKey(
        AIModel,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='usage_analyses'
    )
    raw_model_name = models.CharField(max_length=200, db_index=True)

    # Analysis period
    analysis_period_start = models.DateTimeField()
    analysis_period_end = models.DateTimeField()

    # Request counts
    total_requests = models.PositiveIntegerField(default=0)
    successful_requests = models.PositiveIntegerField(default=0)

    # Token statistics
    max_input_tokens = models.PositiveIntegerField(default=0)
    max_output_tokens = models.PositiveIntegerField(default=0)
    max_total_tokens = models.PositiveIntegerField(default=0, db_index=True)
    avg_input_tokens = models.FloatField(default=0)
    avg_output_tokens = models.FloatField(default=0)

    # Cost statistics
    total_cost = models.DecimalField(max_digits=14, decimal_places=10, default=0)
    avg_cost_per_request = models.DecimalField(
        max_digits=14, decimal_places=10, default=0, db_index=True
    )

    # Performance
    avg_latency_sec = models.FloatField(null=True, blank=True)

    # Capability requirements (derived from usage)
    tool_usage_percentage = models.FloatField(default=0)
    requires_tools = models.BooleanField(default=False, db_index=True)

    # Category breakdown (stored as JSON)
    category_distribution = models.JSONField(default=dict, blank=True)

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Usage Analyses"
        unique_together = [['application', 'raw_model_name', 'analysis_period_start']]
        ordering = ['-analysis_period_end']
        indexes = [
            models.Index(
                fields=['application', 'analysis_period_end'],
                name='idx_analysis_app_period'
            ),
            models.Index(
                fields=['requires_tools', 'max_total_tokens'],
                name='idx_analysis_reqs'
            ),
        ]

    def __str__(self):
        return f"{self.application.application_id} - {self.raw_model_name} analysis"


class RecommendationType(models.TextChoices):
    CHEAPER = 'cheaper', 'Cost Savings'
    FASTER = 'faster', 'Performance'
    CAPABLE = 'capable', 'Enhanced Capabilities'
    BALANCED = 'balanced', 'Balanced Improvement'


class Recommendation(models.Model):
    """
    Generated recommendation for an application to switch models.
    """
    application = models.ForeignKey(
        Application,
        on_delete=models.CASCADE,
        related_name='recommendations',
        db_index=True
    )

    # Current model usage
    usage_analysis = models.ForeignKey(
        UsageAnalysis,
        on_delete=models.CASCADE,
        related_name='recommendations'
    )
    current_model_name = models.CharField(max_length=200)

    # Recommended model
    recommended_model = models.ForeignKey(
        AIModel,
        on_delete=models.CASCADE,
        related_name='recommendations_for'
    )

    # Recommendation details
    recommendation_type = models.CharField(
        max_length=20,
        choices=RecommendationType.choices,
        default=RecommendationType.CHEAPER,
        db_index=True
    )

    # Comparison metrics
    estimated_cost_savings_percent = models.FloatField(default=0)
    estimated_monthly_savings = models.DecimalField(
        max_digits=12, decimal_places=4, default=0
    )

    # Compatibility scores
    context_window_headroom = models.FloatField(default=0)
    capability_match_score = models.FloatField(default=100)

    # Reasoning (for user display)
    reasoning = models.TextField(blank=True)

    # Confidence and status
    confidence_score = models.FloatField(default=0, db_index=True)
    is_active = models.BooleanField(default=True, db_index=True)
    is_dismissed = models.BooleanField(default=False)

    # Test results (actual performance from testing)
    test_status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('completed', 'Completed'),
            ('failed', 'Failed'),
            ('skipped', 'Skipped')
        ],
        default='pending',
        db_index=True
    )
    test_samples_count = models.PositiveIntegerField(default=0)
    test_completed_at = models.DateTimeField(null=True, blank=True)

    # Actual metrics from testing
    actual_avg_latency_sec = models.FloatField(null=True, blank=True)
    actual_avg_cost_per_request = models.DecimalField(
        max_digits=12, decimal_places=10, null=True, blank=True
    )
    actual_success_rate = models.FloatField(null=True, blank=True)

    # Quality evaluation results
    quality_scores = models.JSONField(
        default=dict, blank=True,
        help_text="Quality scores from LLM-as-judge (correctness, completeness, etc.)"
    )
    quality_overall_score = models.FloatField(null=True, blank=True)

    # Comparison metrics vs current model
    quality_comparison = models.JSONField(
        default=dict, blank=True,
        help_text="Quality comparison scores vs current model"
    )
    latency_comparison_pct = models.FloatField(null=True, blank=True)
    cost_comparison_pct = models.FloatField(null=True, blank=True)

    # Error tracking
    test_error_message = models.TextField(blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-confidence_score', '-created_at']
        indexes = [
            models.Index(
                fields=['application', 'is_active', 'confidence_score'],
                name='idx_rec_app_active_conf'
            ),
            models.Index(
                fields=['recommendation_type', 'is_active'],
                name='idx_rec_type_active'
            ),
        ]

    def __str__(self):
        return f"{self.application.application_id}: {self.current_model_name} -> {self.recommended_model.name}"


class ModelNameAlias(models.Model):
    """
    Maps various model name formats to canonical AIModel entries.
    Supports resolving trace model names to database models.
    """
    alias = models.CharField(max_length=200, unique=True, db_index=True)
    canonical_model = models.ForeignKey(
        AIModel,
        on_delete=models.CASCADE,
        related_name='aliases'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Model Name Aliases"

    def __str__(self):
        return f"{self.alias} -> {self.canonical_model.name}"
