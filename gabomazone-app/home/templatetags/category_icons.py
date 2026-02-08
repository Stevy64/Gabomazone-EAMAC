from django import template

register = template.Library()

@register.filter
def category_icon(category_name):
    """
    Retourne l'icône appropriée selon le nom de la catégorie
    """
    if not category_name:
        return 'fi-rs-apps'
    
    name_lower = category_name.lower()
    
    # Mapping des catégories aux icônes
    icon_map = {
        # Électronique
        'électronique': 'fi-rs-laptop',
        'electronique': 'fi-rs-laptop',
        'électroniques': 'fi-rs-laptop',
        'electroniques': 'fi-rs-laptop',
        'tech': 'fi-rs-laptop',
        'technologie': 'fi-rs-laptop',
        'informatique': 'fi-rs-laptop',
        'ordinateur': 'fi-rs-laptop',
        'smartphone': 'fi-rs-smartphone',
        'mobile': 'fi-rs-smartphone',
        'téléphone': 'fi-rs-smartphone',
        'telephone': 'fi-rs-smartphone',
        
        # Mode et Vêtements
        'mode': 'fi-rs-shopping-bag',
        'vêtements': 'fi-rs-shopping-bag',
        'vetements': 'fi-rs-shopping-bag',
        'fashion': 'fi-rs-shopping-bag',
        'habillement': 'fi-rs-shopping-bag',
        'textile': 'fi-rs-shopping-bag',
        'mode et vêtements': 'fi-rs-shopping-bag',
        'mode et vetements': 'fi-rs-shopping-bag',
        
        # Immobilier
        'immobilier': 'fi-rs-building',
        'immobiliers': 'fi-rs-building',
        'maison': 'fi-rs-home',
        'appartement': 'fi-rs-home',
        'logement': 'fi-rs-home',
        'propriété': 'fi-rs-building',
        'propriete': 'fi-rs-building',
        
        # Fournitures Scolaires
        'fournitures scolaires': 'fi-rs-book',
        'fournitures': 'fi-rs-book',
        'scolaire': 'fi-rs-graduation-cap',
        'scolaires': 'fi-rs-graduation-cap',
        'école': 'fi-rs-school',
        'ecole': 'fi-rs-school',
        'éducation': 'fi-rs-graduation-cap',
        'education': 'fi-rs-graduation-cap',
        'livre': 'fi-rs-book',
        'livres': 'fi-rs-book',
        'cahier': 'fi-rs-notebook',
        'papeterie': 'fi-rs-book',
        
        # Loisirs
        'loisirs': 'fi-rs-heart',
        'loisir': 'fi-rs-heart',
        'sport': 'fi-rs-basketball',
        'sports': 'fi-rs-basketball',
        'divertissement': 'fi-rs-music',
        'jeux': 'fi-rs-playing-cards',
        'jeu': 'fi-rs-playing-cards',
        'musique': 'fi-rs-music',
        'hobby': 'fi-rs-heart',
        'hobbies': 'fi-rs-heart',
        
        # Services
        'services': 'fi-rs-briefcase',
        'service': 'fi-rs-briefcase',
        'services et autres': 'fi-rs-settings',
        'services et autres': 'fi-rs-settings',
        'autre': 'fi-rs-box',
        'autres': 'fi-rs-box',
        'divers': 'fi-rs-box',
        
        # Autres catégories communes
        'alimentaire': 'fi-rs-shopping-bag',
        'nourriture': 'fi-rs-shopping-bag',
        'beauté': 'fi-rs-spa',
        'beaute': 'fi-rs-spa',
        'santé': 'fi-rs-heart',
        'sante': 'fi-rs-heart',
        'automobile': 'fi-rs-settings',
        'voiture': 'fi-rs-settings',
        'jardin': 'fi-rs-home',
        'bricolage': 'fi-rs-settings',
        'outils': 'fi-rs-settings',
    }
    
    # Recherche exacte d'abord
    if name_lower in icon_map:
        return icon_map[name_lower]
    
    # Recherche partielle
    for key, icon in icon_map.items():
        if key in name_lower or name_lower in key:
            return icon
    
    # Par défaut
    return 'fi-rs-apps'


@register.filter
def condition_slug(value):
    """
    Convertit la valeur d'état C2C en slug pour les classes CSS (ex. 'BON ETAT' -> 'bon_etat').
    """
    if not value:
        return ''
    return str(value).lower().replace(' ', '_')

