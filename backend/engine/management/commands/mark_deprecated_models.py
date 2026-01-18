from django.core.management.base import BaseCommand
from django.db import transaction

from engine.models import AIModel, Provider


class Command(BaseCommand):
    help = 'Mark models as deprecated manually'

    def add_arguments(self, parser):
        parser.add_argument(
            '--model',
            type=str,
            help='Mark specific model as deprecated (by name or slug)'
        )
        parser.add_argument(
            '--provider',
            type=str,
            help='Mark all models for a provider as deprecated'
        )
        parser.add_argument(
            '--unmark',
            action='store_true',
            help='Unmark models (set is_deprecated=False instead of True)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be marked without making changes'
        )

    def handle(self, *args, **options):
        model_name = options.get('model')
        provider_name = options.get('provider')
        unmark = options.get('unmark', False)
        dry_run = options.get('dry_run', False)
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made'))
            self.stdout.write('')
        
        action = 'unmark' if unmark else 'mark as deprecated'
        updated_count = 0
        
        with transaction.atomic():
            if model_name:
                # Mark specific model
                from django.db.models import Q
                try:
                    model = AIModel.objects.filter(
                        Q(name__iexact=model_name) | Q(slug__iexact=model_name)
                    ).first()
                    if not model:
                        self.stderr.write(self.style.ERROR(f"Model not found: {model_name}"))
                        return
                except Exception as e:
                    self.stderr.write(self.style.ERROR(f"Error finding model: {str(e)}"))
                    return
                
                if model.is_deprecated != (not unmark):
                    if not dry_run:
                        model.is_deprecated = not unmark
                        model.save(update_fields=['is_deprecated'])
                    self.stdout.write(
                        f"{'[DRY RUN] Would' if dry_run else ''} {action} "
                        f"{model.name} ({model.provider.name})"
                    )
                    updated_count += 1
                else:
                    self.stdout.write(
                        f"Model {model.name} is already "
                        f"{'not deprecated' if unmark else 'deprecated'}"
                    )
            
            elif provider_name:
                # Mark all models for a provider
                try:
                    provider = Provider.objects.get(name__iexact=provider_name)
                except Provider.DoesNotExist:
                    try:
                        provider = Provider.objects.get(slug__iexact=provider_name)
                    except Provider.DoesNotExist:
                        self.stderr.write(self.style.ERROR(f"Provider not found: {provider_name}"))
                        return
                
                models = AIModel.objects.filter(provider=provider)
                self.stdout.write(f"Found {models.count()} models for provider: {provider.name}")
                
                for model in models:
                    if model.is_deprecated != (not unmark):
                        if not dry_run:
                            model.is_deprecated = not unmark
                            model.save(update_fields=['is_deprecated'])
                        self.stdout.write(
                            f"{'[DRY RUN] Would' if dry_run else ''} {action} "
                            f"{model.name}"
                        )
                        updated_count += 1
            
            else:
                self.stderr.write(self.style.ERROR(
                    "Please specify --model <model_name> or --provider <provider_name>"
                ))
                return
        
        self.stdout.write(self.style.SUCCESS(
            f'\n{"Would update" if dry_run else "Updated"} {updated_count} models'
        ))

