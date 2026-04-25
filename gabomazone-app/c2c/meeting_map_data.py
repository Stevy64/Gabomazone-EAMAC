"""
Données carte « point de rencontre » partagées entre l’espace utilisateur (commande C2C)
et l’admin (ex. SafeZone) — une seule logique d’agrégation pour la maintenance.
"""
from collections import defaultdict

from .models import C2COrder, PlatformSettings, SafeZone


def get_popular_meeting_min_uses():
    """Seuil minimal d’occurrences pour afficher un lieu populaire (config admin)."""
    try:
        platform_settings = PlatformSettings.get_active_settings()
        cfg_val = int(getattr(platform_settings, 'popular_meeting_min_uses', 2) or 2)
        return max(2, min(cfg_val, 50))
    except Exception:
        return 2


def _zone_to_geo_dict(z):
    return {
        'id': z.id,
        'name': z.name,
        'address': z.address,
        'city': z.city,
        'landmark': z.landmark or '',
        'opening_hours': z.opening_hours or '',
        'is_featured': z.is_featured,
        'latitude': float(z.latitude) if z.latitude is not None else None,
        'longitude': float(z.longitude) if z.longitude is not None else None,
    }


def get_safe_zones_models_and_geo(limit=50):
    """Une requête : instances pour les templates + dicts pour Leaflet."""
    zones = list(
        SafeZone.objects.filter(status=SafeZone.ACTIVE)
        .order_by('-is_featured', 'city', 'name')[:limit]
    )
    return zones, [_zone_to_geo_dict(z) for z in zones]


def build_safe_zones_geo(limit=50):
    """Zones Gabomazone actives pour Leaflet uniquement (sans réutiliser le queryset)."""
    _, geo = get_safe_zones_models_and_geo(limit=limit)
    return geo


def build_popular_points_geo(popular_min_uses=None, max_points=25, sample_orders=1200):
    """
    Lieux populaires dérivés des points personnalisés des commandes (même logique que order_detail).
    """
    if popular_min_uses is None:
        popular_min_uses = get_popular_meeting_min_uses()

    custom_points = C2COrder.objects.filter(
        meeting_type=C2COrder.MEETING_CUSTOM,
        meeting_latitude__isnull=False,
        meeting_longitude__isnull=False,
        status__in=[
            C2COrder.PAID,
            C2COrder.PENDING_DELIVERY,
            C2COrder.DELIVERED,
            C2COrder.VERIFIED,
            C2COrder.COMPLETED,
        ],
    ).exclude(meeting_address__isnull=True).exclude(meeting_address='').order_by('-id')[:sample_orders]

    buckets = defaultdict(list)
    for p in custom_points:
        try:
            lat = float(p.meeting_latitude)
            lng = float(p.meeting_longitude)
        except (TypeError, ValueError):
            continue
        if not (-90 <= lat <= 90 and -180 <= lng <= 180):
            continue
        key = (round(lat, 3), round(lng, 3))
        buckets[key].append({
            'lat': lat,
            'lng': lng,
            'address': (p.meeting_address or '').strip(),
        })

    popular_points_geo = []
    idx = 1
    for _, pts in sorted(buckets.items(), key=lambda kv: len(kv[1]), reverse=True):
        count = len(pts)
        if count < popular_min_uses:
            continue
        lat = sum(x['lat'] for x in pts) / count
        lng = sum(x['lng'] for x in pts) / count
        address_counts = defaultdict(int)
        for x in pts:
            if x['address']:
                address_counts[x['address']] += 1
        top_address = max(address_counts, key=address_counts.get) if address_counts else 'Lieu populaire'
        popular_points_geo.append({
            'id': idx,
            'name': f'Lieu populaire #{idx}',
            'address': top_address[:300],
            'usage_count': count,
            'latitude': lat,
            'longitude': lng,
        })
        idx += 1
        if len(popular_points_geo) >= max_points:
            break

    return popular_points_geo


def get_meeting_map_geo_bundle(safe_zone_limit=50):
    """
    Retourne les deux listes JSON-ready pour json_script / API.
    """
    popular_min = get_popular_meeting_min_uses()
    return {
        'safe_zones_geo_json': build_safe_zones_geo(limit=safe_zone_limit),
        'popular_points_geo_json': build_popular_points_geo(popular_min_uses=popular_min),
    }


def get_admin_safezone_map_context(safe_zone_limit=50):
    """Contexte template admin (carte = même données que l’espace utilisateur)."""
    bundle = get_meeting_map_geo_bundle(safe_zone_limit=safe_zone_limit)
    return {
        'safe_zones_geo_json': bundle['safe_zones_geo_json'],
        'popular_points_geo_json': bundle['popular_points_geo_json'],
    }
