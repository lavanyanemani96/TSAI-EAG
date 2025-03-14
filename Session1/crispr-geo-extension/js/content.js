// Function to extract page content
function extractPageContent() {
    const content = {
        title: document.title,
        url: window.location.href,
        bodyText: document.body.innerText,
        links: Array.from(document.links).map(link => link.href).join('\n')
    };
    return content;
}

// Function to trigger analysis
function triggerAnalysis(callback) {
    const content = extractPageContent();
    console.log('Extracting fresh content:', {
        titleLength: content.title.length,
        bodyLength: content.bodyText.length,
        linksLength: content.links.length,
        timestamp: new Date().toISOString()
    });

    // Clear any old results
    localStorage.removeItem('crisprAnalysisResult');

    // Show loading state
    const loadingState = {
        isCrisprExperiment: null,
        confidence: "Loading",
        explanation: "Analyzing page content...",
        methodology: null,
        crisprTerms: [],
        relevantFiles: []
    };

    // Store and broadcast loading state
    localStorage.setItem('crisprAnalysisResult', JSON.stringify(loadingState));
    chrome.runtime.sendMessage({
        action: 'analysisResult',
        result: loadingState
    });

    // Request new analysis
    chrome.runtime.sendMessage({
        action: 'analyzeContent',
        content: content,
        timestamp: Date.now() // Add timestamp to ensure fresh analysis
    }, response => {
        if (chrome.runtime.lastError) {
            console.error('Analysis request error:', chrome.runtime.lastError);
            if (callback) callback(false);
        } else if (callback) {
            callback(true);
        }
    });
}

// Listen for messages from popup
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === 'getStoredResult') {
        // Always trigger fresh analysis
        triggerAnalysis((success) => {
            if (!success) {
                // If analysis request failed, send error state
                const errorState = {
                    isCrisprExperiment: null,
                    confidence: "Error",
                    explanation: "Failed to start analysis. Please try again.",
                    methodology: null,
                    crisprTerms: [],
                    relevantFiles: []
                };
                localStorage.setItem('crisprAnalysisResult', JSON.stringify(errorState));
                chrome.runtime.sendMessage({
                    action: 'analysisResult',
                    result: errorState
                });
            }
        });
        // Send acknowledgment
        sendResponse({ status: 'analyzing' });
        return false;
    }
});

// Listen for analysis results
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === 'analysisResult' && request.result) {
        console.log('Received fresh analysis result:', {
            timestamp: new Date().toISOString(),
            result: request.result
        });
        localStorage.setItem('crisprAnalysisResult', JSON.stringify(request.result));
    }
});

// Initial analysis when script loads
triggerAnalysis(); 