import csv
from datetime import datetime
from decimal import Decimal
from pathlib import Path

from django.core.management.base import BaseCommand
from django.utils import timezone

from engine.models import Application, LLMTrace
from engine.services.model_resolver import ModelResolver


class Command(BaseCommand):
    help = 'Import LLM traces from CSV file'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help='Path to CSV file')
        parser.add_argument(
            '--clear', action='store_true',
            help='Clear all existing traces before import'
        )

    def handle(self, *args, **options):
        csv_path = Path(options['csv_file'])
        if not csv_path.exists():
            self.stderr.write(self.style.ERROR(f'File not found: {csv_path}'))
            return

        if options['clear']:
            deleted, _ = LLMTrace.objects.all().delete()
            self.stdout.write(f'Deleted {deleted} existing traces')

        # Read CSV and collect unique model names and application IDs
        rows = []
        model_names = set()
        app_ids = set()

        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                rows.append(row)
                model_names.add(row.get('model_name', ''))
                app_ids.add(row.get('application_id', ''))

        self.stdout.write(f'Read {len(rows)} rows from CSV')
        self.stdout.write(f'Found {len(app_ids)} unique applications')
        self.stdout.write(f'Found {len(model_names)} unique model names')

        # Create applications
        apps_created = 0
        for app_id in app_ids:
            if app_id:
                _, created = Application.objects.get_or_create(
                    application_id=app_id
                )
                if created:
                    apps_created += 1
        self.stdout.write(f'Created {apps_created} new applications')

        # Pre-fetch applications
        app_map = {
            app.application_id: app
            for app in Application.objects.filter(application_id__in=app_ids)
        }

        # Pre-resolve model names
        resolved_models = ModelResolver.bulk_resolve(list(model_names))
        resolved_count = sum(1 for v in resolved_models.values() if v is not None)
        self.stdout.write(f'Resolved {resolved_count}/{len(model_names)} model names to AIModel records')

        # Import traces
        traces = []
        now = timezone.now()

        for row in rows:
            app_id = row.get('application_id', '')
            if not app_id or app_id not in app_map:
                continue

            raw_model_name = row.get('model_name', '')
            resolved_model = resolved_models.get(raw_model_name)

            # Parse tool_used
            tool_used_str = row.get('toolused', '').strip().lower()
            tool_used = tool_used_str == 'true'

            # Parse numeric fields safely
            def safe_int(val, default=0):
                try:
                    return int(val) if val else default
                except (ValueError, TypeError):
                    return default

            def safe_float(val, default=None):
                try:
                    return float(val) if val else default
                except (ValueError, TypeError):
                    return default

            def safe_decimal(val, default='0'):
                try:
                    return Decimal(val) if val else Decimal(default)
                except (ValueError, TypeError):
                    return Decimal(default)

            trace = LLMTrace(
                application=app_map[app_id],
                external_id=row.get('id', ''),
                model=resolved_model,
                raw_model_name=raw_model_name,
                prompt=row.get('prompt', ''),
                response=row.get('response', ''),
                input_token_count=safe_int(row.get('input_token_count')),
                output_token_count=safe_int(row.get('output_token_count')),
                total_token_count=safe_int(row.get('token_count')),
                tool_used=tool_used,
                status=row.get('status_code', 'success'),
                category=row.get('category', ''),
                estimated_latency_sec=safe_float(row.get('estimated_latency_sec')),
                input_cost=safe_decimal(row.get('input_cost')),
                output_cost=safe_decimal(row.get('output_cost')),
                total_cost=safe_decimal(row.get('total_cost')),
                traced_at=now,  # Use import time; adjust if CSV has timestamps
            )
            traces.append(trace)

        # Bulk create
        LLMTrace.objects.bulk_create(traces, batch_size=500)
        self.stdout.write(self.style.SUCCESS(f'Imported {len(traces)} traces'))
