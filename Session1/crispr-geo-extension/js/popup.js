document.addEventListener('DOMContentLoaded', function() {
    const loading = document.getElementById('loading');
    const result = document.getElementById('result');

    // Initially hide the result container
    result.style.display = 'none';
    
    // Start analysis immediately
    initializeAnalysis();
});

function initializeAnalysis() {
    // Get the active tab and analyze its content
    chrome.tabs.query({ active: true, currentWindow: true }, function(tabs) {
        if (tabs[0]) {
            chrome.tabs.sendMessage(tabs[0].id, { action: 'getContent' });
        }
    });
}

// Listen for messages from background script
chrome.runtime.onMessage.addListener(function(request, sender, sendResponse) {
    if (request.action === 'analysisResult') {
        displayResults(request.result);
    }
});

function displayResults(results) {
    const loading = document.getElementById('loading');
    const result = document.getElementById('result');
    const status = document.getElementById('status');
    const confidence = document.getElementById('confidence');
    const explanation = document.getElementById('explanation');
    const terms = document.getElementById('terms');

    loading.style.display = 'none';
    result.style.display = 'block';

    if (results.isCrisprExperiment === null) {
        status.textContent = 'Error';
        explanation.textContent = results.explanation;
        confidence.textContent = '';
        terms.textContent = '';
        return;
    }

    status.textContent = results.isCrisprExperiment ? 
        'This page contains CRISPR screen data!' : 
        'This page does not contain CRISPR screen data.';
    
    confidence.textContent = `Confidence: ${results.confidence}`;
    explanation.textContent = results.explanation;
    
    if (results.crisprTerms && results.crisprTerms.length > 0) {
        terms.textContent = 'Relevant terms found: ' + results.crisprTerms.join(', ');
    } else {
        terms.textContent = '';
    }
}

// Check if we're on a valid page and initialize the popup
chrome.tabs.query({active: true, currentWindow: true}, async function(tabs) {
    const url = tabs[0].url;
    
    // Try to get results from the background script
    chrome.runtime.sendMessage({ action: 'getLastAnalysis' }, response => {
        if (response && response.result) {
            displayResults(response.result);
        } else {
            // If no results in background script, try to get from content script's localStorage
            chrome.tabs.sendMessage(tabs[0].id, { action: 'getStoredResult' }, response => {
                if (chrome.runtime.lastError) {
                    // If we can't communicate with the content script, show error
                    document.getElementById('loading').textContent = 'Please refresh the page and try again.';
                    return;
                }
                const storedResult = localStorage.getItem('crisprAnalysisResult');
                if (storedResult) {
                    displayResults(storedResult);
                }
            });
        }
    });
}); 