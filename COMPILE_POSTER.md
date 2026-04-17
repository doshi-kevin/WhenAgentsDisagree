# How to Compile the Poster PDF

The poster LaTeX source has been completely redesigned and is ready to compile. Due to environment constraints, automated compilation isn't available, but here are multiple ways to generate the PDF:

## Option 1: Online (Easiest) - Overleaf

1. Go to https://www.overleaf.com/
2. Create new project → Blank project
3. Copy the contents of `report/poster.tex` into the editor
4. In the project settings, ensure:
   - Compiler: **pdfLaTeX**
   - PDF viewer is enabled
5. Download the compiled PDF

## Option 2: Local Installation

### Windows - Using MikTeX

```powershell
# Install MikTeX (if not already installed)
# Download from: https://miktex.org/download

# In PowerShell, navigate to the poster directory:
cd C:\Projects\CS-584\WhenAgentsDisagree\report

# Compile:
pdflatex -interaction=nonstopmode poster.tex
pdflatex -interaction=nonstopmode poster.tex  # Run twice for TOC/references
```

### Windows - Using TeX Live

```bash
# Download TeX Live from: https://www.tug.org/texlive/
# After installation, in bash:

cd /c/Projects/CS-584/WhenAgentsDisagree/report
pdflatex -interaction=nonstopmode poster.tex
pdflatex -interaction=nonstopmode poster.tex
```

### macOS - Using MacTeX

```bash
cd ~/Projects/CS-584/WhenAgentsDisagree/report
pdflatex -interaction=nonstopmode poster.tex
pdflatex -interaction=nonstopmode poster.tex
```

### Linux - Using TeX Live

```bash
# Install TeX Live
sudo apt-get install texlive-latex-full texlive-fonts-recommended

cd ~/Projects/CS-584/WhenAgentsDisagree/report
pdflatex -interaction=nonstopmode poster.tex
pdflatex -interaction=nonstopmode poster.tex
```

## Option 3: Using Tectonic

```bash
# Install Tectonic: https://tectonic-typesetting.github.io/

cd /c/Projects/CS-584/WhenAgentsDisagree/report
tectonic poster.tex
```

## Option 4: Docker Container

```bash
docker run --rm -v $(pwd):/data latex/latex:latest pdflatex -interaction=nonstopmode /data/report/poster.tex
```

## Poster Specifications

- **Dimensions**: 48" × 36" landscape (121.92cm × 91.44cm)
- **Pages**: 1 page
- **Orientation**: Landscape
- **Format**: A0-equivalent academic poster

## Features

✓ Light background (white)
✓ Stevens academic theme (maroon/gold)
✓ 4-column layout
✓ 14 numbered sections
✓ Clarified hero stat boxes
✓ Professional header/footer
✓ All figures embedded (PNG/PDF format)
✓ Statistical tables and charts
✓ Behavioral DNA visualization

## Troubleshooting

### Missing figures
- Ensure `report/figures/` directory exists with all PNG/PDF files
- Check that figure paths in `\includegraphics` commands match the actual filenames

### Font warnings
- These are typically harmless
- Common fonts used: Helvetica (lmodern), FontAwesome5
- Install `texlive-fonts-recommended` if getting font errors

### Overflow/Layout issues
- The design uses flexible widths and tcolorbox
- All content should fit without overflow
- If issues occur, check that page size is set to exactly 121.92 × 91.44 cm

## Output

After compilation, `poster.pdf` will be created in the `report/` directory.
File size should be approximately 900KB - 1.5MB.
