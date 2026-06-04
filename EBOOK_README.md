# PocketFlow Creator Ebook

## Available Formats

The comprehensive "Learn PocketFlow and PocketFlow Creator" ebook is available in multiple formats:

### 1. **Markdown Format** (Source)
- **File:** `Learn_PocketFlow_Creator.md`
- **Size:** 376 KB
- **Use:** Raw source for conversion or reading in any markdown viewer
- **Preview:** GitHub, GitBook, or any markdown editor

### 2. **HTML Format** (Recommended for reading)
- **File:** `Learn_PocketFlow_Creator.html`
- **Size:** 796 KB
- **Use:** Open in any web browser
- **Features:** 
  - Interactive table of contents
  - Syntax-highlighted code blocks
  - Searchable text
  - Mobile-friendly layout

### 3. **PDF Format** (Print-friendly)
To create a PDF version, choose one of the following methods:

#### Method A: Using Your Web Browser (Easiest)
1. Open `Learn_PocketFlow_Creator.html` in your web browser
2. Press `Ctrl+P` (Windows/Linux) or `Cmd+P` (Mac)
3. Select "Save as PDF"
4. Choose your preferred settings and save

#### Method B: Using Online Conversion Tools
1. Visit [CloudConvert.com](https://cloudconvert.com/) or similar service
2. Upload `Learn_PocketFlow_Creator.html`
3. Select PDF as output format
4. Download the converted PDF

#### Method C: Using Command Line Tools

**Option 1: wkhtmltopdf (Linux/Mac)**
```bash
# Install wkhtmltopdf
sudo apt-get install wkhtmltopdf  # Linux
brew install wkhtmltopdf          # Mac

# Convert to PDF
wkhtmltopdf Learn_PocketFlow_Creator.html Learn_PocketFlow_Creator.pdf
```

**Option 2: Pandoc with LaTeX (if you have LaTeX installed)**
```bash
# Install LaTeX
sudo apt-get install texlive-xetex  # Linux

# Convert with pandoc
pandoc Learn_PocketFlow_Creator.md -o Learn_PocketFlow_Creator.pdf --toc
```

**Option 3: Chromium/Chrome CLI**
```bash
# Using chromium
chromium --headless --disable-gpu --print-to-pdf=Learn_PocketFlow_Creator.pdf Learn_PocketFlow_Creator.html

# Or using chrome
google-chrome --headless --disable-gpu --print-to-pdf=Learn_PocketFlow_Creator.pdf Learn_PocketFlow_Creator.html
```

## Contents Overview

This comprehensive ebook covers:

### Part 0: Foundations
- Chapter 1: What is PocketFlow?
- Chapter 2: What is PocketFlow Creator?

### Part 1: Getting Started  
- Chapter 3: Installation and Setup
- Chapter 4: Your First Flow

### Part 2: Tutorials and Learning
- Part 1: Fundamentals
- Part 2: Patterns
- Part 3: Advanced Topics
- Part 4: Exercises

### Part 3: Advanced Topics
- Hardware I/O Integration (USB Serial, Audio, Video, Webcam)
- Standalone Python Scripts (Export, Deployment, CI/CD)

### Part 4: Reference
- All 76 Node Types with Properties and Examples
- UI Reference (Canvas, Palette, Inspector, Code Editor, etc.)
- Custom Nodes Guide
- Quick Reference

## Total Content

- **10,326 lines** of comprehensive documentation
- **376 KB** markdown source
- **80+ tutorials and guides**
- **76 node types** fully documented
- **50+ examples** with code snippets

## Getting Started

**For Web Reading (Recommended):**
```bash
# Open in your default browser
open Learn_PocketFlow_Creator.html    # Mac
xdg-open Learn_PocketFlow_Creator.html # Linux
start Learn_PocketFlow_Creator.html   # Windows
```

**For Markdown Editing:**
- Use any markdown editor (VS Code, Obsidian, etc.)
- Perfect for searching and indexing
- Source for all conversions

## Feedback

If you find errors or have suggestions for improvements, please:
1. Open an issue on GitHub
2. Submit a pull request with corrections
3. Provide feedback on clarity or completeness

---

**Created with ❤️ by the PocketFlow Creator Community**

Last updated: June 2026
