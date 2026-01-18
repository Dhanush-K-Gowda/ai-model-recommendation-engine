from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Q

from engine.models import Recommendation, AIModel, Provider


class Command(BaseCommand):
    help = 'Deactivate recommendations that point to deprecated models or deprecated providers'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deactivated without making changes'
        )

    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made'))
            self.stdout.write('')
        
        # Define allowed providers (OpenAI, Claude/Anthropic, Gemini/Google)
        allowed_provider_names = {
            'open-ai', 'openai', 'azure-openai', 'azure',
            'anthropic',
            'google', 'vertex-ai'
        }
        
        # Find recommendations pointing to deprecated models
        deprecated_model_recs = Recommendation.objects.filter(
            is_active=True,
            recommended_model__is_deprecated=True
        ).select_related('recommended_model', 'recommended_model__provider')
        
        # Find recommendations pointing to models from deprecated providers
        all_recs = Recommendation.objects.filter(
            is_active=True
        ).select_related('recommended_model', 'recommended_model__provider')
        
        deprecated_provider_recs = []
        for rec in all_recs:
            provider_key = rec.recommended_model.provider.name.lower()
            provider_slug = rec.recommended_model.provider.slug.lower()
            if provider_key not in allowed_provider_names and provider_slug not in allowed_provider_names:
                deprecated_provider_recs.append(rec)
        
        # Combine and deduplicate
        all_deprecated_recs = set(list(deprecated_model_recs) + deprecated_provider_recs)
        
        self.stdout.write(f'Total active recommendations: {Recommendation.objects.filter(is_active=True).count()}')
        self.stdout.write(f'Recommendations pointing to deprecated models: {deprecated_model_recs.count()}')
        self.stdout.write(f'Recommendations pointing to deprecated providers: {len(deprecated_provider_recs)}')
        self.stdout.write(f'Total recommendations to deactivate: {len(all_deprecated_recs)}')
        self.stdout.write('')
        
        if all_deprecated_recs:
            self.stdout.write('Sample recommendations to deactivate:')
            for rec in list(all_deprecated_recs)[:10]:
                self.stdout.write(
                    f'  - {rec.recommended_model.name} ({rec.recommended_model.provider.name}) - '
                    f'deprecated={rec.recommended_model.is_deprecated}'
                )
            if len(all_deprecated_recs) > 10:
                self.stdout.write(f'  ... and {len(all_deprecated_recs) - 10} more')
            self.stdout.write('')
        
        # Deactivate recommendations
        if not dry_run and all_deprecated_recs:
            with transaction.atomic():
                rec_ids = [rec.id for rec in all_deprecated_recs]
                updated = Recommendation.objects.filter(id__in=rec_ids).update(is_active=False)
                self.stdout.write(self.style.SUCCESS(f'Deactivated {updated} recommendations'))
        elif dry_run:
            self.stdout.write(self.style.WARNING(f'[DRY RUN] Would deactivate {len(all_deprecated_recs)} recommendations'))
        else:
            self.stdout.write(self.style.SUCCESS('No recommendations to deactivate'))

