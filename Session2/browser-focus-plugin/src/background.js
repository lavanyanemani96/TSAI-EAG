// Replace with your actual Gemini API key
const GEMINI_API_KEY = '';

async function analyzeWithGemini(content) {
    console.log('Starting Gemini analysis...');
    
    try {
        console.log('Preparing request...');
        
        // Construct the API request with API key in URL and correct API version
        const url = `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=${GEMINI_API_KEY}`;
        const headers = {
            'Content-Type': 'application/json'
        };
        
        // Prepare a clear, structured prompt that focuses on content rather than platform
        const prompt = `You are a content analyzer that determines if webpage content is educational or distracting. 

Analyze this content and respond ONLY with one of these two exact words on the first line:
EDUCATIONAL
or
DISTRACTING

Then on the next line, provide your reasoning.

Here are the criteria:

Educational content includes:
- Tutorials and learning materials
- Technical documentation
- Academic lectures and courses
- Educational videos
- Research papers and articles
- Professional development content
- Informative documentaries

Distracting content includes:
- Meme videos and reactions
- Entertainment vlogs without educational value
- Social media feeds focused on entertainment
- Gaming content without educational purpose
- Clickbait content
- Short-form entertainment videos
- Celebrity gossip and entertainment news

Content to analyze:
${content}`;

        const requestBody = {
            contents: [{
                parts: [{
                    text: prompt
                }]
            }],
            safetySettings: [{
                category: "HARM_CATEGORY_DANGEROUS_CONTENT",
                threshold: "BLOCK_NONE"
            }],
            generationConfig: {
                temperature: 0.1,
                topK: 1,
                topP: 0.8,
                maxOutputTokens: 250
            }
        };

        console.log('Sending request to Gemini API...');
        console.log('Request URL:', url);
        console.log('Request body:', JSON.stringify(requestBody, null, 2));
        
        const response = await fetch(url, {
            method: 'POST',
            headers: headers,
            body: JSON.stringify(requestBody)
        });

        console.log('Response status:', response.status);
        const responseText = await response.text();
        console.log('Raw response:', responseText);

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}, response: ${responseText}`);
        }

        try {
            const data = JSON.parse(responseText);
            console.log('Parsed response:', JSON.stringify(data, null, 2));

            if (!data.candidates || !data.candidates[0] || !data.candidates[0].content || !data.candidates[0].content.parts) {
                throw new Error('Invalid response format');
            }

            const analysisText = data.candidates[0].content.parts[0].text.trim();
            console.log('Analysis text:', analysisText);

            // Split the response into lines
            const lines = analysisText.split('\n').map(line => line.trim()).filter(line => line);
            
            if (lines.length < 2) {
                throw new Error('Response does not contain enough lines');
            }

            // First non-empty line should be EDUCATIONAL or DISTRACTING
            const type = lines[0].toUpperCase();
            if (type !== 'EDUCATIONAL' && type !== 'DISTRACTING') {
                throw new Error(`Invalid type: ${type}`);
            }

            // Rest of the lines form the explanation
            const explanation = lines.slice(1).join('\n').trim();

            const isDistracting = type === 'DISTRACTING';
            
            console.log('Analysis result:', { isDistracting, explanation });

            return {
                isDistracting: isDistracting,
                explanation: `Type: ${type}\nReason: ${explanation}`
            };
        } catch (parseError) {
            console.error('Error parsing response:', parseError);
            throw new Error('Failed to parse API response');
        }
    } catch (error) {
        console.error('Error in analyzeWithGemini:', error);
        throw error;
    }
}

// Listen for messages from content script
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    console.log('Received message type:', request.action);

    if (request.action === 'analyzeContent') {
        console.log('Starting content analysis...');
        console.log('Content to analyze:', request.content);
        
        // Handle the analysis
        analyzeWithGemini(request.content)
            .then(result => {
                console.log('Analysis complete:', result);
                sendResponse(result);
                chrome.storage.local.set({ analysisResult: result });
            })
            .catch(error => {
                console.error('Analysis error:', error);
                const errorResult = {
                    isDistracting: false,
                    explanation: `Error: ${error.message}`
                };
                sendResponse(errorResult);
                chrome.storage.local.set({ analysisResult: errorResult });
            });
        
        return true; // Required for async response
    }

    if (request.action === 'updateStatus') {
        console.log('Updating status:', request.message);
        chrome.storage.local.set({
            analysisResult: {
                explanation: request.message,
                isDistracting: false
            }
        });
    }
}); 