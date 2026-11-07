"""Category shortcuts shared by the dashboard and worker search."""
SERVICE_CATEGORIES = [
    {'slug': 'plumbing', 'label': 'Plumbing', 'icon': '⌁', 'terms': ['plumb', 'pipe']},
    {'slug': 'electrical', 'label': 'Electrical', 'icon': 'ϟ', 'terms': ['electric', 'wiring']},
    {'slug': 'cleaning', 'label': 'Cleaning', 'icon': '✧', 'terms': ['clean', 'housekeep']},
    {'slug': 'carpentry', 'label': 'Carpentry', 'icon': '⌂', 'terms': ['carpent', 'woodwork']},
    {'slug': 'tutoring', 'label': 'Tutoring', 'icon': '▤', 'terms': ['tutor', 'teach']},
    {'slug': 'aircon', 'label': 'Aircon repair', 'icon': '❄', 'terms': ['aircon', 'air condition', 'hvac']},
    {'slug': 'catering', 'label': 'Catering', 'icon': '♧', 'terms': ['cater', 'cook', 'food']},
    {'slug': 'digital', 'label': 'Digital services', 'icon': '▧', 'terms': ['digital', 'graphic', 'virtual assist', 'design']},
]




def service_categories():
    from accounts.models import SkillCategory
    if not SkillCategory.objects.exists():
        return SERVICE_CATEGORIES  # Keep discovery usable while admins set up the catalog.
    legacy = {item['slug']: item for item in SERVICE_CATEGORIES}
    return [{'slug': c.slug, 'label': c.name, 'icon': legacy.get(c.slug, {}).get('icon', '✦'),
             'terms': legacy.get(c.slug, {}).get('terms', [c.name])}
            for c in SkillCategory.objects.all()]
