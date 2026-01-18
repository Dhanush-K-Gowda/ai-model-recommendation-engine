import json
from pathlib import Path
from django.core.management.base import BaseCommand
from django.db import transaction

from engine.models import AIModel


class Command(BaseCommand):
    help = 'Update model categories from JSON file based on benchmark data. Sets categories to null for models not in the file.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            default='scripts/data/model_categories.json',
            help='Path to model categories JSON file (relative to project root)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be updated without making changes'
        )
        parser.add_argument(
            '--set-null',
            action='store_true',
            default=True,
            help='Set categories to null for models not in JSON file (default: True)'
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        set_null = options['set_null']
        json_file_path = options['file']
        
        # Get project root (parent of backend directory)
        project_root = Path(__file__).resolve().parent.parent.parent.parent.parent
        json_file = project_root / json_file_path

        if not json_file.exists():
            self.stderr.write(self.style.ERROR(f'File not found: {json_file}'))
            return

        with open(json_file, 'r') as f:
            category_data = json.load(f)

        updated_count = 0
        nullified_count = 0
        not_found = []
        multiple_matches = []
        processed_model_ids = set()

        with transaction.atomic():
            # First, update models that are in the JSON file
            for model_name, data in category_data.items():
                categories = data.get('categories', [])
                
                # Find matching models
                models = self.find_models_by_name(model_name)
                
                if not models:
                    not_found.append(model_name)
                    continue
                
                if len(models) > 1:
                    multiple_matches.append((model_name, len(models)))

                for model in models:
                    processed_model_ids.add(model.id)
                    
                    if not dry_run:
                        # Set categories (empty list becomes null)
                        if categories:
                            model.categories = sorted(list(set(categories)))  # Remove duplicates and sort
                        else:
                            model.categories = None
                        model.save(update_fields=['categories'])
                    
                    action = 'Updated' if not dry_run else '[DRY RUN] Would update'
                    categories_display = categories if categories else 'null'
                    self.stdout.write(
                        f"{action} {model.name} ({model.provider.name}): {categories_display}"
                    )
                    updated_count += 1

            # Then, set categories to null for models not in the JSON file
            if set_null:
                all_models = AIModel.objects.all()
                models_to_nullify = all_models.exclude(id__in=processed_model_ids)
                
                for model in models_to_nullify:
                    if not dry_run:
                        model.categories = None
                        model.save(update_fields=['categories'])
                    
                    action = 'Set to null' if not dry_run else '[DRY RUN] Would set to null'
                    self.stdout.write(
                        f"{action} {model.name} ({model.provider.name}): null (not in JSON file)"
                    )
                    nullified_count += 1

        self.stdout.write(self.style.SUCCESS(
            f'\n{"Would update" if dry_run else "Updated"} {updated_count} models with categories'
        ))
        
        if set_null:
            self.stdout.write(self.style.SUCCESS(
                f'{"Would set" if dry_run else "Set"} {nullified_count} models to null (not in JSON file)'
            ))

        if not_found:
            self.stdout.write(self.style.WARNING(
                f'\n{len(not_found)} models from JSON not found in database: {", ".join(not_found[:20])}'
                f'{f" (and {len(not_found) - 20} more)" if len(not_found) > 20 else ""}'
            ))

        if multiple_matches:
            self.stdout.write(self.style.WARNING(
                f'\n{len(multiple_matches)} models had multiple matches (all were updated):'
            ))
            for name, count in multiple_matches[:10]:
                self.stdout.write(f'  - {name}: {count} matches')

    def find_models_by_name(self, benchmark_model_name: str):
        """Find AIModel instances that match a benchmark model name."""
        normalized = benchmark_model_name.lower().strip()
        
        # Try exact match first
        models = list(AIModel.objects.filter(name__iexact=normalized))
        
        # Try partial match
        if not models:
            models = list(AIModel.objects.filter(name__icontains=normalized))
        
        # Try slug match
        if not models:
            slug_normalized = normalized.replace(' ', '-').replace('_', '-')
            models = list(AIModel.objects.filter(slug__icontains=slug_normalized))
        
        return models

