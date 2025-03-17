// Function to extract relevant text content from the page
function extractPageContent() {
    const title = document.title;
    const mainContent = document.body.innerText.substring(0, 1000); // First 1000 characters
    return `${title}\n${mainContent}`;
}

// Function to create and update the timer overlay
function createTimerOverlay() {
    const overlay = document.createElement('div');
    overlay.id = 'focus-timer-overlay';
    overlay.style.cssText = `
        position: fixed;
        top: 10px;
        right: 10px;
        background-color: rgba(255, 0, 0, 0.8);
        color: white;
        padding: 10px;
        border-radius: 5px;
        z-index: 9999;
        font-family: Arial, sans-serif;
        font-size: 16px;
    `;
    document.body.appendChild(overlay);
    return overlay;
}

// Create or get the status overlay
function getStatusOverlay() {
    let overlay = document.getElementById('focus-status-overlay');
    if (!overlay) {
        overlay = document.createElement('div');
        overlay.id = 'focus-status-overlay';
        overlay.style.cssText = `
            position: fixed;
            top: 10px;
            right: 10px;
            background-color: rgba(0, 0, 0, 0.8);
            color: white;
            padding: 10px;
            border-radius: 5px;
            z-index: 9999;
            font-family: Arial, sans-serif;
            font-size: 16px;
        `;
        document.body.appendChild(overlay);
    }
    return overlay;
}

let timerInterval;
let startTime;
let lastUrl = window.location.href;
let isAnalyzing = false;
let analysisTimeout;

// Function to get today's date in YYYY-MM-DD format
function getTodayDate() {
    const today = new Date();
    return today.toISOString().split('T')[0];
}

// Function to update timer and save cumulative time
function updateTimer(overlay) {
    const currentTime = new Date().getTime();
    const elapsedTime = Math.floor((currentTime - startTime) / 1000);
    const minutes = Math.floor(elapsedTime / 60);
    const seconds = elapsedTime % 60;

    // Get cumulative time for today
    chrome.storage.local.get(['distractingTime'], (result) => {
        const today = getTodayDate();
        const timeData = result.distractingTime || {};
        const todayTime = timeData[today] || 0;
        
        // Update total time for today
        timeData[today] = todayTime + 1; // Add one second
        chrome.storage.local.set({ distractingTime: timeData });

        // Calculate total time
        const totalMinutes = Math.floor(timeData[today] / 60);
        const totalSeconds = timeData[today] % 60;

        // Update overlay with both current session and total time
        overlay.textContent = `Current session: ${minutes}m ${seconds}s\nTotal today: ${totalMinutes}m ${totalSeconds}s`;
    });
}

// Function to clear existing timer and overlay
function clearExistingTimer() {
    if (timerInterval) {
        clearInterval(timerInterval);
        timerInterval = null;
    }
    const existingOverlay = document.getElementById('focus-timer-overlay');
    if (existingOverlay) {
        existingOverlay.remove();
    }
}

// Start the timer
function startTimer() {
    clearExistingTimer();
    const overlay = createTimerOverlay();
    startTime = new Date().getTime();
    timerInterval = setInterval(() => updateTimer(overlay), 1000);
}

// Function to update status
function updateStatus(message) {
    console.log('Updating status:', message);
    const statusOverlay = getStatusOverlay();
    statusOverlay.textContent = message;

    // Try to update the popup if it's open
    chrome.runtime.sendMessage({
        action: 'updateStatus',
        message: message
    }).catch(error => console.log('Popup not open, status update only shown in overlay'));
}

// Main function to analyze page content
async function analyzePage() {
    if (isAnalyzing) {
        console.log('Analysis already in progress, skipping...');
        return;
    }

    try {
        isAnalyzing = true;
        clearExistingTimer(); // Clear any existing timer before starting analysis

        updateStatus('Extracting page content...');
        console.log('Starting page analysis for URL:', window.location.href);
        const pageContent = extractPageContent();
        console.log('Extracted content length:', pageContent.length);
        
        updateStatus('Sending content for analysis...');
        
        // Send message to background script for API call
        chrome.runtime.sendMessage({
            action: 'analyzeContent',
            content: pageContent
        }, response => {
            const error = chrome.runtime.lastError;
            if (error) {
                console.error('Runtime error:', error);
                updateStatus('Error: Could not connect to extension');
                isAnalyzing = false;
                return;
            }
            
            if (!response) {
                console.error('No response received');
                updateStatus('Error: No response from analysis');
                isAnalyzing = false;
                return;
            }

            console.log('Analysis response:', response);
            
            // Remove the status overlay as we'll either show the timer or nothing
            const statusOverlay = document.getElementById('focus-status-overlay');
            if (statusOverlay) {
                statusOverlay.remove();
            }

            if (response.isDistracting) {
                startTimer();
            }
            
            isAnalyzing = false;
        });
    } catch (error) {
        console.error('Error in analyzePage:', error);
        updateStatus('Error: ' + error.message);
        isAnalyzing = false;
    }
}

// Debounced function to handle URL changes
function handleUrlChange() {
    const currentUrl = window.location.href;
    if (currentUrl !== lastUrl) {
        console.log('URL changed from', lastUrl, 'to', currentUrl);
        lastUrl = currentUrl;
        
        // Clear any existing analysis timeout
        if (analysisTimeout) {
            clearTimeout(analysisTimeout);
        }
        
        // Clear existing timer
        clearExistingTimer();
        
        // Wait for content to load and then analyze
        analysisTimeout = setTimeout(() => {
            analyzePage();
        }, 1500); // Wait 1.5 seconds for content to load
    }
}

// Run initial analysis when page loads
console.log('Content script loaded');
setTimeout(() => {
    updateStatus('Starting initial analysis...');
    analyzePage();
}, 1500);

// Set up URL change detection with more frequent checks for YouTube
const urlCheckInterval = window.location.hostname.includes('youtube.com') ? 500 : 1000;
setInterval(handleUrlChange, urlCheckInterval);

// Listen for history state changes (for SPAs)
window.addEventListener('popstate', () => {
    console.log('History state changed');
    handleUrlChange();
});

// Listen for YouTube navigation events
document.addEventListener('yt-navigate-finish', () => {
    console.log('YouTube navigation detected');
    handleUrlChange();
}); 