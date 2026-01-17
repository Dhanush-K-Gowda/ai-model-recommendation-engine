import json
import os
from decimal import Decimal
from pathlib import Path

from django.core.management.base import BaseCommand
from django.utils.text import slugify

from engine.models import Provider, AIModel, Pricing


class Command(BaseCommand):
    help = 'Import AI models and pricing data from JSON files'

    def add_arguments(self, parser):
        parser.add_argument(
            '--general-dir',
            type=str,
            default='scripts/data/general',
            help='Path to general model data directory (relative to project root)'
        )
        parser.add_argument(
            '--pricing-dir',
            type=str,
            default='scripts/data/pricing',
            help='Path to pricing data directory (relative to project root)'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before import'
        )

    def handle(self, *args, **options):
        # Get project root (parent of backend directory)
        project_root = Path(__file__).resolve().parent.parent.parent.parent.parent

        general_dir = project_root / options['general_dir']
        pricing_dir = project_root / options['pricing_dir']

        if not general_dir.exists():
            self.stderr.write(self.style.ERROR(f'General data directory not found: {general_dir}'))
            return

        if options['clear']:
            self.stdout.write('Clearing existing data...')
            Pricing.objects.all().delete()
            AIModel.objects.all().delete()
            Provider.objects.all().delete()

        # Load all pricing data first (keyed by provider name)
        pricing_data = {}
        if pricing_dir.exists():
            for pricing_file in pricing_dir.glob('*.json'):
                provider_name = pricing_file.stem
                with open(pricing_file, 'r') as f:
                    pricing_data[provider_name] = json.load(f)
                self.stdout.write(f'Loaded pricing: {provider_name}')

        # Process general model data
        providers_created = 0
        models_created = 0
        pricing_created = 0

        for general_file in general_dir.glob('*.json'):
            with open(general_file, 'r') as f:
                data = json.load(f)

            provider_name = data.get('name', general_file.stem)
            provider_slug = slugify(provider_name)

            # Create or update provider
            provider, created = Provider.objects.update_or_create(
                slug=provider_slug,
                defaults={
                    'name': provider_name,
                    'description': data.get('description', ''),
                    'default_params': data.get('default', {}),
                }
            )
            if created:
                providers_created += 1
                self.stdout.write(f'Created provider: {provider_name}')

            # Get default config for this provider
            default_config = data.get('default', {})
            default_type = default_config.get('type', {})
            default_supported = default_type.get('supported', [])

            # Get pricing data for this provider
            provider_pricing = pricing_data.get(provider_name, {})
            default_pricing = provider_pricing.get('default', {}).get('pricing_config', {})

            # Process each model (keys that aren't metadata)
            metadata_keys = {'name', 'description', 'default'}
            for model_name, model_data in data.items():
                if model_name in metadata_keys:
                    continue

                if not isinstance(model_data, dict):
                    continue

                # Extract model type (can be dict or string)
                model_type_data = model_data.get('type', default_type)
                if isinstance(model_type_data, str):
                    primary_type = model_type_data
                    supported = default_supported
                else:
                    primary_type = model_type_data.get('primary', 'chat')
                    supported = model_type_data.get('supported', default_supported)

                # Extract max_tokens from params
                context_window = None
                max_completion_tokens = None
                thinking_budget_min = None
                thinking_budget_max = None
                has_thinking_param = False

                params = model_data.get('params', [])
                for param in params:
                    key = param.get('key')
                    if key == 'max_tokens':
                        context_window = param.get('maxValue')
                    elif key == 'max_completion_tokens':
                        max_completion_tokens = param.get('maxValue')
                    elif key == 'thinking':
                        has_thinking_param = True
                        properties = param.get('properties', {})
                        budget = properties.get('budget_tokens', {})
                        thinking_budget_min = budget.get('minValue')
                        thinking_budget_max = budget.get('maxValue')

                # Map capabilities to boolean fields
                supports_image = 'image' in supported
                supports_tools = 'tools' in supported
                supports_audio = 'audio' in supported
                supports_pdf = 'pdf' in supported
                supports_doc = 'doc' in supported
                supports_cache = 'cache_control' in supported or 'cache_control' in default_supported
                has_reasoning = has_thinking_param

                # Collect additional capabilities not in standard fields
                standard_caps = {'image', 'tools', 'audio', 'pdf', 'doc', 'cache_control'}
                additional_caps = {cap: True for cap in supported if cap not in standard_caps}

                # Create or update model
                model_slug = slugify(model_name)
                ai_model, created = AIModel.objects.update_or_create(
                    provider=provider,
                    name=model_name,
                    defaults={
                        'slug': model_slug,
                        'display_name': model_name,
                        'model_type': primary_type,
                        'context_window': context_window,
                        'max_completion_tokens': max_completion_tokens,
                        'supports_image_input': supports_image,
                        'supports_tools': supports_tools,
                        'supports_audio': supports_audio,
                        'supports_pdf': supports_pdf,
                        'supports_doc': supports_doc,
                        'has_reasoning': has_reasoning,
                        'supports_cache_control': supports_cache,
                        'additional_capabilities': additional_caps,
                        'parameter_config': model_data,
                        'thinking_budget_min': thinking_budget_min,
                        'thinking_budget_max': thinking_budget_max,
                        'is_default': model_data.get('isDefault', False),
                    }
                )
                if created:
                    models_created += 1

                # Extract pricing for this model
                model_pricing = provider_pricing.get(model_name, {}).get('pricing_config', {})
                pay_as_you_go = model_pricing.get('pay_as_you_go', {})

                # Fall back to default pricing if no model-specific pricing
                if not pay_as_you_go:
                    pay_as_you_go = default_pricing.get('pay_as_you_go', {})

                # Extract token prices (convert to Decimal for precision)
                request_price = Decimal(str(pay_as_you_go.get('request_token', {}).get('price', 0)))
                response_price = Decimal(str(pay_as_you_go.get('response_token', {}).get('price', 0)))
                cache_write_price = Decimal(str(pay_as_you_go.get('cache_write_input_token', {}).get('price', 0)))
                cache_read_price = Decimal(str(pay_as_you_go.get('cache_read_input_token', {}).get('price', 0)))

                # Audio pricing (optional)
                request_audio = pay_as_you_go.get('request_audio_token', {}).get('price')
                response_audio = pay_as_you_go.get('response_audio_token', {}).get('price')

                # Additional units (web_search, etc.)
                additional_units = {}
                for key, value in pay_as_you_go.get('additional_units', {}).items():
                    if isinstance(value, dict) and 'price' in value:
                        additional_units[key] = value['price']

                # Create or update pricing
                pricing_obj, created = Pricing.objects.update_or_create(
                    model=ai_model,
                    defaults={
                        'currency': model_pricing.get('currency', default_pricing.get('currency', 'USD')),
                        'request_token_price': request_price,
                        'response_token_price': response_price,
                        'cache_write_input_token_price': cache_write_price,
                        'cache_read_input_token_price': cache_read_price,
                        'request_audio_token_price': Decimal(str(request_audio)) if request_audio else None,
                        'response_audio_token_price': Decimal(str(response_audio)) if response_audio else None,
                        'additional_units': additional_units,
                    }
                )
                if created:
                    pricing_created += 1

        self.stdout.write(self.style.SUCCESS(
            f'\nImport complete!\n'
            f'  Providers: {providers_created} created\n'
            f'  Models: {models_created} created\n'
            f'  Pricing: {pricing_created} created'
        ))

        # Print summary stats
        self.stdout.write(f'\nTotal in database:')
        self.stdout.write(f'  Providers: {Provider.objects.count()}')
        self.stdout.write(f'  Models: {AIModel.objects.count()}')
        self.stdout.write(f'  - with reasoning: {AIModel.objects.filter(has_reasoning=True).count()}')
        self.stdout.write(f'  - with image support: {AIModel.objects.filter(supports_image_input=True).count()}')
        self.stdout.write(f'  - with tools support: {AIModel.objects.filter(supports_tools=True).count()}')
        self.stdout.write(f'  Pricing entries: {Pricing.objects.count()}')
