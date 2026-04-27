# Image Gallery Viewer - Documentation Complète

## 📸 Vue d'ensemble

Un **viewer d'images fullscreen élégant et moderne** style Glisser, entièrement responsive et tactile, pour un meilleur UX lors de la visualisation des produits C2C et B2C.

### Caractéristiques principales
✅ **Fullscreen** - Images en grand, immersif  
✅ **Fond sombre** - Meilleure concentration sur l'image  
✅ **Compteur** - Voir quelle image on regarde (1/5, 2/5, etc.)  
✅ **Navigation** - Flèches, clavier, swipe tactile  
✅ **Miniatures** - Accès rapide aux autres images  
✅ **Animations fluides** - Transitions professionnelles  
✅ **Responsive** - Desktop, tablette, mobile  
✅ **Performance** - GPU acceleration, gestion tactile optimisée  

---

## 🎯 Utilisation Rapide

### Pour C2C Products
**Fichier**: `accounts/templates/accounts/peer-product-details.html`

```html
<!-- Le viewer est déjà inclus et configuré -->
{% include 'components/image-gallery-viewer.html' %}

<!-- Images passées au viewer via JavaScript -->
<script>
    function initPeerProductGallery() {
        const images = [
            { url: '...', alt: 'Description' },
            // ...
        ];
        initImageGallery(images);
    }
</script>
```

**Résultat**: Cliquer sur une image → fullscreen viewer  
**Navigation**: Flèches, clavier (← →), swipe mobiles (←  →)  
**Fermer**: Bouton X, Esc, ou cliquer le fond sombre  

### Pour B2C Products
**Fichier**: `products/templates/products/shop-product-vendor.html`

Exactement la même intégration que C2C.

---

## 🛠️ Installation dans d'autres templates

Si vous voulez ajouter le viewer à une autre page:

### Step 1: Ajouter le CSS
```html
{% block headextra %}
<link rel="stylesheet" href="{% static 'gabomazone-client/css/components/image-gallery-viewer.css' %}?v=1.0" />
{% endblock headextra %}
```

### Step 2: Inclure le composant
```html
<!-- En bas du template, avant fermeture -->
{% include 'components/image-gallery-viewer.html' %}
```

### Step 3: Initialiser les images
```html
<script>
    // Préparer les images
    const images = [
        { url: 'https://...', alt: 'Image 1' },
        { url: 'https://...', alt: 'Image 2' },
        { url: 'https://...', alt: 'Image 3' },
    ];

    // Initialiser le viewer
    document.addEventListener('DOMContentLoaded', () => {
        initImageGallery(images);
    });

    // Fonction pour ouvrir le viewer
    function openMyGallery(imageUrl, index = 0) {
        openImageViewer(imageUrl, index);
    }
</script>
```

### Step 4: Ajouter click handler
```html
<!-- Cliquer sur une image pour ouvrir le viewer -->
<img src="..." onclick="openMyGallery(this.src, 0)" />
```

---

## 📱 API JavaScript

### Fonctions principales

#### `initImageGallery(images)`
Initialise le viewer avec un tableau d'images.

```javascript
initImageGallery([
    { url: 'image1.jpg', alt: 'Description 1' },
    { url: 'image2.jpg', alt: 'Description 2' },
]);
```

**Paramètres**:
- `images` (Array) - Liste des images avec structure `{ url, alt }`

---

#### `openImageViewer(imageUrl, startIndex)`
Ouvre le viewer en fullscreen à partir d'une image spécifique.

```javascript
// Ouvrir à partir de la première image
openImageViewer('https://...', 0);

// Ouvrir à partir de la 3e image
openImageViewer('https://...', 2);
```

**Paramètres**:
- `imageUrl` (String) - URL de l'image à afficher
- `startIndex` (Number, optional) - Index dans le tableau (défaut: 0)

---

#### `closeImageViewer()`
Ferme le viewer.

