from reportlab.lib.pagesizes import landscape
from reportlab.lib.units import cm, inch
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor, white, black
import os

os.chdir(r'C:\Projects\CS-584\WhenAgentsDisagree\report')

print("Creating comprehensive PDF from poster content...")

# Page size: 48" x 36" landscape
width = 48 * inch
height = 36 * inch

pdf_file = "poster.pdf"

# Colors
stevens_red = HexColor("#A32035")
stevens_gold = HexColor("#C9A84C")
bg_white = HexColor("#FFFFFF")
bg_light = HexColor("#F8F8F8")
txt_dark = HexColor("#1A1A1A")
txt_mid = HexColor("#444444")
accent_blue = HexColor("#1565C0")
accent_green = HexColor("#2E7D32")
accent_orange = HexColor("#E65100")
accent_purple = HexColor("#6A4C93")

# Create canvas
c = canvas.Canvas(pdf_file, pagesize=(width, height))
c.setTitle("When Agents Disagree - Research Symposium Poster")

# Background
c.setFillColor(bg_white)
c.rect(0, 0, width, height, fill=1, stroke=0)

# ===== HEADER SECTION =====
# Top red bar
c.setFillColor(stevens_red)
c.rect(0, height - 0.5*inch, width, 0.5*inch, fill=1, stroke=0)

# Title area
c.setFillColor(white)
c.rect(0, height - 3.5*inch, width, 3*inch, fill=1, stroke=1)
c.setStrokeColor(HexColor("#DDDDDD"))
c.setLineWidth(0.5)

# Main title
c.setFont("Helvetica-Bold", 68)
c.setFillColor(stevens_red)
c.drawCentredString(width/2, height - 1.6*inch, "WHEN AGENTS DISAGREE")

# Subtitle
c.setFont("Helvetica-Oblique", 18)
c.setFillColor(txt_mid)
c.drawCentredString(width/2, height - 2.2*inch, "LLM Conflict Resolution in Adversarial Multi-Agent Debates")

# Authors
c.setFont("Helvetica", 13)
c.setFillColor(txt_dark)
c.drawCentredString(width/2, height - 2.75*inch, "Kevin Doshi  .  Sandun Munasinghe  .  Sai Lasya Vellampalli")

# Institute
c.setFont("Helvetica", 11)
c.setFillColor(txt_mid)
c.drawCentredString(width/2, height - 3.1*inch, "Stevens Institute of Technology . CS 584 NLP . Spring 2026")

# Bottom red bar
c.setFillColor(stevens_red)
c.rect(0, 0, width, 0.5*inch, fill=1, stroke=0)

# Footer text
c.setFont("Helvetica-Bold", 10)
c.setFillColor(white)
c.drawString(0.4*inch, 0.15*inch, "STEVENS INSTITUTE OF TECHNOLOGY . CS 584 NLP . Research Symposium 2026")

# ===== HERO STAT BOXES =====
box_y = height - 4.2*inch
box_width = (width - 3*0.25*inch - 1*inch) / 3
box_height = 1.3*inch
box_x_start = 0.5*inch

boxes = [
    {
        'num': '88%',
        'title': 'MISINFORMATION WINS',
        'desc1': 'In LLM Debate Battles:',
        'desc2': 'Agent with fabricated evidence',
        'desc3': 'convinces others 88% of time',
        'stat': 'p=0.006; |d|=0.98',
        'color': stevens_red,
        'x': box_x_start
    },
    {
        'num': '100%',
        'title': 'DEBATE DEADLOCK',
        'desc1': 'Of Structured Debates:',
        'desc2': 'Every 5-round exchange',
        'desc3': 'ended in stalemate',
        'stat': 'All 8 debates deadlocked',
        'color': accent_purple,
        'x': box_x_start + box_width + 0.25*inch
    },
    {
        'num': '75%',
        'title': 'HIERARCHY WINS',
        'desc1': 'Accuracy for Strategy:',
        'desc2': 'Lead agent decides after',
        'desc3': 'hearing briefings',
        'stat': 'vs 50% majority voting',
        'color': accent_green,
        'x': box_x_start + 2*(box_width + 0.25*inch)
    }
]

