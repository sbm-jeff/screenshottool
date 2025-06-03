#!/usr/bin/env python
import json
import os
from PIL import Image
import cairosvg
from datetime import datetime
from bs4 import BeautifulSoup
from io import BytesIO
import requests

BASE_PATH = '../download-assets'
EXCLUDED_DIRS = {'.gitignore', 'yogibitdev', 'Development'}

def download_image_from_url(url):
    response = requests.get(url)
    response.raise_for_status()
    return Image.open(BytesIO(response.content)).convert("RGBA")

# SVG naar PNG converteren
def svg_to_png(svg_path, png_path):
    cairosvg.svg2png(url=svg_path, write_to=png_path)

def paste_rotated_image(background, image, position, angle, size=(1345, 750)):
    # Verklein naar vast formaat
    image = image.resize(size, Image.Resampling.LANCZOS)

    # Roteer afbeelding
    rotated = image.rotate(angle, expand=True)

    # Plak op achtergrond met transparantie
    background.paste(rotated, position, rotated)
    return background

# Overlay PNG op achtergrond met rotatie
def paste_rotated_png(background, png_path, position, angle):
    overlay = Image.open(png_path).convert("RGBA")
    rotated_overlay = overlay.rotate(angle, expand=True)
    background.paste(rotated_overlay, position, rotated_overlay)
    return background

# Afbeelding uitsnijden en opslaan
def crop_image(input_path, crop_box, output_path):
    image = Image.open(input_path)
    cropped = image.crop(crop_box)
    cropped.save(output_path)

def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

# Afbeelding uit omgeving
def blend_background_with_hex_color(background, hex_color, opacity=0.5):
    rgb_color = hex_to_rgb(hex_color)
    background = background.convert("RGBA")
    color_layer = Image.new("RGBA", background.size, rgb_color + (int(255 * opacity),))
    blended = Image.alpha_composite(background, color_layer)
    return blended

def safe_download_image(data, fallback_url):
    try:
        base_url = None

        if data and isinstance(data, dict):
            sportlocatie = data.get('sportlocatie')
            if sportlocatie and isinstance(sportlocatie, dict):
                base_url = sportlocatie.get('url')

        if not base_url:
            raise ValueError("Geen geldige sportlocatie URL gevonden.")

        url = base_url.rstrip("/") + "/img/bg.jpg"
        image = download_image_from_url(url)
        if image is None:
            raise ValueError("Download mislukt of geen afbeelding ontvangen.")
        return image

    except Exception as e:
        print(f"Fout bij downloaden van externe afbeelding: {e}")
        fallback = fallback_url.rstrip("/") + "/img/bg.jpg"
        print(f"Gebruik fallback: {fallback}")
        return download_image_from_url(fallback)


def customize_devicesvg(svg_template, data):
    soup = BeautifulSoup(svg_template, 'xml')

    # Kleur aanpassen
    theme = data['themeConfigLight']
    for el in soup.find_all('path', class_='tabbarColor'):
        el['fill'] = theme['appBarColor']
    if (divider := soup.find('path', class_='divider')):
        divider['fill'] = theme['dividerColor']
    if (bg := soup.find('rect', class_='background')):
        bg['fill'] = theme['brandColor']
    if (bg := soup.find('path', class_='brandbutton')):
        bg['fill'] = theme['welkomInlogknopColor']    


    # Teksten aanpassen
    for t in soup.find_all('tspan', class_='brandname'):
        if t.string:
            t.string = t.string.replace('SportBit Manager', data['app']['naam'])

    for t in soup.find_all('tspan', class_='trainer'):
        if data.get('dialect') == 'yoga':
            t.string.replace_with('docent')

    jaar = str(datetime.now().year)
    for t in soup.find_all('tspan', class_='year'):
        if t.string:
            t.string = t.string.replace('{year}', jaar)

    return str(soup)
    
# Hoofdprogramma
def compose_and_crop(background_path, output_path, data):
    with open('mockup1.svg', 'r') as f:
        device_svg = f.read()
    modified_svg = customize_devicesvg(device_svg, data)
    svg_filename = f"{data['urlScheme']}_1.svg"
    with open(svg_filename, 'w') as f:
        f.write(modified_svg)

    with open('mockup2.svg', 'r') as f:
        device_svg2 = f.read()
    modified_svg2 = customize_devicesvg(device_svg2, data)
    svg_filename2 = f"{data['urlScheme']}_2.svg"
    with open(svg_filename2, 'w') as f:
        f.write(modified_svg2)    

    # SVG-bestanden converteren
    svg_to_png(svg_filename, "mockup1.png")
    svg_to_png(svg_filename2, "mockup2.png")

    # SVG-bestanden verwijderen
    os.remove(svg_filename)
    os.remove(svg_filename2)
    
    # Achtergrond laden
    background = Image.open(background_path).convert("RGBA")
    # Color layer
    brandColor = data['themeConfigLight']['brandColor']
    background = blend_background_with_hex_color(background, brandColor, opacity=0.25)

    # PNG's plaatsen op achtergrond
    background = paste_rotated_png(
        background,
        png_path="mockup1.png",
        position=(10, 300),
        angle=-15
    )
    background = paste_rotated_png(
        background,
        png_path="mockup2.png",
        position=(3300, 500),
        angle=15
    )

    fallback_base_url = "https://demo.sportbitapp.nl"
    downloaded_image = safe_download_image(data, fallback_base_url)

    # Plak afbeelding (mits succesvol gedownload)
    if downloaded_image:
        background = paste_rotated_image(
            background,
            image=downloaded_image,
            position=(3555, 1260),
            angle=15
        )

    # Samengesteld beeld opslaan
    background.save(output_path)

    output_dir = f"./{data['urlScheme']}"
    os.makedirs(output_dir, exist_ok=True)

    # Uitsnijden left, top, right, bottom
    crop_image(output_path, crop_box=(1000, 20, 2580, 3300), output_path= os.path.join(output_dir, f"uitsnede_mockup1.png"))
    crop_image(output_path, crop_box=(2650, 0, 4230, 3300), output_path= os.path.join(output_dir, f"uitsnede_mockup2.png"))
    crop_image(output_path, crop_box=(4300, 0, 5880, 3300), output_path= os.path.join(output_dir, f"uitsnede_mockup3.png"))

    

    # Afbeeldingen verwijderen
    os.remove("mockup1.png")
    os.remove("mockup2.png")
    os.remove("samengesteld.png")

# Starten
def process_config(config_path):
    # Config inladen
    with open(config_path) as f:
        data = json.load(f)

    compose_and_crop(
        background_path="bg.png",
        output_path="samengesteld.png",
        data=data
    )

def main():
    config_paths = []
    for flavor in os.listdir(BASE_PATH):
        dir_path = os.path.join(BASE_PATH, flavor)
        if os.path.isdir(dir_path) and flavor not in EXCLUDED_DIRS: # == 'adventurebikeriderclub': #
            config_path = os.path.join(dir_path, 'config.json')
            if os.path.exists(config_path):
                config_paths.append(config_path)

    for path in config_paths:
        print(f"Verwerk: {path}")
        process_config(path)

if __name__ == "__main__":
    main()