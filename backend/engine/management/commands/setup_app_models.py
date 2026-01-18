from django.core.management.base import BaseCommand
from django.db import transaction

from engine.models import Application, AIModel, LLMTrace
from engine.services.model_resolver import ModelResolver


class Command(BaseCommand):
    help = 'Create or update 6 applications (app_1 through app_6) with their assigned models. Use --update-traces to also update existing traces to use the assigned model names.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without making changes'
        )
        parser.add_argument(
            '--update-traces',
            action='store_true',
            help='Update traces to use assigned model names'
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']

        # Define app to model mappings
        app_model_mappings = {
            'app_1': 'gpt-5.1-chat-latest',
            'app_2': 'gpt-4o-latest',
            'app_3': 'gpt-5.2-pro',
            'app_4': 'claude-opus-4-0',
            'app_5': 'claude-opus-4-1',
            'app_6': 'gpt-5.1-chat-latest',
        }

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made'))
            self.stdout.write('')

        apps_created = 0
        apps_updated = 0
        traces_updated = 0
        errors = []

        with transaction.atomic():
            for app_id, model_name in app_model_mappings.items():
                # Resolve model by name using ModelResolver (handles exact match, alias, partial match)
                model = ModelResolver.resolve(model_name)
                
                # If ModelResolver doesn't find it, try direct lookup as fallback
                if not model:
                    try:
                        model = AIModel.objects.get(name=model_name)
                    except AIModel.DoesNotExist:
                        try:
                            model = AIModel.objects.get(slug=model_name)
                        except AIModel.DoesNotExist:
                            error_msg = f"Model '{model_name}' not found for {app_id}"
                            errors.append(error_msg)
                            self.stderr.write(self.style.ERROR(error_msg))
                            continue

                # Create or update application
                app, created = Application.objects.update_or_create(
                    application_id=app_id,
                    defaults={
                        'name': f'Application {app_id.replace("_", " ").title()}',
                        'assigned_model': model,
                        'is_active': True,
                    }
                )

                if created:
                    apps_created += 1
                    action = 'Created'
                else:
                    apps_updated += 1
                    action = 'Updated'

                if not dry_run:
                    self.stdout.write(
                        f"{action} {app_id} -> {model.name} "
                        f"({model.provider.name})"
                    )
                else:
                    self.stdout.write(
                        f"[DRY RUN] Would {action.lower()} {app_id} -> {model.name} "
                        f"({model.provider.name})"
                    )

                # Update traces if requested
                if options['update_traces'] and not dry_run:
                    trace_count = LLMTrace.objects.filter(application=app).update(
                        model=model,
                        raw_model_name=model.name
                    )
                    if trace_count > 0:
                        traces_updated += trace_count
                        self.stdout.write(
                            f"  Updated {trace_count} trace(s) to use {model.name}"
                        )
                elif options['update_traces'] and dry_run:
                    trace_count = LLMTrace.objects.filter(application=app).count()
                    if trace_count > 0:
                        self.stdout.write(
                            f"  [DRY RUN] Would update {trace_count} trace(s) to use {model.name}"
                        )

            if dry_run:
                # Rollback transaction in dry-run mode
                transaction.set_rollback(True)

        # Summary
        self.stdout.write('')
        summary_lines = [
            f'\nSetup complete!',
            f'  Applications created: {apps_created}',
            f'  Applications updated: {apps_updated}',
        ]
        if options['update_traces']:
            summary_lines.append(f'  Traces updated: {traces_updated}')
        summary_lines.append(f'  Errors: {len(errors)}')
        
        self.stdout.write(self.style.SUCCESS('\n'.join(summary_lines)))

        if errors:
            self.stdout.write('')
            self.stderr.write(self.style.ERROR('Errors encountered:'))
            for error in errors:
                self.stderr.write(self.style.ERROR(f'  - {error}'))
            return

        if not dry_run:
            self.stdout.write('')
            self.stdout.write('All applications have been set up successfully!')

