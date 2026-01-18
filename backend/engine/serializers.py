from rest_framework import serializers
from decimal import Decimal
from django.utils import timezone
from datetime import datetime

from engine.models import Application, LLMTrace, AIModel
from engine.services.model_resolver import ModelResolver


class TraceIngestionSerializer(serializers.Serializer):
    """
    Serializer for ingesting LLM trace data.
    Accepts prompt, response, model name, tokens, cost, latency from user input.
    """
    application_id = serializers.CharField(
        required=True,
        help_text="Unique identifier for the application/service"
    )
    prompt = serializers.CharField(
        required=True,
        allow_blank=True,
        help_text="The input prompt sent to the model"
    )
    response = serializers.CharField(
        required=True,
        allow_blank=True,
        help_text="The response from the model"
    )
    model_name = serializers.CharField(
        required=True,
        help_text="Name of the model used (e.g., 'gpt-4o', 'claude-3-opus')"
    )

    # Token counts
    input_token_count = serializers.IntegerField(
        required=False,
        min_value=0,
        help_text="Number of input tokens (will be estimated if not provided)"
    )
    output_token_count = serializers.IntegerField(
        required=False,
        min_value=0,
        help_text="Number of output tokens (will be estimated if not provided)"
    )
    total_token_count = serializers.IntegerField(
        required=False,
        min_value=0,
        help_text="Total tokens (will be calculated if not provided)"
    )

    # Cost information
    input_cost = serializers.DecimalField(
        required=False,
        max_digits=12,
        decimal_places=10,
        min_value=0,
        help_text="Cost for input tokens in USD"
    )
    output_cost = serializers.DecimalField(
        required=False,
        max_digits=12,
        decimal_places=10,
        min_value=0,
        help_text="Cost for output tokens in USD"
    )
    total_cost = serializers.DecimalField(
        required=False,
        max_digits=12,
        decimal_places=10,
        min_value=0,
        help_text="Total cost in USD (will be calculated if not provided)"
    )

    # Performance metrics
    latency_sec = serializers.FloatField(
        required=False,
        min_value=0,
        help_text="Latency in seconds"
    )
    latency_ms = serializers.FloatField(
        required=False,
        min_value=0,
        help_text="Latency in milliseconds (will be converted to seconds)"
    )

    # Metadata
    external_id = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="External ID for this trace (e.g., from your system)"
    )
    category = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Category/type of the prompt (e.g., 'coding', 'chat', 'content_creation')"
    )
    tool_used = serializers.BooleanField(
        required=False,
        default=False,
        help_text="Whether tools/function calling was used"
    )
    status = serializers.CharField(
        required=False,
        default='success',
        help_text="Status of the request (e.g., 'success', 'error', 'timeout')"
    )
    traced_at = serializers.DateTimeField(
        required=False,
        help_text="Timestamp when the trace occurred (defaults to now)"
    )

    def validate(self, attrs):
        """Validate and normalize the data."""
        # Convert latency_ms to latency_sec if provided
        if 'latency_ms' in attrs and 'latency_sec' not in attrs:
            attrs['latency_sec'] = attrs.pop('latency_ms') / 1000.0
        elif 'latency_ms' in attrs:
            # If both provided, prefer latency_sec
            attrs.pop('latency_ms')

        # Calculate total_token_count if not provided
        if 'total_token_count' not in attrs or not attrs.get('total_token_count'):
            input_tokens = attrs.get('input_token_count', 0)
            output_tokens = attrs.get('output_token_count', 0)
            if input_tokens or output_tokens:
                attrs['total_token_count'] = input_tokens + output_tokens

        # Calculate total_cost if not provided
        if 'total_cost' not in attrs or not attrs.get('total_cost'):
            input_cost = attrs.get('input_cost', Decimal('0'))
            output_cost = attrs.get('output_cost', Decimal('0'))
            if input_cost or output_cost:
                attrs['total_cost'] = input_cost + output_cost

        # Set default traced_at if not provided
        if 'traced_at' not in attrs or not attrs.get('traced_at'):
            attrs['traced_at'] = timezone.now()

        return attrs

    def estimate_tokens(self, text: str) -> int:
        """
        Simple token estimation: ~4 characters per token.
        This is a rough estimate; in production, you might want to use tiktoken or similar.
        """
        if not text:
            return 0
        return max(1, len(text) // 4)

    def create(self, validated_data):
        """Create LLMTrace instance from validated data."""
        application_id = validated_data['application_id']
        model_name = validated_data['model_name']

        # Get or create application
        application, _ = Application.objects.get_or_create(
            application_id=application_id,
            defaults={'name': application_id}
        )

        # Resolve model name to AIModel (optional, can be None)
        resolved_model = ModelResolver.resolve(model_name)

        # Estimate tokens if not provided
        input_tokens = validated_data.get('input_token_count')
        output_tokens = validated_data.get('output_token_count')

        if not input_tokens:
            input_tokens = self.estimate_tokens(validated_data.get('prompt', ''))

        if not output_tokens:
            output_tokens = self.estimate_tokens(validated_data.get('response', ''))

        total_tokens = validated_data.get('total_token_count', input_tokens + output_tokens)

        # Calculate costs if not provided and we have pricing
        input_cost = validated_data.get('input_cost', Decimal('0'))
        output_cost = validated_data.get('output_cost', Decimal('0'))
        total_cost = validated_data.get('total_cost', Decimal('0'))

        # If we have a resolved model with pricing, calculate costs if not provided
        if resolved_model and hasattr(resolved_model, 'pricing') and resolved_model.pricing:
            pricing = resolved_model.pricing
            if not input_cost and input_tokens:
                input_cost = Decimal(str(input_tokens)) * pricing.request_token_price / Decimal('1000000')
            if not output_cost and output_tokens:
                output_cost = Decimal(str(output_tokens)) * pricing.response_token_price / Decimal('1000000')
            if not total_cost:
                total_cost = input_cost + output_cost

        # Create trace
        trace = LLMTrace.objects.create(
            application=application,
            external_id=validated_data.get('external_id', ''),
            model=resolved_model,
            raw_model_name=model_name,
            prompt=validated_data.get('prompt', ''),
            response=validated_data.get('response', ''),
            input_token_count=input_tokens,
            output_token_count=output_tokens,
            total_token_count=total_tokens,
            input_cost=input_cost,
            output_cost=output_cost,
            total_cost=total_cost,
            estimated_latency_sec=validated_data.get('latency_sec'),
            tool_used=validated_data.get('tool_used', False),
            status=validated_data.get('status', 'success'),
            category=validated_data.get('category', ''),
            traced_at=validated_data.get('traced_at', timezone.now()),
        )

        return trace


class TraceBulkIngestionSerializer(serializers.Serializer):
    """
    Serializer for bulk ingesting multiple LLM traces at once.
    """
    traces = TraceIngestionSerializer(many=True, required=True)

    def create(self, validated_data):
        """Create multiple LLMTrace instances."""
        traces_data = validated_data['traces']
        created_traces = []

        for trace_data in traces_data:
            serializer = TraceIngestionSerializer(data=trace_data)
            if serializer.is_valid():
                trace = serializer.save()
                created_traces.append(trace)
            else:
                # Log validation errors but continue processing
                # In production, you might want to collect errors and return them
                pass

        return created_traces
