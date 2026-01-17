from django.core.management.base import BaseCommand

from engine.models import Application, UsageAnalysis, Recommendation
from engine.services.usage_analyzer import UsageAnalyzer
from engine.services.recommendation_engine import RecommendationEngine


class Command(BaseCommand):
    help = 'Run usage analysis and generate recommendations'

    def add_arguments(self, parser):
        parser.add_argument(
            '--app', type=str,
            help='Analyze specific application only (application_id)'
        )
        parser.add_argument(
            '--days', type=int, default=30,
            help='Analysis period in days (default: 30)'
        )
        parser.add_argument(
            '--max-recs', type=int, default=5,
            help='Max recommendations per model (default: 5)'
        )
        parser.add_argument(
            '--clear-old', action='store_true',
            help='Clear old recommendations before generating new ones'
        )

    def handle(self, *args, **options):
        analyzer = UsageAnalyzer(analysis_period_days=options['days'])
        rec_engine = RecommendationEngine()

        # Clear old recommendations if requested
        if options['clear_old']:
            deleted, _ = Recommendation.objects.filter(is_active=True).update(is_active=False)
            self.stdout.write(f'Deactivated existing recommendations')

        # Determine applications to analyze
        if options['app']:
            applications = Application.objects.filter(application_id=options['app'])
            if not applications.exists():
                self.stderr.write(self.style.ERROR(
                    f"Application not found: {options['app']}"
                ))
                return
        else:
            applications = Application.objects.filter(
                traces__isnull=False
            ).distinct()

        total_analyses = 0
        total_recommendations = 0

        for app in applications:
            self.stdout.write(f'Analyzing application: {app.application_id}')

            # Run usage analysis
            analyses = analyzer.analyze_application(app)
            total_analyses += len(analyses)
            self.stdout.write(f'  Created {len(analyses)} usage analyses')

            # Generate recommendations for each analysis
            for analysis in analyses:
                recs = rec_engine.generate_recommendations(
                    analysis,
                    max_recommendations=options['max_recs']
                )
                total_recommendations += len(recs)

                if recs:
                    self.stdout.write(
                        f'    {analysis.raw_model_name}: {len(recs)} recommendations'
                    )
                else:
                    self.stdout.write(
                        f'    {analysis.raw_model_name}: no cheaper alternatives found'
                    )

        self.stdout.write(self.style.SUCCESS(
            f'\nComplete! Analyses: {total_analyses}, Recommendations: {total_recommendations}'
        ))
