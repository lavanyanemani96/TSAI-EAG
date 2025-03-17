document.addEventListener('DOMContentLoaded', () => {
    const statusDiv = document.getElementById('status');
    const timerDiv = document.getElementById('timer');
    const dailyStatsDiv = document.getElementById('daily-stats');

    // Function to format time
    function formatTime(seconds) {
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        const remainingSeconds = seconds % 60;
        
        let timeString = '';
        if (hours > 0) timeString += `${hours}h `;
        if (minutes > 0 || hours > 0) timeString += `${minutes}m `;
        timeString += `${remainingSeconds}s`;
        return timeString;
    }

    // Get today's date
    function getTodayDate() {
        const today = new Date();
        return today.toISOString().split('T')[0];
    }

    // Update daily statistics
    function updateDailyStats() {
        chrome.storage.local.get(['distractingTime'], (result) => {
            const timeData = result.distractingTime || {};
            const today = getTodayDate();
            const todayTime = timeData[today] || 0;
            
            let statsHtml = `<strong>Today:</strong> ${formatTime(todayTime)}<br>`;
            
            // Show last 7 days
            const last7Days = [];
            for (let i = 1; i <= 7; i++) {
                const date = new Date();
                date.setDate(date.getDate() - i);
                const dateStr = date.toISOString().split('T')[0];
                if (timeData[dateStr]) {
                    last7Days.push(`${date.toLocaleDateString()}: ${formatTime(timeData[dateStr])}`);
                }
            }
            
            if (last7Days.length > 0) {
                statsHtml += '<br><strong>Previous days:</strong><br>' + last7Days.join('<br>');
            }
            
            dailyStatsDiv.innerHTML = statsHtml;
        });
    }

    // Get the latest analysis result
    chrome.storage.local.get(['analysisResult'], (result) => {
        if (result.analysisResult) {
            const { isDistracting, explanation } = result.analysisResult;
            statusDiv.textContent = explanation;
            statusDiv.className = `status ${isDistracting ? 'distracting' : 'educational'}`;
        }
    });

    // Query the active tab to get timer information
    chrome.tabs.query({active: true, currentWindow: true}, (tabs) => {
        if (tabs[0]) {
            chrome.scripting.executeScript({
                target: {tabId: tabs[0].id},
                function: getTimerInfo
            }, (results) => {
                if (results && results[0].result) {
                    timerDiv.textContent = results[0].result;
                }
            });
        }
    });

    // Update stats immediately and every second
    updateDailyStats();
    setInterval(updateDailyStats, 1000);
});

// Function to get timer information from the content script
function getTimerInfo() {
    const overlay = document.getElementById('focus-timer-overlay');
    if (overlay) {
        return overlay.textContent;
    }
    return '';
} 