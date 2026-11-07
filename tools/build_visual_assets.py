#!/usr/bin/env python3
"""Extraire uniquement les photographies décoratives de la référence fournie.

Ces images illustrent la maquette, pas les pièces réelles ni l'état des appareils.
Les valeurs et commandes restent rendues dynamiquement par Home Assistant.
"""
import argparse
import hashlib
import json
from pathlib import Path
from PIL import Image, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = Path('/root/.hermes/webui/attachments/838f6e7e7697/tableau_de_bord_domotique_ai_nexus_avec_sportage.png')
# Coordonnées revues à partir des boîtes OCR de la référence 1672 x 941.
# Exclusion des noms (y >= 425), valeurs (y >= 467) et boutons.
CROPS = {
    'salon': (196, 345, 430, 418),
    'cuisine': (442, 345, 674, 418),
    'bureau': (685, 345, 917, 418),
    'parents': (929, 345, 1162, 418),
    'emile': (1176, 345, 1406, 418),
    'maddy': (1418, 345, 1657, 418),
    'sami': (1190, 662, 1355, 705),
    'navimow-map': (1409, 666, 1647, 705),
    'sportage': (775, 816, 970, 892),  # historique conservé pour rollback
    'sportage-full': (774, 806, 950, 889),  # silhouette entière, sans chiffres/boutons
}


def build_sportage_full(source, destination=None):
    """Ajout isolé de l'image corrigée ; aucun asset précédent n'est écrasé."""
    destination = destination or ROOT / 'assets' / 'visual'
    image = Image.open(source).convert('RGB')
    if image.size != (1672, 941):
        raise ValueError('La source doit être la référence originale 1672 x 941')
    destination.mkdir(parents=True, exist_ok=True)
    box = CROPS['sportage-full']
    crop = image.crop(box)
    path = destination / 'sportage-full.webp'
    crop.save(path, 'WEBP', quality=95)
    entry = {'file': path.name, 'crop': list(box), 'size': list(crop.size),
             'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
             'source': str(source), 'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest()}
    manifest_path = destination / 'manifest.json'
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {'assets': [], 'illustrative_only': True}
    manifest['assets'] = [item for item in manifest['assets'] if item['file'] != path.name] + [entry]
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2))
    return entry


def build(source=DEFAULT_SOURCE, destination=None):
    destination = destination or ROOT / 'assets' / 'visual'
    destination.mkdir(parents=True, exist_ok=True)
    raw = source.read_bytes()
    image = Image.open(source).convert('RGB')
    if image.size != (1672, 941):
        raise ValueError('La source doit être la référence originale 1672 x 941')
    entries = []
    for name, box in CROPS.items():
        crop = image.crop(box)
        path = destination / f'{name}.webp'
        crop.save(path, 'WEBP', quality=95)
        entries.append({'file': path.name, 'crop': list(box), 'size': list(crop.size),
                        'sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
    # Fond photographique doux, sans textes/boutons/valeurs de la maquette.
    hero = image.crop(CROPS['salon']).resize((1400, 438), Image.Resampling.LANCZOS).filter(ImageFilter.GaussianBlur(1.5))
    path = destination / 'hero.webp'
    hero.save(path, 'WEBP', quality=92)
    entries.append({'file': path.name, 'crop': list(CROPS['salon']), 'size': list(hero.size),
                    'sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'transform': 'resize + blur decorative'})
    # Le crop Navimow de la maquette est une carte, pas une tondeuse :
    # utiliser la copie locale du visuel constructeur vérifié, même série i2 AWD.
    product = ROOT / 'assets/source/navimow-i2-awd.png'
    provenance = json.loads((product.parent / 'navimow-provenance.json').read_text())
    if hashlib.sha256(product.read_bytes()).hexdigest() != provenance['sha256']:
        raise ValueError('Le visuel constructeur ne correspond pas à sa provenance')
    mower = Image.open(product).convert('RGBA')
    mower.thumbnail((600, 600), Image.Resampling.LANCZOS)
    path = destination / 'navimow.webp'
    mower.save(path, 'WEBP', quality=95)
    entries.append({'file': path.name, 'size': list(mower.size),
                    'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                    'provenance': provenance})
    manifest = {'source': str(source), 'source_sha256': hashlib.sha256(raw).hexdigest(),
                'source_size': list(image.size), 'illustrative_only': True,
                'notice': 'Photographies recadrées de la maquette fournie par Denis. Pas de photo réelle de son domicile. Visuels produits illustratifs, sans état statique.',
                'public_prefix': '/local/ai-nexus-v4/visual/', 'assets': entries}
    (destination / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2))
    return manifest


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', nargs='?', type=Path, default=DEFAULT_SOURCE)
    args = parser.parse_args()
    print(json.dumps(build(args.source), ensure_ascii=False, indent=2))
