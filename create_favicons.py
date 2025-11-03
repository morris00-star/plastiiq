from PIL import Image, ImageDraw, ImageFont
import os


def create_favicons():
    """Create favicon files in different sizes"""

    # Create static/images directory if it doesn't exist
    os.makedirs('static/images', exist_ok=True)

    # Sizes needed for different devices
    sizes = {
        'favicon.ico': (32, 32),  # ICO format for legacy support
        'favicon-16x16.png': (16, 16),
        'favicon-32x32.png': (32, 32),
        'apple-touch-icon.png': (180, 180),
        'android-chrome-192x192.png': (192, 192),
        'android-chrome-512x512.png': (512, 512),
        'mstile-70x70.png': (70, 70),
        'mstile-150x150.png': (150, 150),
        'mstile-310x150.png': (310, 150),
        'mstile-310x310.png': (310, 310),
    }

    print("Creating favicon files...")

    for filename, size in sizes.items():
        # Create image with gradient background
        img = Image.new('RGBA', size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # Draw gradient background (blue to purple)
        width, height = size
        for i in range(width):
            # Blue (#667eea) to Purple (#764ba2) gradient
            r = int(102 + (118 - 102) * i / width)
            g = int(126 + (74 - 126) * i / width)
            b = int(234 + (162 - 234) * i / width)
            draw.line([(i, 0), (i, height)], fill=(r, g, b, 255))

        # Draw calculator icon
        if width >= 32:  # Only draw detailed icon for larger sizes
            # Draw calculator body (white rectangle)
            margin = width // 8
            body_coords = [margin, margin, width - margin, height - margin]
            draw.rounded_rectangle(body_coords, radius=width // 16, fill=(255, 255, 255, 220),
                                   outline=(255, 255, 255, 255))

            # Draw display (dark rectangle)
            display_margin = width // 6
            display_height = height // 4
            display_coords = [display_margin, display_margin, width - display_margin, display_margin + display_height]
            draw.rounded_rectangle(display_coords, radius=width // 32, fill=(40, 40, 40, 255))

            # Draw buttons for larger icons
            if width >= 70:
                button_size = width // 10
                button_margin = width // 8

                # Draw 3x3 grid of buttons
                for row in range(3):
                    for col in range(3):
                        x1 = button_margin + col * (button_size + 2)
                        y1 = display_margin + display_height + button_margin + row * (button_size + 2)
                        x2 = x1 + button_size
                        y2 = y1 + button_size
                        draw.rounded_rectangle([x1, y1, x2, y2], radius=button_size // 4, fill=(200, 200, 200, 255))

        # Special handling for ICO file
        if filename == 'favicon.ico':
            # Convert to RGB for ICO format
            rgb_img = Image.new('RGB', size, (255, 255, 255))
            rgb_img.paste(img, (0, 0), img)
            rgb_img.save(f'static/images/{filename}')
        else:
            img.save(f'static/images/{filename}')

        print(f"✅ Created: static/images/{filename} ({size[0]}x{size[1]})")

    print("\n🎉 All favicon files created successfully!")
    print("📁 Files are saved in: static/images/")


def create_safari_pinned_tab():
    """Create SVG for Safari pinned tab"""
    svg_content = '''<svg width="32" height="32" viewBox="0 0 32 32" xmlns="http://www.w3.org/2000/svg">
    <defs>
        <linearGradient id="gradient" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" style="stop-color:#667eea;stop-opacity:1" />
            <stop offset="100%" style="stop-color:#764ba2;stop-opacity:1" />
        </linearGradient>
    </defs>
    <rect width="32" height="32" rx="8" fill="url(#gradient)"/>
    <rect x="6" y="6" width="20" height="20" rx="4" fill="white" opacity="0.9"/>
    <rect x="8" y="8" width="16" height="6" fill="#333" rx="2"/>
    <circle cx="12" cy="18" r="2" fill="#666"/>
    <circle cx="18" cy="18" r="2" fill="#666"/>
    <circle cx="24" cy="18" r="2" fill="#666"/>
    <circle cx="12" cy="24" r="2" fill="#666"/>
    <circle cx="18" cy="24" r="2" fill="#666"/>
    <circle cx="24" cy="24" r="2" fill="#666"/>
</svg>'''

    with open('static/images/safari-pinned-tab.svg', 'w') as f:
        f.write(svg_content)
    print("✅ Created: static/images/safari-pinned-tab.svg")


if __name__ == "__main__":
    create_favicons()
    create_safari_pinned_tab()
