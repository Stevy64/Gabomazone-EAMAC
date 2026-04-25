/**
 * Carte C2C partagée : fond satellite (Esri) + secours, surcouche noms,
 * marqueurs zones Gabomazone et lieux populaires — même logique que la commande utilisateur.
 * Maintenance centralisée : inclure ce script + gm_c2c_leaflet_map.css
 */
(function (global) {
  'use strict';

  var LIBREVILLE = [0.4162, 9.4673];

  var TILE_PROVIDERS = [
    {
      url: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
      attr:
        'Imagery © <a href="https://www.esri.com/" target="_blank" rel="noopener">Esri</a>, Maxar, Earthstar et contributeurs',
    },
    {
      url: 'https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
      attr:
        'Imagery © <a href="https://www.esri.com/" target="_blank" rel="noopener">Esri</a>, Maxar et contributeurs',
    },
    {
      url: 'https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png',
      subdomains: 'abcd',
      attr: '© <a href="https://carto.com/attributions" target="_blank" rel="noopener">CARTO</a> © OSM',
    },
    {
      url: 'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
      attr:
        '© <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener">OpenStreetMap</a>',
    },
  ];

  function parseCoord(v) {
    if (typeof v === 'number') return Number.isFinite(v) ? v : NaN;
    if (v === null || typeof v === 'undefined') return NaN;
    var s = String(v).trim().replace(',', '.');
    var n = parseFloat(s);
    return Number.isFinite(n) ? n : NaN;
  }

  function escapeHtml(s) {
    var d = document.createElement('div');
    d.textContent = s || '';
    return d.innerHTML;
  }

  function setLeafletDefaultIconPath(baseUrl) {
    if (typeof L === 'undefined') return;
    var b = (baseUrl || '').replace(/\/?$/, '/');
    try {
      L.Icon.Default.mergeOptions({
        iconUrl: b + 'marker-icon.png',
        iconRetinaUrl: b + 'marker-icon-2x.png',
        shadowUrl: b + 'marker-shadow.png',
      });
    } catch (e) {
      try {
        L.Icon.Default.prototype.options.imagePath = b;
      } catch (e2) {}
    }
  }

  function filterValidZones(zones) {
    var z = zones || [];
    if (!Array.isArray(z)) return [];
    return z.filter(function (zone) {
      var la = parseCoord(zone.latitude);
      var lo = parseCoord(zone.longitude);
      return (
        Number.isFinite(la) &&
        Number.isFinite(lo) &&
        Math.abs(la) <= 90 &&
        Math.abs(lo) <= 180
      );
    });
  }

  /**
   * Tuiles satellite en priorité, bascule automatique si erreur / timeout.
   */
  function attachSatelliteBasemapWithFallback(map, options) {
    options = options || {};
    var onHideLoading = typeof options.onHideLoading === 'function' ? options.onHideLoading : function () {};
    var tileIdx = 0;
    var tileErrorCount = 0;
    var tiles = null;
    var tileSwitchTimer = null;
    var tileLayerDidLoad = false;
    var labelOverlay = null;

    function gmSyncPlaceNameOverlay() {
      if (!map) return;
      var onSatellite = tileIdx < 2;
      if (onSatellite) {
        if (!labelOverlay) {
          labelOverlay = L.tileLayer(
            'https://{s}.basemaps.cartocdn.com/rastertiles/voyager_only_labels/{z}/{x}/{y}{r}.png',
            {
              subdomains: 'abcd',
              maxZoom: 20,
              minZoom: 1,
              opacity: 0.95,
              attribution:
                ' · Noms de lieux © <a href="https://carto.com/attributions" target="_blank" rel="noopener">CARTO</a> © <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener">OSM</a>',
            }
          );
        }
        if (!map.hasLayer(labelOverlay)) labelOverlay.addTo(map);
        try {
          labelOverlay.bringToFront();
        } catch (e) {}
      } else if (labelOverlay && map.hasLayer(labelOverlay)) {
        map.removeLayer(labelOverlay);
      }
    }

    function gmClearTileSwitchTimer() {
      if (tileSwitchTimer) {
        clearTimeout(tileSwitchTimer);
        tileSwitchTimer = null;
      }
    }

    function gmTryNextTileProvider(reason) {
      gmClearTileSwitchTimer();
      if (tileIdx >= TILE_PROVIDERS.length - 1) {
        onHideLoading();
        return;
      }
      if (tiles && map) {
        try {
          map.removeLayer(tiles);
        } catch (e) {}
      }
      tileIdx++;
      tileErrorCount = 0;
      gmAddTiles();
    }

    function gmAddTiles() {
      tileLayerDidLoad = false;
      var p = TILE_PROVIDERS[tileIdx];
      var opts = { maxZoom: 19, minZoom: 5, attribution: p.attr };
      if (p.subdomains) opts.subdomains = p.subdomains;
      tiles = L.tileLayer(p.url, opts);
      tiles.on('load', function () {
        tileLayerDidLoad = true;
        gmClearTileSwitchTimer();
        gmSyncPlaceNameOverlay();
        onHideLoading();
      });
      tiles.on('tileerror', function () {
        tileErrorCount++;
        if (tileErrorCount >= 2) {
          gmTryNextTileProvider('tileerror');
        }
      });
      tiles.addTo(map);
      gmSyncPlaceNameOverlay();
      tileSwitchTimer = setTimeout(function () {
        if (!tiles || !map || !map.hasLayer(tiles)) return;
        if (!tileLayerDidLoad) {
          gmTryNextTileProvider('timeout');
        }
      }, 6500);
    }

    gmAddTiles();

    return {
      destroy: function () {
        gmClearTileSwitchTimer();
        try {
          if (tiles && map.hasLayer(tiles)) map.removeLayer(tiles);
        } catch (e) {}
        try {
          if (labelOverlay && map.hasLayer(labelOverlay)) map.removeLayer(labelOverlay);
        } catch (e2) {}
      },
    };
  }

  function popupSafeZoneUser(z) {
    var la = parseCoord(z.latitude);
    var lo = parseCoord(z.longitude);
    return (
      '<div style="min-width:180px;">' +
      '<strong style="font-size:14px;color:#111827;">' +
      (z.is_featured ? '⭐ ' : '') +
      escapeHtml(z.name) +
      '</strong>' +
      '<p style="margin:6px 0 2px;font-size:12px;color:#6B7280;">' +
      escapeHtml(z.address) +
      '</p>' +
      (z.city
        ? '<p style="margin:2px 0;font-size:12px;color:#6B7280;">' + escapeHtml(z.city) + '</p>'
        : '') +
      (z.opening_hours
        ? '<p style="margin:4px 0 8px;font-size:11px;color:#374151;">' +
          escapeHtml(z.opening_hours) +
          '</p>'
        : '') +
      '<button type="button" onclick="if(typeof gmSelectZone===\'function\'){gmSelectZone(' +
      z.id +
      ');} if(window.gmMapRef){try{window.gmMapRef.closePopup();}catch(e){}}" style="width:100%;padding:8px;background:#10B981;color:#fff;border:none;border-radius:8px;font-weight:700;cursor:pointer;font-size:12px;">Sélectionner cette zone</button>' +
      '</div>'
    );
  }

  function popupPopularUser(p) {
    var pLabel = p.name || 'Lieu populaire';
    var pAddr = p.address || '';
    var pUses = Number(p.usage_count || 0);
    return (
      '<div style="min-width:190px;">' +
      '<strong style="font-size:14px;color:#111827;">🔥 ' +
      escapeHtml(pLabel) +
      '</strong>' +
      (pAddr
        ? '<p style="margin:6px 0 4px;font-size:12px;color:#6B7280;">' + escapeHtml(pAddr) + '</p>'
        : '') +
      (pUses
        ? '<p style="margin:2px 0 8px;font-size:11px;color:#9A3412;">Utilisé ' +
          pUses +
          ' fois</p>'
        : '') +
      '<button type="button" onclick="if(typeof gmUsePopularPointById===\'function\'){gmUsePopularPointById(' +
      p.id +
      ');} if(window.gmMapRef){try{window.gmMapRef.closePopup();}catch(e){}}" style="width:100%;padding:8px;background:#F97316;color:#fff;border:none;border-radius:8px;font-weight:700;cursor:pointer;font-size:12px;">Utiliser ce lieu</button>' +
      '</div>'
    );
  }

  function popupSafeZoneAdmin(z) {
    var la = parseCoord(z.latitude);
    var lo = parseCoord(z.longitude);
    return (
      '<div style="min-width:180px;">' +
      '<strong style="font-size:14px;color:#111827;">' +
      (z.is_featured ? '⭐ ' : '') +
      escapeHtml(z.name) +
      '</strong>' +
      '<p style="margin:6px 0;font-size:12px;color:#6B7280;">' +
      escapeHtml(z.address) +
      '</p>' +
      '<button type="button" class="gm-admin-map-pick-btn" data-lat="' +
      la +
      '" data-lng="' +
      lo +
      '" style="width:100%;padding:8px;background:#2563EB;color:#fff;border:none;border-radius:8px;font-weight:700;cursor:pointer;font-size:12px;">Copier ces coordonnées</button>' +
      '</div>'
    );
  }

  function popupPopularAdmin(p) {
    var la = parseCoord(p.latitude);
    var lo = parseCoord(p.longitude);
    var pLabel = p.name || 'Lieu populaire';
    return (
      '<div style="min-width:190px;">' +
      '<strong style="font-size:14px;color:#111827;">🔥 ' +
      escapeHtml(pLabel) +
      '</strong>' +
      (p.address
        ? '<p style="margin:6px 0;font-size:12px;color:#6B7280;">' + escapeHtml(p.address) + '</p>'
        : '') +
      '<button type="button" class="gm-admin-map-pick-btn" data-lat="' +
      la +
      '" data-lng="' +
      lo +
      '" style="width:100%;padding:8px;background:#F97316;color:#fff;border:none;border-radius:8px;font-weight:700;cursor:pointer;font-size:12px;">Copier ces coordonnées</button>' +
      '</div>'
    );
  }

  function addSafeZoneMarkers(map, zones, mode) {
    mode = mode || 'user';
    var valid = filterValidZones(zones);
    valid.forEach(function (z) {
      var la = parseCoord(z.latitude);
      var lo = parseCoord(z.longitude);
      var iconClass =
        'gm-leaflet-zone-marker' + (z.is_featured ? ' gm-leaflet-zone-marker--featured' : '');
      var sym = z.is_featured ? '⭐' : '★';
      var icon = L.divIcon({
        html: '<div class="' + iconClass + '">' + sym + '</div>',
        className: '',
        iconSize: [32, 32],
        iconAnchor: [16, 16],
      });
      var m = L.marker([la, lo], { icon: icon, title: z.name }).addTo(map);
      var html = mode === 'admin' ? popupSafeZoneAdmin(z) : popupSafeZoneUser(z);
      m.bindPopup(html);
    });
    return valid;
  }

  function addPopularPointMarkers(map, points, mode) {
    mode = mode || 'user';
    (points || []).forEach(function (p) {
      var pla = parseCoord(p.latitude);
      var plo = parseCoord(p.longitude);
      if (!Number.isFinite(pla) || !Number.isFinite(plo)) return;
      var icon = L.divIcon({
        html: '<div class="gm-leaflet-popular-marker">★</div>',
        className: '',
        iconSize: [26, 26],
        iconAnchor: [13, 13],
      });
      var pm = L.marker([pla, plo], { icon: icon, title: p.name || 'Lieu populaire' }).addTo(map);
      var html = mode === 'admin' ? popupPopularAdmin(p) : popupPopularUser(p);
      pm.bindPopup(html);
    });
  }

  function defaultCenterFromZones(zones) {
    var valid = filterValidZones(zones);
    if (valid.length > 0) {
      return [parseCoord(valid[0].latitude), parseCoord(valid[0].longitude)];
    }
    return LIBREVILLE.slice();
  }

  global.GmC2cLeafletMapCore = {
    LIBREVILLE: LIBREVILLE,
    parseCoord: parseCoord,
    escapeHtml: escapeHtml,
    setLeafletDefaultIconPath: setLeafletDefaultIconPath,
    filterValidZones: filterValidZones,
    defaultCenterFromZones: defaultCenterFromZones,
    attachSatelliteBasemapWithFallback: attachSatelliteBasemapWithFallback,
    addSafeZoneMarkers: addSafeZoneMarkers,
    addPopularPointMarkers: addPopularPointMarkers,
  };
})(typeof window !== 'undefined' ? window : this);
