from django import template

register = template.Library()

@register.simple_tag
def smart_page_range(page_obj, paginator, delta=2):
    current = page_obj.number
    total = paginator.num_pages

    # Handle edge cases
    if total <= 1:
        return [1] if total == 1 else []

    # First two pages
    first_pages = [1, 2] if total >= 2 else [1]
    # Last two pages
    last_pages = [total - 1, total] if total > 2 else [total] if total == 2 else []
    # Middle pages: pages around current page, bounded inside [3, total]
    left = max(current - delta, 3)
    right = min(current + delta, total)
    middle_pages = list(range(left, right + 1)) if left <= right else []

    pages = []
    # Add first pages
    pages.extend(first_pages)

    # Add ellipsis between first pages and middle pages
    if middle_pages and middle_pages[0] - first_pages[-1] > 1:
        pages.append('...')

    # Add middle pages
    pages.extend(middle_pages)

    # Add last pages without ellipsis
    if last_pages:
        if current not in last_pages:
            pages.append('..')
        # Only add last pages that are not already in middle_pages
        for page in last_pages:
            if page not in middle_pages:
                pages.append(page)

    # Remove duplicates while preserving order
    seen = set()
    result = []
    for p in pages:
        if p not in seen:
            result.append(p)
            seen.add(p)
    
    return result