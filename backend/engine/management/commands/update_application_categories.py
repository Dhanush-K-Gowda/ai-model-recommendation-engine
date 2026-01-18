from django.core.management.base import BaseCommand
from django.db import transaction

from engine.models import Application


def select_categories(model_categories):
    """
    Select 1-2 categories from model's categories.
    Excludes 'general' if possible, but uses it if it's the only category.
    """
    if not model_categories:
        return ['general']
    
    # Filter out 'general'
    filtered = [cat for cat in model_categories if cat != 'general']
    
    if not filtered:
        # All were 'general', use it
        return ['general']
    elif len(filtered) == 1:
        return filtered[:1]
    else:
        # Take first 2
        return filtered[:2]


class Command(BaseCommand):
    help = 'Update application categories from assigned_model categories (selects 1-2 categories)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be updated without making changes'
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        updated_count = 0
        skipped_count = 0
        no_model_count = 0
        no_categories_count = 0
        
        with transaction.atomic():
            for app in Application.objects.all().select_related('assigned_model'):
                if not app.assigned_model:
                    # No assigned model, set to general
                    if not dry_run:
                        app.categories = ['general']
                        app.save(update_fields=['categories'])
                    self.stdout.write(
                        f"{'[DRY RUN] Would update' if dry_run else 'Updated'} "
                        f"{app.application_id}: ['general'] (no assigned_model)"
                    )
                    updated_count += 1
                    no_model_count += 1
                    continue
                
                model = app.assigned_model
                model_categories = model.categories
                
                if not model_categories:
                    # Model has no categories, set to general
                    if not dry_run:
                        app.categories = ['general']
                        app.save(update_fields=['categories'])
                    self.stdout.write(
                        f"{'[DRY RUN] Would update' if dry_run else 'Updated'} "
                        f"{app.application_id}: ['general'] (model {model.name} has no categories)"
                    )
                    updated_count += 1
                    no_categories_count += 1
                    continue
                
                # Select 1-2 categories from model's categories
                selected_categories = select_categories(model_categories)
                
                # Check if categories need updating
                current_categories = sorted(app.categories or [])
                new_categories = sorted(selected_categories)
                
                if current_categories == new_categories:
                    # Already up to date
                    skipped_count += 1
                    continue
                
                if not dry_run:
                    app.categories = selected_categories
                    app.save(update_fields=['categories'])
                
                self.stdout.write(
                    f"{'[DRY RUN] Would update' if dry_run else 'Updated'} "
                    f"{app.application_id}: {selected_categories} "
                    f"(from model {model.name}: {model_categories})"
                )
                updated_count += 1

        self.stdout.write(self.style.SUCCESS(
            f'\n{"Would update" if dry_run else "Updated"} {updated_count} applications'
        ))
        
        if skipped_count > 0:
            self.stdout.write(self.style.WARNING(
                f'Skipped {skipped_count} applications (already up to date)'
            ))
        
        if no_model_count > 0:
            self.stdout.write(
                f'  - {no_model_count} applications without assigned_model (set to ["general"])'
            )
        
        if no_categories_count > 0:
            self.stdout.write(
                f'  - {no_categories_count} applications with models that have no categories (set to ["general"])'
            )

