#!/usr/bin/env python
import json
import os
from PIL import Image, ImageDraw, ImageFont
import cairosvg
from datetime import datetime
from bs4 import BeautifulSoup
from io import BytesIO
import requests

BASE_PATH = '../download-assets'
EXCLUDED_DIRS = {'.gitignore', 'yogibitdev', 'Development'}
MAINFONT = "C:\\Users\\sbmpc\\AppData\\Local\\Microsoft\\Windows\\Fonts\\OGJ Type Design - Shapiro Pro 573 Black Caviar.ttf"
original_size = (5880, 3300)

formaten = {
    "69": (1290, 2796),
    "65": (1242, 2688),
    # "61": (1170, 2532),
    # "55": (1242, 2208),
    # "SE": (640, 1136)
}

# left, top, right, bottom
crop_boxes = {
    "mockup1": (1000, 20, 2580, 3300),
    "mockup2": (2650, 0, 4230, 3300),
    "mockup3": (4300, 0, 5880, 3300)
}

def add_text_to_image(image, text, position, font_path=None, font_size=50, color=(255, 255, 255), opacity=255):
    txt_layer = Image.new("RGBA", image.size, (255, 255, 255, 0))
    draw = ImageDraw.Draw(txt_layer)

    try:
        if font_path:
            font = ImageFont.truetype(font_path, font_size)
        else:
            raise OSError("Geen font pad opgegeven")
    except OSError:
        print("⚠️  Kon opgegeven font niet laden, gebruik standaardfont.")
        font = ImageFont.load_default()

    # Kleur inclusief opacity
    rgba_color = (*color[:3], opacity)

    # Tekst tekenen
    draw.text(position, text, font=font, fill=rgba_color)

    # Transparante laag over originele afbeelding plakken
    return Image.alpha_composite(image.convert("RGBA"), txt_layer)

def download_image_from_url(url):
    response = requests.get(url)
    response.raise_for_status()
    return Image.open(BytesIO(response.content)).convert("RGBA")

# SVG naar PNG converteren
def svg_to_png(svg_path, png_path):
    cairosvg.svg2png(url=svg_path, write_to=png_path)

def paste_rotated_image(background, image, position, angle, size=(1345, 750)):
    target_width, target_height = size
    image_ratio = image.width / image.height
    target_ratio = target_width / target_height

    # Crop de afbeelding met behoud van verhouding
    if image_ratio > target_ratio:
        # Afbeelding is te breed: crop zijkanten
        new_width = int(image.height * target_ratio)
        offset = (image.width - new_width) // 2
        image = image.crop((offset, 0, offset + new_width, image.height))
    else:
        # Afbeelding is te hoog: crop boven/onder
        new_height = int(image.width / target_ratio)
        offset = (image.height - new_height) // 2
        image = image.crop((0, offset, image.width, offset + new_height))

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
    if (bg := soup.find('rect', class_='brandbutton')):
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
    
def scale_crop_box(box, from_size, to_size):
    fx = to_size[0] / from_size[0]
    fy = to_size[1] / from_size[1]
    return tuple(int(coord * fx if i % 2 == 0 else coord * fy) for i, coord in enumerate(box))


def textgenerator(background, text, xpos, ypos, fontsize, opacity=255):
    return add_text_to_image(
        image=background,
        text=text,
        position=(xpos, ypos),
        font_path=MAINFONT,
        font_size=fontsize,
        color=(255, 255, 255),
        opacity=opacity
    )

def compose_and_crop(background_path, output_path, data):
    def create_mockup(svg_path, output_name):
        with open(svg_path, 'r') as f:
            svg_content = f.read()
        modified_svg = customize_devicesvg(svg_content, data)
        svg_filename = f"{data['urlScheme']}_{output_name}.svg"
        with open(svg_filename, 'w') as f:
            f.write(modified_svg)
        png_filename = f"mockup{output_name}.png"
        svg_to_png(svg_filename, png_filename)
        os.remove(svg_filename)
        return png_filename

    # Mockups genereren
    mockup1 = create_mockup('mockup1.svg', '1')
    mockup2 = create_mockup('mockup2.svg', '2')

    # Achtergrond voorbereiden
    background = Image.open(background_path).convert("RGBA")
    brandColor = data['themeConfigLight']['brandColor']
    background = blend_background_with_hex_color(background, brandColor, opacity=0.25)

    # Mockups plaatsen
    background = paste_rotated_png(background, mockup1, (10, 300), -15)
    background = paste_rotated_png(background, mockup2, (3300, 500), 15)

    # Extra afbeelding downloaden
    fallback_base_url = "https://demo.sportbitapp.nl"
    downloaded_image = safe_download_image(data, fallback_base_url)
    if downloaded_image:
        background = paste_rotated_image(background, downloaded_image, (3555, 1260), 15)

    # Samengestelde afbeelding opslaan
    background.save(output_path)

    # Croppen en tekst toevoegen
    output_dir = f"./{data['urlScheme']}"
    os.makedirs(output_dir, exist_ok=True)

    for model, target_size in formaten.items():
        if model == '69':
            crops = [(1290, 20, 2580, 2796), (2650, 0, 3940, 2796), (4010, 0, 5300, 2796)]
        elif model == '65':
            crops = [(1338, 20, 2580, 2688), (2650, 0, 3892, 2688), (3962, 0, 5204, 2688)]
        else:
            continue

        for i, crop_box in enumerate(crops, start=1):
            cropped_path = os.path.join(output_dir, f"{model}_{i}.png")
            crop_image(output_path, crop_box=crop_box, output_path=cropped_path)

        # Tekst toevoegen aan eerste twee afbeeldingen
        texts = [
            ("Rooster", "Een plekje vrij?\nBekijk het in het overzicht"),
            ("Reserveren", "Aanmelden voor\nJouw favoriete lessen")
        ]

        for i, (title, subtitle) in enumerate(texts, start=1):
            img_path = os.path.join(output_dir, f"{model}_{i}.png")
            img = Image.open(img_path).convert("RGBA")
            img = add_text_to_image(img, title, (100, 128), MAINFONT, 50, (0, 0, 0), 128)
            img = add_text_to_image(img, title, (100, 125), MAINFONT, 50, (255, 255, 255), 128)
            img = add_text_to_image(img, subtitle, (100, 183), MAINFONT, 80, (0, 0, 0), 128)
            img = add_text_to_image(img, subtitle, (100, 180), MAINFONT, 80, (255, 255, 255))
            img.save(img_path)

    # Tijdelijke bestanden opruimen
    for fname in [mockup1, mockup2, output_path]:
        if os.path.exists(fname):
            os.remove(fname)

