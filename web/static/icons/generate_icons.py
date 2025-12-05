#!/usr/bin/env python3
"""
PWA Icon Generator for AtomAgent
Generates all required icon sizes from a base SVG
"""

import os

# Base SVG icon
SVG_ICON = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512">
  <defs>
    <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#1e3a5f"/>
      <stop offset="100%" style="stop-color:#0a0a0f"/>
    </linearGradient>
    <linearGradient id="accent" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#60a5fa"/>
      <stop offset="100%" style="stop-color:#3b82f6"/>
    </linearGradient>
  </defs>
  <!-- Background -->
  <rect width="512" height="512" rx="96" fill="url(#bg)"/>
  <!-- Atom symbol -->
  <g transform="translate(256, 256)">
    <!-- Orbits -->
    <ellipse cx="0" cy="0" rx="140" ry="50" fill="none" stroke="url(#accent)" stroke-width="8" transform="rotate(-30)"/>
    <ellipse cx="0" cy="0" rx="140" ry="50" fill="none" stroke="url(#accent)" stroke-width="8" transform="rotate(30)"/>
    <ellipse cx="0" cy="0" rx="140" ry="50" fill="none" stroke="url(#accent)" stroke-width="8" transform="rotate(90)"/>
    <!-- Core -->
    <circle cx="0" cy="0" r="35" fill="url(#accent)"/>
    <!-- Electrons -->
    <circle cx="120" cy="-70" r="12" fill="#60a5fa"/>
    <circle cx="-120" cy="70" r="12" fill="#60a5fa"/>
    <circle cx="0" cy="140" r="12" fill="#60a5fa"/>
  </g>
</svg>'''

SIZES = [72, 96, 128, 144, 152, 192, 384, 512]

def generate_icons():
    """Generate PNG icons from SVG using PIL or save SVG"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Save base SVG
    svg_path = os.path.join(script_dir, 'icon.svg')
    with open(svg_path, 'w') as f:
        f.write(SVG_ICON)
    print(f"Created: {svg_path}")
    
    try:
        # Try using cairosvg for PNG conversion
        import cairosvg
        
        for size in SIZES:
            png_path = os.path.join(script_dir, f'icon-{size}.png')
            cairosvg.svg2png(
                bytestring=SVG_ICON.encode(),
                write_to=png_path,
                output_width=size,
                output_height=size
            )
            print(f"Created: icon-{size}.png")
            
    except ImportError:
        print("\nNote: Install cairosvg for PNG generation:")
        print("  pip install cairosvg")
        print("\nAlternatively, use an online converter or Inkscape:")
        print("  inkscape icon.svg -w SIZE -h SIZE -o icon-SIZE.png")
        
        # Create placeholder PNGs with PIL if available
        try:
            from PIL import Image, ImageDraw
            
            for size in SIZES:
                img = Image.new('RGBA', (size, size), (10, 10, 15, 255))
                draw = ImageDraw.Draw(img)
                
                # Simple circle as placeholder
                margin = size // 8
                draw.ellipse(
                    [margin, margin, size - margin, size - margin],
                    fill=(59, 130, 246, 255)
                )
                
                # Inner circle
                inner_margin = size // 3
                draw.ellipse(
                    [inner_margin, inner_margin, size - inner_margin, size - inner_margin],
                    fill=(96, 165, 250, 255)
                )
                
                png_path = os.path.join(script_dir, f'icon-{size}.png')
                img.save(png_path, 'PNG')
                print(f"Created placeholder: icon-{size}.png")
                
        except ImportError:
            print("\nNote: Install Pillow for placeholder icons:")
            print("  pip install Pillow")

if __name__ == '__main__':
    generate_icons()
    print("\nIcon generation complete!")
