from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from engine.models import Application, Recommendation
from engine.services.model_tester import test_recommendation


class Command(BaseCommand):
    help = 'Test top 5 recommendations per application by running real prompts through models'

    def add_arguments(self, parser):
        parser.add_argument(
            '--app',
            type=str,
            help='Test recommendations for specific application (application_id)'
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Test recommendations for all applications'
        )
        parser.add_argument(
            '--sample-size',
            type=int,
            default=20,
            help='Number of prompts to test (default: 20)'
        )
        parser.add_argument(
            '--skip-quality',
            action='store_true',
            help='Skip LLM-as-judge quality evaluation (faster testing)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be tested without making changes'
        )

    def handle(self, *args, **options):
        app_id = options.get('app')
        test_all = options.get('all', False)
        sample_size = options.get('sample_size', 20)
        evaluate_quality = not options.get('skip_quality', False)
        dry_run = options.get('dry_run', False)
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made'))
            self.stdout.write('')
        
        # Determine applications to test
        if app_id:
            applications = Application.objects.filter(application_id=app_id)
            if not applications.exists():
                self.stderr.write(self.style.ERROR(f"Application not found: {app_id}"))
                return
        elif test_all:
            applications = Application.objects.filter(is_active=True)
        else:
            self.stderr.write(self.style.ERROR(
                "Please specify --app <application_id> or --all"
            ))
            return
        
        total_tested = 0
        total_completed = 0
        total_failed = 0
        
        for app in applications:
            self.stdout.write(f'\n{"="*80}')
            self.stdout.write(f'Testing recommendations for: {app.application_id}')
            self.stdout.write(f'{"="*80}')
            
            # Get top 5 active recommendations for this application
            recommendations = Recommendation.objects.filter(
                application=app,
                is_active=True
            ).order_by('-confidence_score')[:5]
            
            if not recommendations.exists():
                self.stdout.write(self.style.WARNING(
                    f'  No active recommendations found for {app.application_id}'
                ))
                continue
            
            self.stdout.write(f'  Found {recommendations.count()} recommendations to test\n')
            
            for idx, rec in enumerate(recommendations, 1):
                self.stdout.write(
                    f'  [{idx}/{recommendations.count()}] Testing: '
                    f'{rec.current_model_name} -> {rec.recommended_model.name}'
                )
                
                if dry_run:
                    self.stdout.write(f'    [DRY RUN] Would test with {sample_size} prompts')
                    continue
                
                # Update status to pending
                rec.test_status = 'pending'
                rec.save(update_fields=['test_status'])
                
                try:
                    # Run tests
                    test_results = test_recommendation(
                        rec,
                        sample_size=sample_size,
                        evaluate_quality=evaluate_quality
                    )
                    
                    if test_results['status'] == 'completed':
                        # Update recommendation with test results
                        rec.test_status = 'completed'
                        rec.test_samples_count = test_results['test_samples_count']
                        rec.test_completed_at = timezone.now()
                        rec.actual_avg_latency_sec = test_results['actual_avg_latency_sec']
                        rec.actual_avg_cost_per_request = test_results['actual_avg_cost_per_request']
                        rec.actual_success_rate = test_results['actual_success_rate']
                        rec.quality_scores = test_results['quality_scores']
                        rec.quality_overall_score = test_results['quality_overall_score']
                        rec.quality_comparison = test_results['quality_comparison']
                        rec.latency_comparison_pct = test_results['latency_comparison_pct']
                        rec.cost_comparison_pct = test_results['cost_comparison_pct']
                        rec.test_error_message = ''
                        
                        rec.save()
                        
                        total_completed += 1
                        
                        # Display results
                        self.stdout.write(self.style.SUCCESS(
                            f'    ✓ Completed - '
                            f'Latency: {test_results["actual_avg_latency_sec"]:.3f}s '
                            f'({test_results["latency_comparison_pct"]:+.1f}%), '
                            f'Cost: ${test_results["actual_avg_cost_per_request"]:.6f} '
                            f'({test_results["cost_comparison_pct"]:+.1f}%), '
                            f'Success: {test_results["actual_success_rate"]:.1f}%'
                        ))
                        
                        if test_results['quality_overall_score']:
                            self.stdout.write(
                                f'    Quality Score: {test_results["quality_overall_score"]:.2f}/10'
                            )
                    else:
                        # Test failed
                        rec.test_status = 'failed'
                        rec.test_error_message = test_results.get('error', 'Unknown error')
                        rec.save()
                        
                        total_failed += 1
                        self.stdout.write(self.style.ERROR(
                            f'    ✗ Failed: {test_results.get("error", "Unknown error")}'
                        ))
                        
                except Exception as e:
                    rec.test_status = 'failed'
                    rec.test_error_message = str(e)[:500]
                    rec.save()
                    
                    total_failed += 1
                    self.stdout.write(self.style.ERROR(
                        f'    ✗ Error: {str(e)[:100]}'
                    ))
                
                total_tested += 1
        
        # Summary
        self.stdout.write(f'\n{"="*80}')
        self.stdout.write(self.style.SUCCESS(
            f'Testing Complete! Tested: {total_tested}, '
            f'Completed: {total_completed}, Failed: {total_failed}'
        ))
        self.stdout.write(f'{"="*80}\n')