for box in boxes:
    # Box background
    c.setFillColor(bg_light)
    c.setStrokeColor(box['color'])
    c.setLineWidth(2)
    c.rect(box['x'], box_y, box_width, box_height, fill=1, stroke=1)

    # Header bar
    c.setFillColor(box['color'])
    c.rect(box['x'], box_y + box_height - 0.35*inch, box_width, 0.35*inch, fill=1, stroke=0)

    # Title
    c.setFont("Helvetica-Bold", 10)
    c.setFillColor(white)
    c.drawCentredString(box['x'] + box_width/2, box_y + box_height - 0.18*inch, box['title'])

    # Number
    c.setFont("Helvetica-Bold", 44)
    c.setFillColor(box['color'])
    c.drawCentredString(box['x'] + box_width/2, box_y + 0.7*inch, box['num'])

    # Description
    c.setFont("Helvetica", 9)
    c.setFillColor(txt_dark)
    c.drawString(box['x'] + 0.1*inch, box_y + 0.55*inch, box['desc1'])
    c.drawString(box['x'] + 0.1*inch, box_y + 0.38*inch, box['desc2'])
    c.drawString(box['x'] + 0.1*inch, box_y + 0.21*inch, box['desc3'])

    # Stats
    c.setFont("Helvetica", 8)
    c.setFillColor(txt_mid)
    c.drawString(box['x'] + 0.1*inch, box_y + 0.05*inch, box['stat'])

# ===== CONTENT SECTIONS =====
content_y = box_y - 0.3*inch
section_height = (content_y - 1*inch) / 2
col_width = width / 4

sections = [
    ('1', 'FIGHTERS', 'Character\nintroductions', accent_blue),
    ('2', 'ARENA', 'Problem\nstatement', stevens_red),
    ('3', 'MODES', '4 conflict\nstrategies', stevens_gold),
    ('4', 'SETUP', 'Experimental\nconfiguration', accent_blue),
    ('5', 'DNA', '10-dim\nfingerprints', accent_purple),
    ('6', 'BOARD', 'Strategy\naccuracy', stevens_gold),
    ('7', 'ABLATION', 'Deadlock\nanalysis', accent_orange),
    ('8', 'MISINFO', 'Fabricated\nevidence', stevens_red),
    ('9', 'PARADOX', 'Source\nreliability', accent_purple),
    ('10', 'STATS', 'Statistical\ntests', accent_blue),
    ('11', 'PRIOR', 'Novelty\ncomparison', accent_green),
    ('12', 'LIMITS', 'Honest\nlimitations', txt_mid),
    ('13', 'WHY', 'Safety &\ndeployment', stevens_red),
    ('14', 'TEAM', 'Authors &\nrefs', accent_purple),
]

for i, (num, title, desc, color) in enumerate(sections):
    col = i % 4
    row = i // 4

    x = col * col_width + 0.3*inch
    y = content_y - row * section_height - section_height + 0.4*inch

    if y > 0.8*inch:
        # Section box
        c.setFillColor(bg_light)
        c.setStrokeColor(color)
        c.setLineWidth(1.5)
        c.rect(x, y - 0.5*inch, col_width - 0.6*inch, section_height - 0.2*inch, fill=1, stroke=1)

        # Number + Title bar
        c.setFillColor(color)
        c.rect(x, y - 0.35*inch, col_width - 0.6*inch, 0.35*inch, fill=1, stroke=0)

        c.setFont("Helvetica-Bold", 11)
        c.setFillColor(white)
        text = f"{num} {title}"
        c.drawString(x + 0.1*inch, y - 0.2*inch, text)

        # Description
        c.setFont("Helvetica", 8.5)
        c.setFillColor(txt_dark)
        desc_lines = desc.split('\n')
        desc_y = y - 0.55*inch
        for line in desc_lines:
            c.drawString(x + 0.15*inch, desc_y, line)
            desc_y -= 0.2*inch

c.save()

final_size = os.path.getsize(pdf_file)
print(f"\nSUCCESS: PDF created!")
print(f"File: {os.path.abspath(pdf_file)}")
print(f"Size: {final_size} bytes ({final_size/1024:.1f} KB)")
print(f"\nLaTeX source (poster.tex): {os.path.getsize('poster.tex')} bytes")
print("\nTo generate the full LaTeX-compiled PDF:")
print("  - Use Overleaf.com (easiest)")
print("  - Install MikTeX or TeX Live locally")
print("  - See COMPILE_POSTER.md for detailed instructions")
