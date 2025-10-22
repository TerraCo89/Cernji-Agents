# Advanced Claude Skills Examples

Comprehensive code examples for building production-ready skills with Claude.

## Table of Contents
- [Document Generation](#document-generation)
- [Data Processing](#data-processing)
- [MCP Server Integration](#mcp-server-integration)
- [Algorithmic Art](#algorithmic-art)
- [Animation & GIFs](#animation--gifs)

---

## Document Generation

### Excel with Formulas and Formatting (openpyxl)

```python
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
import subprocess

wb = Workbook()
sheet = wb.active
sheet.title = "Q4 Sales"

# Headers with formatting
sheet['A1'] = 'Product'
sheet['B1'] = 'Units Sold'
sheet['C1'] = 'Revenue'
sheet['D1'] = 'Growth %'

header_font = Font(bold=True, color='FFFFFF')
header_fill = PatternFill('solid', start_color='0066CC')

for cell in ['A1', 'B1', 'C1', 'D1']:
    sheet[cell].font = header_font
    sheet[cell].fill = header_fill
    sheet[cell].alignment = Alignment(horizontal='center')

# Data with color coding (blue = input, black = formula)
sheet['A2'] = 'Widget A'
sheet['B2'] = 1200  # Input: blue text
sheet['B2'].font = Font(color='0000FF')
sheet['C2'] = 48000  # Input: blue text
sheet['C2'].font = Font(color='0000FF')
sheet['D2'] = '=(C2/C$7)-1'  # Formula: black text

sheet['A3'] = 'Widget B'
sheet['B3'] = 850
sheet['B3'].font = Font(color='0000FF')
sheet['C3'] = 34000
sheet['C3'].font = Font(color='0000FF')
sheet['D3'] = '=(C3/C$8)-1'

# Totals with formulas
sheet['A5'] = 'Total'
sheet['B5'] = '=SUM(B2:B3)'
sheet['C5'] = '=SUM(C2:C3)'

# Format numbers
sheet['C2'].number_format = '$#,##0;($#,##0);-'
sheet['C3'].number_format = '$#,##0;($#,##0);-'
sheet['C5'].number_format = '$#,##0;($#,##0);-'
sheet['D2'].number_format = '0.0%'
sheet['D3'].number_format = '0.0%'

# Column width
sheet.column_dimensions['A'].width = 20

wb.save('sales_report.xlsx')

# CRITICAL: Recalculate formulas
subprocess.run(['python', 'recalc.py', 'sales_report.xlsx'], check=True)
```

### PDF with ReportLab (Multi-page)

```python
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

doc = SimpleDocTemplate("report.pdf", pagesize=letter)
styles = getSampleStyleSheet()
story = []

# Page 1: Title and Introduction
title = Paragraph("Q4 2024 Financial Report", styles['Title'])
story.append(title)
story.append(Spacer(1, 12))

body_text = """Revenue grew 15% year-over-year to $2.5M.
Operating expenses decreased 8% while maintaining service quality."""
body = Paragraph(body_text, styles['Normal'])
story.append(body)
story.append(PageBreak())

# Page 2: Regional Breakdown
story.append(Paragraph("Regional Breakdown", styles['Heading1']))
story.append(Paragraph("North America: $1.2M (+12%)", styles['Normal']))
story.append(Paragraph("Europe: $0.9M (+20%)", styles['Normal']))
story.append(Paragraph("Asia-Pacific: $0.4M (+15%)", styles['Normal']))
story.append(Spacer(1, 20))

# Page 3: Table
data = [
    ['Product', 'Q1', 'Q2', 'Q3', 'Q4'],
    ['Widgets', '120', '135', '142', '158'],
    ['Gadgets', '85', '92', '98', '105']
]

table = Table(data)
table.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
    ('FONTSIZE', (0, 0), (-1, 0), 14),
    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
    ('GRID', (0, 0), (-1, -1), 1, colors.black)
]))
story.append(table)

doc.build(story)
```

### Word Document with Lists (docx-js)

```javascript
const { Document, Paragraph, TextRun, AlignmentType, UnderlineType, LevelFormat } = require('docx');

const doc = new Document({
  numbering: {
    config: [
      {
        reference: "bullet-list",
        levels: [
          {
            level: 0,
            format: LevelFormat.BULLET,
            text: "•",
            alignment: AlignmentType.LEFT,
            style: {
              paragraph: {
                indent: { left: 720, hanging: 360 }
              }
            }
          }
        ]
      },
      {
        reference: "numbered-list",
        levels: [
          {
            level: 0,
            format: LevelFormat.DECIMAL,
            text: "%1.",
            alignment: AlignmentType.LEFT,
            style: {
              paragraph: {
                indent: { left: 720, hanging: 360 }
              }
            }
          }
        ]
      }
    ]
  },
  styles: {
    default: {
      document: { run: { font: "Arial", size: 24 } } // 12pt
    },
    paragraphStyles: [
      {
        id: "Title",
        name: "Title",
        basedOn: "Normal",
        run: { size: 56, bold: true, color: "000000", font: "Arial" },
        paragraph: { spacing: { before: 240, after: 120 }, alignment: AlignmentType.CENTER }
      }
    ]
  },
  sections: [{
    properties: {
      page: { margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 } }
    },
    children: [
      new Paragraph({
        heading: HeadingLevel.TITLE,
        children: [new TextRun("Document Title")]
      }),
      new Paragraph({
        numbering: { reference: "bullet-list", level: 0 },
        children: [new TextRun("First bullet point")]
      }),
      new Paragraph({
        numbering: { reference: "bullet-list", level: 0 },
        children: [new TextRun("Second bullet point")]
      }),
      new Paragraph({
        numbering: { reference: "numbered-list", level: 0 },
        children: [new TextRun("First numbered item")]
      }),
      new Paragraph({
        numbering: { reference: "numbered-list", level: 0 },
        children: [new TextRun("Second numbered item")]
      })
    ]
  }]
});

// ⚠️ CRITICAL: Each reference creates an INDEPENDENT numbered list
// Same reference = continues numbering (1, 2, 3... then 4, 5, 6...)
// Different reference = restarts at 1 (1, 2, 3... then 1, 2, 3...)

// ⚠️ NEVER use unicode bullets - always use LevelFormat.BULLET
```

### PowerPoint with Charts (PptxGenJS)

```javascript
const pptxgen = require('pptxgenjs');

const pptx = new pptxgen();
pptx.layout = 'LAYOUT_16x9';
pptx.author = 'Your Name';
pptx.title = 'Q4 Sales Report';

// Slide 1: Title
const slide1 = pptx.addSlide();
slide1.addText('Q4 2024 Sales Report', {
  x: 1, y: 2, w: 8, h: 1,
  fontSize: 44, bold: true, align: 'center'
});

// Slide 2: Bar Chart
const slide2 = pptx.addSlide();
slide2.addText('Quarterly Sales', { x: 0.5, y: 0.5, fontSize: 24, bold: true });

const chartData = [{
  name: 'Sales 2024',
  labels: ['Q1', 'Q2', 'Q3', 'Q4'],
  values: [4500, 5500, 6200, 7100]
}];

slide2.addChart(pptx.charts.BAR, chartData, {
  x: 1, y: 1.5, w: 8, h: 4,
  barDir: 'col',  // Vertical bars
  showTitle: true,
  title: 'Quarterly Sales Performance',
  showLegend: false,
  showCatAxisTitle: true,
  catAxisTitle: 'Quarter',
  showValAxisTitle: true,
  valAxisTitle: 'Sales ($000s)',
  valAxisMaxVal: 8000,
  valAxisMinVal: 0,
  valAxisMajorUnit: 2000,
  dataLabelPosition: 'outEnd',
  chartColors: ["4472C4"]
});

// Slide 3: Table
const slide3 = pptx.addSlide();
const tableData = [
  [
    { text: "Product", options: { fill: { color: "4472C4" }, color: "FFFFFF", bold: true } },
    { text: "Revenue", options: { fill: { color: "4472C4" }, color: "FFFFFF", bold: true } },
    { text: "Growth", options: { fill: { color: "4472C4" }, color: "FFFFFF", bold: true } }
  ],
  ["Product A", "$50M", "+15%"],
  ["Product B", "$35M", "+22%"],
  ["Product C", "$28M", "+8%"]
];

slide3.addTable(tableData, {
  x: 1, y: 1.5, w: 8, h: 3,
  colW: [3, 2.5, 2.5],
  rowH: [0.5, 0.6, 0.6, 0.6],
  border: { pt: 1, color: "CCCCCC" },
  align: "center",
  valign: "middle",
  fontSize: 14
});

// Save
pptx.writeFile({ fileName: 'sales_report.pptx' });
```

---

## Data Processing

### PDF Manipulation (pypdf)

```python
from pypdf import PdfReader, PdfWriter

# Merge multiple PDFs
writer = PdfWriter()
for pdf_file in ["doc1.pdf", "doc2.pdf", "doc3.pdf"]:
    reader = PdfReader(pdf_file)
    for page in reader.pages:
        writer.add_page(page)

with open("merged.pdf", "wb") as output:
    writer.write(output)

# Split PDF into individual pages
reader = PdfReader("input.pdf")
for i, page in enumerate(reader.pages):
    writer = PdfWriter()
    writer.add_page(page)
    with open(f"page_{i+1}.pdf", "wb") as output:
        writer.write(output)

# Rotate pages
reader = PdfReader("input.pdf")
writer = PdfWriter()
page = reader.pages[0]
page.rotate(90)  # 90 degrees clockwise
writer.add_page(page)

with open("rotated.pdf", "wb") as output:
    writer.write(output)
```

### DOCX to Markdown (Pandoc)

```bash
# Convert document to markdown with tracked changes
pandoc --track-changes=all path-to-file.docx -o output.md

# Options:
# --track-changes=accept  (accept all changes)
# --track-changes=reject  (reject all changes)
# --track-changes=all     (show all changes)

# Extract images from DOCX
pandoc document.docx --extract-media=./images -o output.md
```

---

## MCP Server Integration

### TypeScript MCP Server with GitHub Search

```typescript
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";

const server = new Server(
  { name: "github-server", version: "1.0.0" },
  { capabilities: { tools: {} } }
);

// Input validation with Zod
const SearchReposInput = z.object({
  query: z.string().describe("Search query (e.g., 'language:python stars:>100')"),
  per_page: z.number().min(1).max(100).default(10).describe("Results per page (1-100)"),
}).strict();

// Tool registration
server.registerTool({
  name: "search_repositories",
  description: "Search GitHub repositories with filters",
  inputSchema: {
    type: "object",
    properties: {
      query: { type: "string", description: "Search query" },
      per_page: { type: "number", description: "Results per page (1-100)" },
    },
    required: ["query"],
  },
  annotations: {
    readOnlyHint: true,
    openWorldHint: true,
  },
}, async (args) => {
  const { query, per_page } = SearchReposInput.parse(args);

  try {
    const response = await fetch(
      `https://api.github.com/search/repositories?q=${encodeURIComponent(query)}&per_page=${per_page}`,
      {
        headers: {
          "Accept": "application/vnd.github.v3+json",
          "User-Agent": "MCP-GitHub-Server",
        },
      }
    );

    if (!response.ok) {
      throw new Error(`GitHub API error: ${response.statusText}`);
    }

    const data = await response.json();
    const repos = data.items.map((repo: any) => ({
      name: repo.full_name,
      stars: repo.stargazers_count,
      url: repo.html_url,
      description: repo.description || "No description",
    }));

    return {
      content: [{ type: "text", text: JSON.stringify(repos, null, 2) }],
    };

  } catch (error) {
    return {
      content: [{ type: "text", text: `Error: ${error.message}` }],
      isError: true,
    };
  }
});

// Start server
const transport = new StdioServerTransport();
await server.connect(transport);
```

### Pydantic Input Validation (Python MCP)

```python
from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import Optional
from enum import Enum

class ResponseFormat(str, Enum):
    MARKDOWN = "MARKDOWN"
    JSON = "JSON"

class UserSearchInput(BaseModel):
    """Input model for user search operations."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True
    )

    query: str = Field(
        ...,
        description="Search string to match against names/emails",
        min_length=2,
        max_length=200
    )
    limit: Optional[int] = Field(
        default=20,
        description="Maximum results to return",
        ge=1,
        le=100
    )
    offset: Optional[int] = Field(
        default=0,
        description="Number of results to skip for pagination",
        ge=0
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format"
    )

    @field_validator('query')
    @classmethod
    def validate_query(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Query cannot be empty or whitespace only")
        return v.strip()

# Tool function with comprehensive docstring
async def search_users(params: UserSearchInput) -> str:
    '''
    Search for users in the Example system by name, email, or team.

    This tool searches across all user profiles in the Example platform,
    supporting partial matches and various search filters.

    Args:
        params (UserSearchInput): Validated input parameters containing:
            - query (str): Search string to match against names/emails
            - limit (Optional[int]): Maximum results to return (default: 20)
            - offset (Optional[int]): Results to skip for pagination (default: 0)

    Returns:
        str: JSON-formatted string containing search results

    Examples:
        - "Find all marketing team members" -> query="team:marketing"
        - "Search for John's account" -> query="john"

    Error Handling:
        - Returns "Error: Rate limit exceeded" if too many requests
        - Returns "Error: Invalid API authentication" if API key invalid
        - Returns "No users found matching 'query'" if no results
    '''
    # Implementation here
    pass
```

---

## Algorithmic Art

### Interactive p5.js Template

```html
<!DOCTYPE html>
<html>
<head>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/p5.js/1.7.0/p5.min.js"></script>
  <style>
    body { margin: 0; padding: 20px; font-family: Arial; }
    #canvas-container { margin-bottom: 20px; }
    #controls { display: flex; gap: 15px; flex-wrap: wrap; }
    .control { display: flex; flex-direction: column; gap: 5px; }
  </style>
</head>
<body>
  <div id="canvas-container"></div>
  <div id="controls">
    <!-- Parameter controls will be added here -->
  </div>
  <script>
    let params = {
      seed: 12345,  // Always include seed for reproducibility
      // Add algorithm-specific parameters:
      // - Quantities (how many?)
      // - Scales (how big? how fast?)
      // - Probabilities (how likely?)
      // - Ratios (what proportions?)
      // - Angles (what direction?)
      // - Thresholds (when does behavior change?)
    };

    function setup() {
      let canvas = createCanvas(800, 800);
      canvas.parent('canvas-container');
      randomSeed(params.seed);
      noLoop();
    }

    function draw() {
      background(255);
      // Your algorithm here
    }

    // Regenerate with new seed
    function regenerate() {
      params.seed = Math.floor(Math.random() * 1000000);
      randomSeed(params.seed);
      redraw();
    }
  </script>
</body>
</html>
```

---

## Animation & GIFs

### GIF Builder with Easing Functions

```python
from PIL import Image, ImageDraw
import math

class GIFBuilder:
    def __init__(self, width, height, fps):
        self.width = width
        self.height = height
        self.fps = fps
        self.frames = []

    def add_frame(self, frame):
        self.frames.append(frame)

    def save(self, filename, num_colors=256, optimize_for_emoji=False):
        duration = int(1000 / self.fps)
        self.frames[0].save(
            filename,
            save_all=True,
            append_images=self.frames[1:],
            duration=duration,
            loop=0,
            optimize=True
        )

def interpolate(start, end, t, easing='linear'):
    """
    Interpolate between start and end with easing function.

    Args:
        t: Progress from 0 to 1
        easing: 'linear', 'ease_in', 'ease_out', 'bounce_out'
    """
    if easing == 'linear':
        return start + (end - start) * t
    elif easing == 'ease_in':
        return start + (end - start) * (t ** 2)
    elif easing == 'ease_out':
        return start + (end - start) * (1 - (1 - t) ** 2)
    elif easing == 'bounce_out':
        if t < 1/2.75:
            val = 7.5625 * t * t
        elif t < 2/2.75:
            t -= 1.5/2.75
            val = 7.5625 * t * t + 0.75
        elif t < 2.5/2.75:
            t -= 2.25/2.75
            val = 7.5625 * t * t + 0.9375
        else:
            t -= 2.625/2.75
            val = 7.5625 * t * t + 0.984375
        return start + (end - start) * val
    return start + (end - start) * t

# Example: Bounce animation
builder = GIFBuilder(480, 480, 20)
num_frames = 30
start_y = 50
ground_y = 400
center_x = 240

for i in range(num_frames):
    frame = Image.new('RGB', (480, 480), (240, 248, 255))
    draw = ImageDraw.Draw(frame)

    t = i / (num_frames - 1)
    y = interpolate(start_y, ground_y, t, 'bounce_out')

    # Draw circle
    draw.ellipse([center_x-30, y-30, center_x+30, y+30], fill='red')

    builder.add_frame(frame)

builder.save('bounce.gif', num_colors=128)
```

---

## Best Practices Summary

1. **Document Generation**
   - Use appropriate libraries for each format
   - Always validate output files
   - Include error handling for file operations
   - Consider file size and performance

2. **Data Processing**
   - Validate inputs with Pydantic or Zod
   - Handle errors gracefully
   - Provide clear error messages
   - Support common data formats

3. **MCP Integration**
   - Use strong typing (TypeScript/Pydantic)
   - Implement comprehensive docstrings
   - Handle rate limits and errors
   - Provide clear tool descriptions

4. **Visual Content**
   - Support parameter customization
   - Include reproducibility (seeds)
   - Optimize output file sizes
   - Provide interactive controls

5. **Code Organization**
   - Keep functions focused and reusable
   - Use constants for magic numbers
   - Document expected inputs/outputs
   - Include usage examples
