# Focus Timer Chrome Extension

This Chrome extension uses Google's Gemini AI to analyze webpage content and determine if it's educational or potentially distracting. If a page is identified as distracting, it displays a timer to help you track how much time you spend on it.

## Setup

1. Get a Gemini API key from the [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Clone this repository
3. Open `src/background.js` and replace `YOUR_API_KEY` with your actual Gemini API key
4. Open Chrome and go to `chrome://extensions/`
5. Enable "Developer mode" in the top right
6. Click "Load unpacked" and select the `browser-focus-plugin` directory

## Features

- Analyzes webpage content using Gemini AI
- Identifies educational vs. potentially distracting content
- Displays a timer for distracting content
- Shows analysis results in the extension popup
- Timer overlay on distracting pages

## Usage

1. Click the extension icon to see the analysis of the current page
2. For pages identified as distracting, a timer will appear in the top-right corner
3. The timer tracks how long you spend on distracting content

## Privacy

The extension only sends the page title and first 1000 characters of content to the Gemini API for analysis. No personal data is collected or stored. 