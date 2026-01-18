from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Q

from engine.models import AIModel, Provider


class Command(BaseCommand):
    help = 'Mark all vendors (providers) except OpenAI, Claude, and Gemini as deprecated'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be marked without making changes'
        )
        parser.add_argument(
            '--unmark',
            action='store_true',
            help='Unmark vendors (set is_deprecated=False instead of True)'
        )

    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)
        unmark = options.get('unmark', False)
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made'))
            self.stdout.write('')
        
        # Define the vendors to keep (case-insensitive matching)
        # OpenAI variations: open-ai, openai, azure-openai
        # Anthropic/Claude: anthropic
        # Google/Gemini: google, vertex-ai
        keep_vendors = {
            'open-ai', 'openai', 'azure-openai', 'azure',
            'anthropic',
            'google', 'vertex-ai'
        }
        
        # Get all providers
        all_providers = Provider.objects.all()
        
        # Find providers to mark as deprecated (those NOT in keep_vendors)
        providers_to_deprecate = []
        providers_to_keep = []
        
        for provider in all_providers:
            # Check both name and slug (case-insensitive)
            provider_key = provider.name.lower()
            provider_slug = provider.slug.lower()
            
            if provider_key in keep_vendors or provider_slug in keep_vendors:
                providers_to_keep.append(provider)
            else:
                providers_to_deprecate.append(provider)
        
        # Display summary
        self.stdout.write(f'Total providers found: {all_providers.count()}')
        self.stdout.write(f'Providers to keep (not deprecated): {len(providers_to_keep)}')
        self.stdout.write(f'Providers to {"unmark" if unmark else "mark as deprecated"}: {len(providers_to_deprecate)}')
        self.stdout.write('')
        
        if providers_to_keep:
            self.stdout.write(self.style.SUCCESS('Providers to keep:'))
            for provider in providers_to_keep:
                self.stdout.write(f'  - {provider.name} (slug: {provider.slug})')
            self.stdout.write('')
        
        if providers_to_deprecate:
            self.stdout.write(self.style.WARNING('Providers to {}:'.format('unmark' if unmark else 'mark as deprecated')))
            for provider in providers_to_deprecate:
                self.stdout.write(f'  - {provider.name} (slug: {provider.slug})')
            self.stdout.write('')
        
        # Mark models as deprecated
        action = 'unmark' if unmark else 'mark as deprecated'
        updated_count = 0
        
        with transaction.atomic():
            for provider in providers_to_deprecate:
                models = AIModel.objects.filter(provider=provider)
                self.stdout.write(f'Processing {provider.name}: {models.count()} models')
                
                for model in models:
                    if model.is_deprecated != (not unmark):
                        if not dry_run:
                            model.is_deprecated = not unmark
                            model.save(update_fields=['is_deprecated'])
                        updated_count += 1
                        if updated_count <= 10:  # Show first 10 as examples
                            self.stdout.write(
                                f"  {'[DRY RUN] Would' if dry_run else ''} {action} "
                                f"{model.name}"
                            )
                
                if models.count() > 10:
                    self.stdout.write(f'  ... and {models.count() - 10} more models')
        
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(
            f'\n{"Would update" if dry_run else "Updated"} {updated_count} models across {len(providers_to_deprecate)} providers'
        ))

