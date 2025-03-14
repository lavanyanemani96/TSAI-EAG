# CRISPR GEO Analyzer Chrome Extension

This Chrome extension analyzes NCBI GEO datasets to determine if they are CRISPR-based experiments. It uses OpenAI's GPT-4 model to analyze the content and provide insights.

## Features

- Automatically analyzes GEO dataset pages
- Identifies CRISPR-related experiments
- Provides confidence levels and explanations
- Lists relevant CRISPR-related terms found in the dataset

## Installation

1. Clone or download this repository
2. Open Chrome and navigate to `chrome://extensions/`
3. Enable "Developer mode" in the top right
4. Click "Load unpacked" and select the `crispr-geo-extension` directory

## Usage

1. Navigate to any GEO dataset page (e.g., https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE100027)
2. Click the extension icon in your Chrome toolbar
3. The extension will analyze the page content and display:
   - Whether it's a CRISPR-based experiment
   - Confidence level of the analysis
   - Explanation of the determination
   - Related CRISPR terms found

## Dependencies

- Chrome Browser
- OpenAI API access

## Privacy

This extension only analyzes content from NCBI GEO dataset pages. No personal data is collected or stored. 
