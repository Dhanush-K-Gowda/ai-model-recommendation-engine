import time
from django.core.management.base import BaseCommand
from django.db import transaction

from engine.models import AIModel, Provider

try:
    from duckduckgo_search import DDGS
    DDGS_AVAILABLE = True
except ImportError:
    DDGS_AVAILABLE = False
    try:
        from googlesearch import search as google_search
        GOOGLE_SEARCH_AVAILABLE = True
    except ImportError:
        GOOGLE_SEARCH_AVAILABLE = False


class Command(BaseCommand):
    help = 'Check models with categories for deprecation status via web search and mark them in database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be marked without making changes'
        )
        parser.add_argument(
            '--provider',
            type=str,
            help='Limit to specific provider (by name or slug)'
        )
        parser.add_argument(
            '--limit',
            type=int,
            help='Limit number of models to check (for testing)'
        )

    def perform_web_search(self, query, max_results=5):
        """
        Perform web search using available library.
        
        Returns list of search result dictionaries with 'title' and 'snippet' keys.
        """
        results = []
        
        if DDGS_AVAILABLE:
            try:
                with DDGS() as ddgs:
                    search_results = ddgs.text(query, max_results=max_results)
                    for result in search_results:
                        results.append({
                            'title': result.get('title', ''),
                            'snippet': result.get('body', ''),
                            'url': result.get('href', '')
                        })
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"  ⚠ DuckDuckGo search error: {str(e)}"))
        elif GOOGLE_SEARCH_AVAILABLE:
            try:
                search_results = list(google_search(query, num_results=max_results))
                # Google search returns URLs, we'd need to fetch them
                # For simplicity, just store URLs
                for url in search_results:
                    results.append({
                        'title': '',
                        'snippet': url,
                        'url': url
                    })
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"  ⚠ Google search error: {str(e)}"))
        else:
            raise ImportError(
                "No web search library available. Please install one of:\n"
                "  pip install duckduckgo-search\n"
                "  pip install googlesearch-python"
            )
        
        return results

    def is_deprecated_from_search(self, search_results):
        """
        Analyze web search results to determine if a model is deprecated.
        
        Returns True if deprecation indicators are found in search results.
        """
        if not search_results:
            return False
        
        # Combine all search result text
        combined_text = ' '.join([
            result.get('snippet', '') + ' ' + result.get('title', '') + ' ' + result.get('url', '')
            for result in search_results
        ]).lower()
        
        # Common deprecation indicators
        deprecation_keywords = [
            'deprecated',
            'discontinued',
            'no longer available',
            'sunset',
            'retired',
            'phased out',
            'removed from',
            'end of life',
            'eol',
            'legacy model',
            'obsolete',
        ]
        
        # Check for deprecation keywords
        for keyword in deprecation_keywords:
            if keyword in combined_text:
                return True
        
        return False

    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)
        provider_name = options.get('provider')
        limit = options.get('limit')
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made'))
            self.stdout.write('')
        
        # Check if web search is available
        if not DDGS_AVAILABLE and not GOOGLE_SEARCH_AVAILABLE:
            self.stderr.write(self.style.ERROR(
                "No web search library available. Please install one of:\n"
                "  pip install duckduckgo-search\n"
                "  pip install googlesearch-python"
            ))
            return
        
        # Build query for models with categories
        query = AIModel.objects.filter(categories__isnull=False, is_deprecated=False)
        
        # Filter by provider if specified
        if provider_name:
            try:
                provider = Provider.objects.get(name__iexact=provider_name)
            except Provider.DoesNotExist:
                try:
                    provider = Provider.objects.get(slug__iexact=provider_name)
                except Provider.DoesNotExist:
                    self.stderr.write(self.style.ERROR(f"Provider not found: {provider_name}"))
                    return
            query = query.filter(provider=provider)
            self.stdout.write(f'Filtering by provider: {provider.name}')
        
        # Apply limit if specified
        if limit:
            models = list(query.order_by('provider__name', 'name')[:limit])
            self.stdout.write(f'Limited to {limit} models')
        else:
            models = list(query.order_by('provider__name', 'name'))
        
        total_models = len(models)
        
        if total_models == 0:
            self.stdout.write(self.style.WARNING('No models found to check'))
            return
        
        self.stdout.write(f'Checking {total_models} models for deprecation status...\n')
        
        marked_count = 0
        error_count = 0
        
        # Process each model
        for idx, model in enumerate(models, 1):
            self.stdout.write(
                f'[{idx}/{total_models}] Checking: {model.name} ({model.provider.name})'
            )
            
            # Construct search query
            search_query = f"{model.provider.name} {model.name} deprecated"
            
            try:
                # Perform web search
                search_results = self.perform_web_search(search_query, max_results=5)
                
                # Analyze results
                is_deprecated = self.is_deprecated_from_search(search_results)
                
                if is_deprecated:
                    if not dry_run:
                        with transaction.atomic():
                            model.is_deprecated = True
                            model.save(update_fields=['is_deprecated'])
                    
                    self.stdout.write(self.style.SUCCESS(
                        f"  ✓ {'[DRY RUN] Would mark' if dry_run else 'Marked'} as deprecated"
                    ))
                    marked_count += 1
                else:
                    self.stdout.write(f"  - Not deprecated (or no clear indication found)")
                
                # Rate limiting - be respectful to search APIs
                time.sleep(1)
                    
            except Exception as e:
                error_count += 1
                self.stdout.write(self.style.ERROR(
                    f"  ✗ Error checking {model.name}: {str(e)}"
                ))
        
        # Summary
        self.stdout.write(f'\n{"="*80}')
        self.stdout.write(self.style.SUCCESS(
            f'Summary:\n'
            f'  Total checked: {total_models}\n'
            f'  {"Would mark" if dry_run else "Marked"} as deprecated: {marked_count}\n'
            f'  Errors: {error_count}'
        ))
        self.stdout.write(f'{"="*80}\n')

