# PowerOFF-Maker
# Copyright (C) 2025 MetaOne
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import os
import re
import json
import textwrap
from PIL import Image, ImageDraw, ImageFont
import argparse
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BBCodeParser:
    def __init__(self):
        self.size_pattern = re.compile(r'\[size=(\d+)\](.*?)\[/size\]', re.DOTALL)
        self.color_pattern = re.compile(r'\[color=(#[0-9a-fA-F]{6}|#[0-9a-fA-F]{3})\](.*?)\[/color\]', re.DOTALL)

    def parse(self, text):
        if not ('[size=' in text or '[color=' in text):
            return [{'text': text, 'size': 20, 'color': '#FFFFFF'}]

        segments = []

        while text:
            size_match = self.size_pattern.search(text)
            color_match = self.color_pattern.search(text)

            size_pos = size_match.start() if size_match else float('inf')
            color_pos = color_match.start() if color_match else float('inf')

            if size_pos == float('inf') and color_pos == float('inf'):
                if text.strip():
                    segments.append({'text': text, 'size': 20, 'color': '#FFFFFF'})
                break

            if min(size_pos, color_pos) > 0:
                pre_text = text[:min(size_pos, color_pos)]
                if pre_text.strip():
                    segments.append({'text': pre_text, 'size': 20, 'color': '#FFFFFF'})

            if size_pos < color_pos:
                size = int(size_match.group(1))
                inner_text = size_match.group(2)

                inner_color_match = self.color_pattern.search(inner_text)
                if inner_color_match:
                    color = inner_color_match.group(1)
                    colored_text = inner_color_match.group(2)
                    segments.append({'text': colored_text, 'size': size, 'color': color})
                    inner_text = inner_text.replace(inner_color_match.group(0), '')
                    if inner_text.strip():
                        segments.append({'text': inner_text, 'size': size, 'color': '#FFFFFF'})
                else:
                    segments.append({'text': inner_text, 'size': size, 'color': '#FFFFFF'})

                text = text[size_match.end():]
            else:
                color = color_match.group(1)
                inner_text = color_match.group(2)

                inner_size_match = self.size_pattern.search(inner_text)
                if inner_size_match:
                    size = int(inner_size_match.group(1))
                    sized_text = inner_size_match.group(2)
                    segments.append({'text': sized_text, 'size': size, 'color': color})
                    inner_text = inner_text.replace(inner_size_match.group(0), '')
                    if inner_text.strip():
                        segments.append({'text': inner_text, 'size': 20, 'color': color})
                else:
                    segments.append({'text': inner_text, 'size': 20, 'color': color})

                text = text[color_match.end():]

        return segments

class ImageCreator:
    def __init__(self, config='config.json'):
        self.ensure_directories()
        self.create_default_config(config)
        self.load_config(config)
        self.bbcode_parser = BBCodeParser()

    def create_default_config(self, config):
        if not os.path.exists(config):
            default_config = {
                "image": {
                    "width": 1200,
                    "height": 675,
                    "background": "background.png"
                },
                "text": {
                    "file": "text.txt",
                    "position": {"x": 20, "y": 420},
                    "max_width": 800,
                    "default_font": "Montserrat-Regular.ttf",
                    "default_size": 20,
                    "default_color": "#FFFFFF"
                },
                "title": {
                    "text": "OPERATION ANTIFRAP",
                    "position": {"x": 20, "y": 360},
                    "font": "Montserrat-Bold.ttf",
                    "size": 40,
                    "color": "#FFFFFF"
                },
                "icons": {
                    "position": {"x": 1190, "y": 10},
                    "spacing": 100,
                    "size": 96
                }
            }

            with open(config, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=2)

            logger.info(f"Default configuration file created: {config}")

    def load_config(self, config):
        try:
            with open(config, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
            logger.info(f"Configuration loaded from {config}")
        except FileNotFoundError:
            logger.warning(f"Configuration file not found: {config}.")

    def ensure_directories(self):
        os.makedirs('assets', exist_ok=True)
        os.makedirs('assets/fonts', exist_ok=True)
        os.makedirs('assets/backgrounds', exist_ok=True)
        os.makedirs('assets/icons', exist_ok=True)

    def get_text(self, text_file):
        try:
            with open(os.path.join('assets', text_file), 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            logger.error(f"Text file not found: {text_file}")
            return "Text file not found!"

    def list_icons(self):
        icons_dir = 'assets/icons'
        if not os.path.exists(icons_dir):
            return []
        icons = [f for f in os.listdir(icons_dir) if os.path.isfile(os.path.join(icons_dir, f))]
        return icons

    def create_image(self, output_path='output.png'):
        width = self.config['image']['width']
        height = self.config['image']['height']

        try:
            bg_path = os.path.join('assets/backgrounds', self.config['image']['background'])
            background = Image.open(bg_path).convert('RGBA')
            background = background.resize((width, height))
        except FileNotFoundError:
            logger.warning(f"Background image not found: {bg_path}.")

        img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        title_config = self.config['title']
        try:
            title_font = ImageFont.truetype(
                os.path.join('assets/fonts', title_config['font']),
                title_config['size']
            )
        except (OSError, FileNotFoundError):
            logger.warning(f"Title font not found: {title_config['font']}.")
            title_font = ImageFont.load_default()

        draw.text(
            (title_config['position']['x'], title_config['position']['y']),
            title_config['text'],
            fill=title_config['color'],
            font=title_font
        )

        config = self.config['text']
        text_content = self.get_text(config['file'])
        text_segments = self.bbcode_parser.parse(text_content)

        x = config['position']['x']
        y = config['position']['y']
        max_width = config.get('max_width', width - x - 20)

        for segment in text_segments:
            try:
                font = ImageFont.truetype(
                    os.path.join('assets/fonts', config.get('default_font', 'Montserrat-Regular.ttf')),
                    segment['size']
                )
            except (OSError, FileNotFoundError):
                logger.warning(f"Font not found.")
                font = ImageFont.load_default()

            wrapped_text = textwrap.fill(segment['text'], width=int(max_width / (segment['size'] / 2)))
            draw.text((x, y), wrapped_text, fill=segment['color'], font=font)

            left, top, right, bottom = font.getbbox(wrapped_text)
            y += bottom - top + 2

        icons_config = self.config['icons']
        icons = self.list_icons()

        x = icons_config['position']['x']
        y = icons_config['position']['y']
        size = icons_config['size']
        spacing = icons_config['spacing']

        for icon_file in icons:
            try:
                icon = Image.open(os.path.join('assets/icons', icon_file)).convert('RGBA')
                icon = icon.resize((size, size))
                img.paste(icon, (x - size, y), icon)
                y += spacing
            except Exception as e:
                logger.error(f"Error loading icon {icon_file}: {e}")

        final_img = Image.alpha_composite(background, img)

        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

        final_img.convert('RGB').save(output_path)
        logger.info(f"Image created: {output_path}")
        return output_path

parser = argparse.ArgumentParser()
parser.add_argument('--config', default='config.json', help='Path to configuration file')
parser.add_argument('--output', default='output.png', help='Path to save image')
args = parser.parse_args()

creator = ImageCreator(args.config).create_image(args.output)