```javascript
closeImageViewer();
```

---

#### `nextImage()`
Affiche l'image suivante.

```javascript
nextImage(); // Ou flèche droite / swipe gauche
```

---

#### `previousImage()`
Affiche l'image précédente.

```javascript
previousImage(); // Ou flèche gauche / swipe droite
```

---

#### `goToImage(index)`
Va directement à l'image à l'index spécifié.

```javascript
goToImage(2); // Aller à la 3e image
```

---

## ⌨️ Raccourcis clavier

| Touche | Action |
|--------|--------|
| **→** | Image suivante |
| **←** | Image précédente |
| **Esc** | Fermer le viewer |

---

## 👆 Gestes tactiles

| Geste | Action |
|-------|--------|
| **Swipe gauche** | Image suivante |
| **Swipe droite** | Image précédente |
| **Tap fond** | Fermer le viewer |
| **Scroll miniatures** | Parcourir les images en bas |

---

## 🎨 Personnalisation CSS

### Personnaliser les couleurs

**Fichier**: `static/gabomazone-client/css/components/image-gallery-viewer.css`

```css
/* Modifier la transparence du fond */
.gm-image-viewer-backdrop {
    background: rgba(0, 0, 0, 0.95); /* De 0.95 à 0.98 pour plus sombre */
}

/* Modifier la couleur des boutons */
.gm-image-viewer-nav {
    background: rgba(255, 255, 255, 0.1);
    border-color: rgba(255, 255, 255, 0.2);
}

.gm-image-viewer-nav:hover {
    background: rgba(255, 255, 255, 0.25); /* Plus clair au survol */
}

/* Modifier l'accent des miniatures actives */
.gm-image-viewer-thumbnail.active {
    border-color: #FFD700; /* Couleur or au lieu de blanc */
    box-shadow: 0 0 12px rgba(255, 215, 0, 0.4);
}
```

### Modifier les tailles

```css
/* Buttons de navigation plus grands */
.gm-image-viewer-nav {
    width: 60px;  /* Au lieu de 50px */
    height: 60px;
}

/* Miniatures plus petites */
.gm-image-viewer-thumbnail {
    width: 55px;  /* Au lieu de 70px */
    height: 55px;
}

/* Police du compteur plus grande */
.gm-image-viewer-counter {
    font-size: 16px;  /* Au lieu de 13px */
}
```

---

## 🚀 Performance

### Optimisations incluses
✅ **GPU acceleration** - `transform: translateZ(0)` pour smooth animations  
✅ **Touch optimized** - `touch-action: manipulation` pour tactile fluide  
✅ **Lazy loading** - Charger images seulement quand nécessaire  
✅ **Debounce** - Éviter les appels excessifs  
✅ **Memory efficient** - État minimal en mémoire  

### Points de contrôle

**Bureau**: Flèches rapides et fluides, pas de lag  
**Mobile**: Swipe immédiat, pas de délai tactile  
**Charge**: Images chargées progressivement  

---

## 🔧 Dépannage

### Le viewer ne s'ouvre pas
1. Vérifier que `image-gallery-viewer.html` est inclus dans le template
2. Vérifier la console du navigateur pour les erreurs JavaScript
3. S'assurer que `initImageGallery()` est appelé après `DOMContentLoaded`

```javascript
// ✅ Correct
document.addEventListener('DOMContentLoaded', () => {
    initImageGallery(images);
});

// ❌ Incorrect
initImageGallery(images); // Trop tôt, DOM pas chargé
```

### Les images ne s'affichent pas
1. Vérifier les URLs des images (pas de 404)
2. Vérifier les CORS si images depuis autre domaine
3. Ouvrir DevTools → Network pour voir les requêtes

```javascript
// Déboguer les images
console.log('Images chargées:', gmImageViewerState.images);
console.log('Index courant:', gmImageViewerState.currentIndex);
```