def compose_and_crop_ipad(background_path, output_path, data):
    def create_mockup(svg_path, output_name):
        with open(svg_path, 'r') as f:
            svg_content = f.read()
        modified_svg = customize_devicesvg(svg_content, data)
        svg_filename = f"{data['urlScheme']}_ipad_{output_name}.svg"
        with open(svg_filename, 'w') as f:
            f.write(modified_svg)
        png_filename = f"ipad_mockup{output_name}.png"
        svg_to_png(svg_filename, png_filename)
        os.remove(svg_filename)
        return png_filename

    # iPad mockups genereren
    mockup1 = create_mockup('mockup_ipad1.svg', '1')
    mockup2 = create_mockup('mockup_ipad2.svg', '2')

    background = Image.open(background_path).convert("RGBA")
    brandColor = data['themeConfigLight']['brandColor']
    background = blend_background_with_hex_color(background, brandColor, opacity=0.25)

    background = paste_rotated_png(background, mockup1, (1100, 700), 0)
    background = paste_rotated_png(background, mockup2, (3150, 700), 0)

    # Extra afbeelding downloaden
    fallback_base_url = "https://demo.sportbitapp.nl"
    downloaded_image = safe_download_image(data, fallback_base_url)
    if downloaded_image:
        background = paste_rotated_image(background, downloaded_image, (3225, 1175), 0, (1720, 600))

    # Samengestelde afbeelding opslaan
    
    background.save(output_path)

    output_dir = f"./{data['urlScheme']}"
    os.makedirs(output_dir, exist_ok=True)

    # Crop box-waarden aanpassen aan iPad afmetingen  2048 2732
    ipad_crops = [(1000, 100, 3048, 2732), (3050, 100, 5098, 2732)]
    for i, crop_box in enumerate(ipad_crops, start=1):
        cropped_path = os.path.join(output_dir, f"ipad_{i}.png")
        crop_image(output_path, crop_box=crop_box, output_path=cropped_path)

        # Tekst toevoegen aan eerste twee afbeeldingen
        texts = [
            ("Rooster", "Een plekje vrij?\nBekijk het in het overzicht"),
            ("Reserveren", "Aanmelden voor\nJouw favoriete lessen")
        ]

        for i, (title, subtitle) in enumerate(texts, start=1):
            img_path = os.path.join(output_dir, f"ipad_{i}.png")
            if not os.path.exists(img_path):
                continue

            img = Image.open(img_path).convert("RGBA")
            img = add_text_to_image(img, title, (100, 128), MAINFONT, 50, (0, 0, 0), 128)
            img = add_text_to_image(img, title, (100, 125), MAINFONT, 50, (255, 255, 255), 128)
            img = add_text_to_image(img, subtitle, (100, 183), MAINFONT, 80, (0, 0, 0), 128)
            img = add_text_to_image(img, subtitle, (100, 180), MAINFONT, 80, (255, 255, 255))
            img.save(img_path)

    for fname in [mockup1, mockup2, output_path]:
        if os.path.exists(fname):
            os.remove(fname)


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

    compose_and_crop_ipad(
        background_path="bg.png",
        output_path="samengesteld_ipad.png",
        data=data
    )

def main():
    config_paths = []
    for flavor in os.listdir(BASE_PATH):
        dir_path = os.path.join(BASE_PATH, flavor)
        if os.path.isdir(dir_path) and flavor not in EXCLUDED_DIRS:
            config_path = os.path.join(dir_path, 'config.json')
            if os.path.exists(config_path):
                config_paths.append(config_path)

    for path in config_paths:
        process_config(path)

if __name__ == "__main__":
    main()