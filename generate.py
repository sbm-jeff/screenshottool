#!/usr/bin/env python
import json
import os
import base64
from datetime import datetime
from bs4 import BeautifulSoup
import cairosvg

# Basisdirectory en uitzonderingen
BASE_PATH = '../download-assets'
EXCLUDED_DIRS = {'.gitignore', 'yogibitdev', 'Development'}
TEMPLATES = ['template.svg', 'template_2.svg']
IPHONE_SIZES = {
    "67": (1290, 2796),
    "65": (1242, 2688),
    "61": (1170, 2532),
    "55": (1242, 2208),
    "SE": (640, 1136)
}

# Achtergrondafbeelding inlezen als base64
def get_background_image_data_uri():
    with open(os.path.join(os.path.dirname(__file__), "bg.png"), "rb") as img_file:
        b64_string = base64.b64encode(img_file.read()).decode()
    return f"data:image/png;base64,{b64_string}"

# SVG bewerken
def customize_svg(svg_template, data, image_x):
    soup = BeautifulSoup(svg_template, 'xml')
    svg = soup.find('svg')

    # Voeg afbeelding toe
    image_tag = soup.new_tag('image', href=get_background_image_data_uri(), x=str(image_x), y="0")
    svg.insert(0, image_tag)

    # Kleur aanpassen
    theme = data['themeConfigLight']
    for el in soup.find_all('path', class_='tabbarColor'):
        el['fill'] = theme['appBarColor']
    if (divider := soup.find('path', class_='divider')):
        divider['fill'] = theme['dividerColor']
    if (bg := soup.find('rect', class_='background')):
        bg['fill'] = theme['brandColor']

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

# PNG genereren
def generate_pngs(svg_path, output_dir, prefix):
    os.makedirs(output_dir, exist_ok=True)
    for model, (width, height) in IPHONE_SIZES.items():
        output_path = os.path.join(output_dir, f"{prefix}_APP_IPHONE_{model}_{prefix}.png")
        cairosvg.svg2png(
            url=svg_path,
            write_to=output_path,
            output_width=width,
            output_height=height
        )

# Hoofdverwerking
def process_config(config_path):
    with open(config_path) as f:
        data = json.load(f)

    for idx, template_file in enumerate(TEMPLATES):
        with open(template_file, 'r') as f:
            svg_template = f.read()

        modified_svg = customize_svg(svg_template, data, image_x=-150 if idx == 0 else -1750)

        svg_filename = f"{data['urlScheme']}_{idx}.svg"
        with open(svg_filename, 'w') as f:
            f.write(modified_svg)

        generate_pngs(svg_filename, f"./{data['urlScheme']}", prefix=str(idx))

        if os.path.exists(svg_filename):
            os.remove(svg_filename)
            print(f"{svg_filename} is verwijderd.")
        else:
            print(f"{svg_filename} bestaat niet.")

# Zoek config-bestanden
def main():
    config_paths = []
    for flavor in os.listdir(BASE_PATH):
        dir_path = os.path.join(BASE_PATH, flavor)
        if os.path.isdir(dir_path) and flavor not in EXCLUDED_DIRS:
            config_path = os.path.join(dir_path, 'config.json')
            if os.path.exists(config_path):
                config_paths.append(config_path)

    for path in config_paths:
        print(f"Verwerk: {path}")
        process_config(path)

if __name__ == "__main__":
    main()
