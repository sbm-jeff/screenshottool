#!/usr/bin/env python
import json
import os
import base64
from datetime import datetime
from bs4 import BeautifulSoup
import cairosvg
import xml.etree.ElementTree as ET
import math

# Basisdirectory en uitzonderingen
BASE_PATH = '../download-assets'
EXCLUDED_DIRS = {'.gitignore', 'yogibitdev', 'Development'}
TEMPLATES = ['template.svg', 'template_2.svg']
VIEWBOX_SIZES = {
    "67": (1290, 2796),
    "65": (1242, 2688),
    "61": (1170, 2532),
    "55": (1242, 2208),
    "SE": (1242, 2208)  # base op "55"
}
IPHONE_SIZES = {
    "67": (1290, 2796),
    "65": (1242, 2688),
    "61": (1170, 2532),
    "55": (1242, 2208),
    "SE": (640, 1136)  # output formaat
}
# Achtergrondafbeelding inlezen als base64
def get_background_image_data_uri():
    with open(os.path.join(os.path.dirname(__file__), "bg.png"), "rb") as img_file:
        b64_string = base64.b64encode(img_file.read()).decode()
    return f"data:image/png;base64,{b64_string}"

# SVG bewerken

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

def customize_svg(svg_template, data, image_x, viewbox, idx):
    
    soup = BeautifulSoup(svg_template, 'xml')
    svg = soup.find('svg')
    svg['viewBox'] = viewbox
    # Voeg afbeelding toe
    image_tag = soup.new_tag('image', href=get_background_image_data_uri(), x=str(image_x), y="0")
    svg.insert(0, image_tag)

    # "67": (1290, 2796),
    # "65": (1242, 2688),
    # "61": (1170, 2532),
    # "55": (1242, 2208),
    # "SE": (640, 1136)
    viewbox_width = int(float(viewbox.split(' ')[2]))
    viewbox_height = int(float(viewbox.split(' ')[3]))

    
    if viewbox_width == 1290:    
        positieX = 150 if idx == 0 else -1250
        positieY = '15%' if idx == 0 else '25.5%'
        shadowtext = '6% 5%'
        text = '3% 5%'
    elif viewbox_width == 1242 and viewbox_height == 2688:
        positieX = 95 if idx == 0 else -1250
        positieY = '13%' if idx == 0 else '29.5%'
        shadowtext = '3% 4.5%'
        text = '3% 5%'
    elif viewbox_width == 1242 and viewbox_height == 2208:
        positieX = 80 if idx == 0 else -1250  
        positieY = '11%' if idx == 0 else '29.5%'
        shadowtext = '3% 4.5%'
        text = '3% 5%'
    elif viewbox_width == 1170:
        positieX = 15 if idx == 0 else -1250
        positieY = '20%' if idx == 0 else '36.5%'
        shadowtext = '3% 4.5%'
        text = '3% 5%'
    elif viewbox_width == 640:
        positieX = 50 if idx == 0 else -1250
        positieY = '20%' if idx == 0 else '36.5%'
        shadowtext = '3% 4.5%'
        text = '3% 5%'
    else:
        positieX = 0  # fallback
        positieY = '20%' if idx == 0 else '36.5%'
        shadowtext = '3% 4.5%'
        text = '3% 5%'

    # round(gekantelde_breedte) - int(viewbox.split(' ')[2])
    for el in soup.find_all('g', class_='device-container'):
        for attr, value in el.attrs.items():
            if isinstance(value, str) and '{positionX}' in value:
                el[attr] = value.replace('{positionX}', str(positieX))        

    for el in soup.find_all('g', class_='device-container'):
        for attr, value in el.attrs.items():
            if isinstance(value, str) and '{positionY}' in value:
                el[attr] = value.replace('{positionY}', str(positieY))

    for el in soup.find_all('g', class_='shadowtext'):
        for attr, value in el.attrs.items():
            if isinstance(value, str) and '{position}' in value:
                el[attr] = value.replace('{position}', str(shadowtext))

    for el in soup.find_all('g', class_='text'):
        for attr, value in el.attrs.items():
            if isinstance(value, str) and '{position}' in value:
                el[attr] = value.replace('{position}', str(text))                

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

    for t in soup.find_all(string=True):
        if '{height}' in t:
            t.replace_with(t.replace('{height}', viewbox.split(' ')[3]))


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

def process_config(config_path):
    # Config inladen
    with open(config_path) as f:
        data = json.load(f)

    # Laad device.svg en pas aan
    with open('device.svg', 'r') as f:
        device_svg = f.read()
    modified_device_svg = customize_devicesvg(device_svg, data)

    # Gebruik dezelfde aangepaste device slechts eenmaal
    custom_device_soup = BeautifulSoup(modified_device_svg, 'xml')
    device_root = custom_device_soup.find('g')

    for idx, template_file in enumerate(TEMPLATES):
        with open(template_file, 'r') as f:
            svg_template = f.read()

        soup = BeautifulSoup(svg_template, 'xml')

        # Voeg aangepast device toe aan template
        target_group = soup.find('g', {'id': 'device-container'})
        if not target_group:
            raise ValueError(f"Kon geen <g id='device-container'> vinden in {template_file}.")

        target_group.append(device_root)

        for model, (width, height) in IPHONE_SIZES.items():
            # Stel viewBox in per model
            viewbox_width, viewbox_height = VIEWBOX_SIZES[model]
            viewbox = f"48 0 {viewbox_width} {viewbox_height}"

            image_x = -150 if idx == 0 else -1750
            modified_svg = customize_svg(str(soup), data, image_x=image_x, viewbox=viewbox, idx=idx)

            svg_filename = f"{data['urlScheme']}_{idx}_{model}.svg"
            with open(svg_filename, 'w') as f:
                f.write(modified_svg)

            # generate_pngs(svg_filename, f"./{data['urlScheme']}", prefix=str(idx))

            output_dir = f"./{data['urlScheme']}"
            output_path = os.path.join(output_dir, f"{idx}_APP_IPHONE_{model}_{idx}.png")
            os.makedirs(output_dir, exist_ok=True)

            cairosvg.svg2png(
                bytestring=modified_svg.encode(),
                write_to=output_path,
                output_width=width,
                output_height=height
            )

            # print(f"PNG gegenereerd: {output_path}")
            f.close()
            if os.path.exists(svg_filename):
                os.remove(svg_filename)
                # print(f"{svg_filename} is verwijderd.")
            else:
                print(f"{svg_filename} bestaat niet.")

# Zoek config-bestanden
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
