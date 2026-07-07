import re

from django.db.models import Q

from webapp.constants import WHOLE_STRING_ONLY_SEARCH_FIELDS

MIN_CHARS_ALLOWED = 1


def query_to_tokens(query):
    return [token.lower() for token in re.split(r"[ ,-]", query) if token]


def perform_search(query, queryset=None, search_fields=None):
    if queryset is None:
        raise ValueError("Queryset cannot be None")

    if query and len(query) >= MIN_CHARS_ALLOWED and search_fields:
        # Check if query is wrapped in double quotes for exact match
        is_exact_match = (
            len(query) >= 2 and query.startswith('"') and query.endswith('"')
        )

        # Strip quotes if present for the actual search
        search_query = query[1:-1] if is_exact_match else query

        q_objects = Q()
        for field_name in search_fields:
            tokens = [search_query.lower()]
            if field_name not in WHOLE_STRING_ONLY_SEARCH_FIELDS and not is_exact_match:
                tokens.extend(query_to_tokens(search_query))

            for token in tokens:
                q_objects |= Q(**{f"{field_name}__icontains": token})

        return queryset.filter(q_objects)

    return queryset