### Le swipe ne fonctionne pas
1. Vérifier que le touch event listener est attaché
2. Tester sur appareil réel (simulateur Safari peut bugger)
3. Vérifier que l'élément `.gm-image-viewer-modal` est visible

```javascript
// Déboguer les touches
document.addEventListener('touchstart', (e) => {
    console.log('Début:', e.changedTouches[0].screenX);
});
```

### Les miniatures se chevauchent
1. Ajuster la largeur du conteneur
2. Réduire la taille des miniatures
3. Vérifier le responsive CSS pour mobile

---

## 📊 État du composant

L'état du viewer est stocké dans `gmImageViewerState`:

```javascript
gmImageViewerState = {
    images: [],           // Array des images
    currentIndex: 0,      // Index de l'image actuelle
    isOpen: false,        // Viewer ouvert?
    touchStartX: 0,       // Position X du début du swipe
    touchStartY: 0        // Position Y du début du swipe
}
```

Accès en console pour déboguer:
```javascript
console.log('État:', gmImageViewerState);
console.log('Image actuelle:', gmImageViewerState.images[gmImageViewerState.currentIndex]);
```

---

## 🎬 Animations

### Animations incluses

**Apparition du viewer**:
```css
animation: gmFadeIn 0.3s ease-out;
```

**Images qui apparaissent**:
```css
animation: gmImageZoomIn 0.4s ease-out;
```

**Boutons au survol**:
```css
transition: all 0.3s ease;
transform: scale(1.1);
```

---

## 📦 Fichiers relatifs

| Fichier | Rôle |
|---------|------|
| `components/image-gallery-viewer.html` | Composant HTML + JS principal |
| `css/components/image-gallery-viewer.css` | Styles fullscreen |
| `accounts/templates/accounts/peer-product-details.html` | Intégration C2C |
| `products/templates/products/shop-product-vendor.html` | Intégration B2C |

---

## ✅ Checklist de test

- [ ] Viewer s'ouvre au clic sur image
- [ ] Compteur affiche bon nombre d'images (1/5, etc.)
- [ ] Flèches avant/arrière changent images
- [ ] Clavier marche (← →, Esc)
- [ ] Swipe marche sur mobile (←, →)
- [ ] Miniatures changent image au clic
- [ ] Miniature active est bien highlight
- [ ] Fond sombre bien opaque
- [ ] Animations sont fluides (pas de lag)
- [ ] Boutons sont accessibles au clavier
- [ ] Viewer ferme au clic fond
- [ ] Viewer ferme à Esc
- [ ] Bouton X ferme le viewer
- [ ] Responsive OK sur mobile

---

## 🌐 Compatibilité

| Navigateur | Support |
|------------|---------|
| Chrome | ✅ Excellent |
| Firefox | ✅ Excellent |
| Safari | ✅ Bon |
| Edge | ✅ Excellent |
| Opera | ✅ Excellent |
| IE 11 | ❌ Non supporté |

**Mobile**:
- ✅ iOS Safari 12+
- ✅ Android Chrome
- ✅ Android Firefox
- ✅ Samsung Internet

---

## 🚀 Prochaines améliorations possibles

1. **Zoom pinch** - Pinch to zoom sur mobile
2. **Fullscreen mode** - Mode vidéo fullscreen natif
3. **Rotation** - Tourner les images
4. **Partage** - Bouton partager image
5. **Download** - Télécharger l'image
6. **Lightbox** - Titre et description sous image
7. **Keyboard focus** - Navigation au clavier complète
8. **Analytics** - Tracker quelles images sont regardées

---

## 📝 Notes

- Viewer compatible avec tous les navigateurs modernes
- Pas de dépendances externes (jQuery, etc.)
- CSS optimisé pour performance
- JavaScript minifiable/transpilable si needed

---

**Version**: 1.0  
**Date**: 2026-04-27  
**Status**: Production Ready ✅
