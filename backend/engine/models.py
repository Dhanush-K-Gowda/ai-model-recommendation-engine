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

    # JSON field for additional/uncommon capabilities
    additional_capabilities = models.JSONField(default=dict, blank=True)

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
