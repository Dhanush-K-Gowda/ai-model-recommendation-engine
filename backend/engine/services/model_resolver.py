from typing import Optional, List, Dict
from django.db.models import Q

from engine.models import AIModel, ModelNameAlias


class ModelResolver:
    """
    Resolves raw model names from traces to canonical AIModel entries.
    Uses multiple strategies: exact match, alias lookup, partial match.
    """

    @classmethod
    def resolve(cls, raw_name: str) -> Optional[AIModel]:
        """
        Resolve a raw model name to an AIModel.
        Returns None if no match found.
        """
        if not raw_name:
            return None

        raw_name_lower = raw_name.lower().strip()

        # 1. Check alias table first (fastest for known mappings)
        alias = ModelNameAlias.objects.filter(alias__iexact=raw_name_lower).first()
        if alias:
            return alias.canonical_model

        # 2. Try exact match on name or slug
        model = AIModel.objects.filter(
            Q(name__iexact=raw_name_lower) | Q(slug__iexact=raw_name_lower)
        ).first()
        if model:
            return model

        # 3. Try partial match (name contains raw_name)
        model = AIModel.objects.filter(
            Q(name__icontains=raw_name_lower) | Q(slug__icontains=raw_name_lower)
        ).order_by('name').first()

        return model

    @classmethod
    def bulk_resolve(cls, raw_names: List[str]) -> Dict[str, Optional[AIModel]]:
        """
        Efficiently resolve multiple names.
        Returns dict mapping raw_name -> AIModel or None
        """
        results = {}
        unique_names = set(name.lower().strip() for name in raw_names if name)

        # Pre-fetch all aliases for these names
        aliases = ModelNameAlias.objects.filter(
            alias__in=unique_names
        ).select_related('canonical_model')
        alias_map = {a.alias.lower(): a.canonical_model for a in aliases}

        # Pre-fetch all models that might match
        all_models = AIModel.objects.filter(
            Q(name__in=unique_names) | Q(slug__in=unique_names)
        )
        exact_match_map = {}
        for model in all_models:
            exact_match_map[model.name.lower()] = model
            exact_match_map[model.slug.lower()] = model

        # Resolve each name
        for raw_name in raw_names:
            if not raw_name:
                results[raw_name] = None
                continue

            name_lower = raw_name.lower().strip()

            # Check alias first
            if name_lower in alias_map:
                results[raw_name] = alias_map[name_lower]
            # Then exact match
            elif name_lower in exact_match_map:
                results[raw_name] = exact_match_map[name_lower]
            else:
                # Fall back to individual resolution for partial matches
                results[raw_name] = cls.resolve(raw_name)

        return results

    @classmethod
    def create_alias(cls, alias: str, model: AIModel) -> ModelNameAlias:
        """
        Create a new alias mapping.
        """
        return ModelNameAlias.objects.create(
            alias=alias.lower().strip(),
            canonical_model=model
        )
