const OPENAI_API_KEY = '';

const CRISPR_KEYWORDS = [
    'CRISPR', 'CAS9', 'CRISPR screen', 'CRISPRi', 'CRISPRa', 'CRISPR KO',
    'CRISPR Interference', 'CRISPR Activation', 'CRISPR Knockout', 'sgrna',
    'grna', 'guide rna', 'single guide rna', 'Mageck', 'GeCKO', 'GeCKOv2',
    'CRISPR-screening', 'MAGeCK-RRA', 'sgRNA count matrix', 'sgRNA-level',
    'SpCas9', 'SpCas9-NG', 'xCas9', 'CRISPR dropout screens', 'CRISPR libraries'
];

function validateContent(content) {
    // Check if we have any meaningful content
    if (!content.bodyText || content.bodyText.length < 100) {
        throw new Error('No meaningful content found in the page');
    }
    return true;
}

async function analyzeWithOpenAI(content) {
    try {
        // Validate content before proceeding
        validateContent(content);
        
        const prompt = `
        Please analyze this webpage content to determine if it contains CRISPR screen data or sgRNA-related experimental data.

        CRITERIA FOR TRUE POSITIVE (isCrisprExperiment = true):
        1. Must have supplementary files containing CRISPR screen or sgRNA-related data, such as:
           - sgRNA count matrices or gene-level screen data
           - Raw CRISPR screen data files
           - Files with names containing: sgRNA_counts, Cscreen, screen_results
           - Clear indication of available CRISPR screening data

        CRITERIA FOR FALSE NEGATIVE (isCrisprExperiment = false):
        1. Single-cell data, even if CRISPR-related
        2. RNA-seq or ATAC-seq data without CRISPR screen data
        3. Studies that used CRISPR KO/editing but don't provide screen data
        4. Studies that only mention CRISPR or compare with CRISPR studies

        EXAMPLES:
        True Positives:
        - GSE121355: Contains file "GSE121355_esc_Cscreen_res.txt.gz" with sgRNA counts
        - GSE97432: Has "sgRNAScorer_screen_counts.txt.gz" with count data

        False Negatives:
        - GSE194054: Contains ATAC peak data, not CRISPR screen data
        - Studies with CRISPR KO but no screen data
        - Single-cell CRISPR studies without raw screen data

        Consider these keywords as potential indicators (but verify actual screen data availability): 
        ${CRISPR_KEYWORDS.join(', ')}.

        Please note that the supplementary files are not always available or named in the manner that indicates CRISPR screen data, so you may need to infer the presence of CRISPR screen data from the content.
        
        Page Title: ${content.title}
        URL: ${content.url}
        
        Page Content:
        ${content.bodyText}
        
        Links and Files:
        ${content.links}
        
        Provide your analysis in the following JSON format:
        {
            "isCrisprExperiment": boolean,  // true ONLY if CRISPR screen data is available
            "confidence": string,  // "High", "Medium", or "Low"
            "explanation": string,  // Detailed explanation focusing on available data files
            "methodology": {
                "usageDetails": string,  // Focus on screening methodology if present
                "procedures": string,    // Specific screening procedures
                "results": string       // Screen results and data availability
            },
            "crisprTerms": string[],  // Array of CRISPR-related terms found
            "relevantFiles": string[]  // Array of files that contain CRISPR screen data
        }

        In your explanation, focus on the presence or absence of CRISPR screen data files. Ensure your response is valid JSON and includes all fields. Use null for any fields where information is not available.
        `;

        console.log('Content statistics:', {
            titleLength: content.title?.length || 0,
            bodyLength: content.bodyText?.length || 0,
            linksLength: content.links?.length || 0
        });

        const response = await fetch('https://api.openai.com/v1/chat/completions', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${OPENAI_API_KEY}`
            },
            body: JSON.stringify({
                model: 'gpt-4-turbo-preview',
                messages: [{
                    role: 'user',
                    content: prompt
                }],
                temperature: 0.05,
                max_tokens: 1000,
                response_format: { type: "json_object" }
            })
        });

        if (!response.ok) {
            throw new Error(`OpenAI API error: ${response.status}`);
        }

        const data = await response.json();
        
        if (!data.choices?.[0]?.message?.content) {
            throw new Error('Invalid response from OpenAI');
        }
        
        // Parse the JSON response
        const analysis = JSON.parse(data.choices[0].message.content);
        return analysis;
    } catch (error) {
        console.error('Error in analyzeWithOpenAI:', error);
        return {
            isCrisprExperiment: null,
            confidence: "Unknown",
            explanation: `Error analyzing content: ${error.message}. Please refresh the page and try again.`,
            methodology: { usageDetails: null, procedures: null, results: null },
            crisprTerms: [],
            relevantFiles: []
        };
    }
}

// Utility function to safely send messages
async function safeSendMessage(target, message) {
    try {
        if (target === 'runtime') {
            await chrome.runtime.sendMessage(message);
        } else if (typeof target === 'number') {
            // Check if tab exists before sending message
            const tab = await chrome.tabs.get(target).catch(() => null);
            if (tab) {
                await chrome.tabs.sendMessage(target, message);
            }
        }
    } catch (error) {
        // Silently ignore expected connection errors
        const expectedErrors = [
            'receiving end does not exist',
            'could not establish connection',
            'port closed',
            'connection closed',
            'no tab with id'
        ];
        
        if (!expectedErrors.some(msg => error.message.toLowerCase().includes(msg))) {
            console.error('Unexpected message sending error:', error);
        }
    }
}

// Store analysis results with timestamps
let analysisCache = new Map();

// Listen for messages from content script
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === 'analyzeContent') {
        // Handle the analysis request
        analyzeWithOpenAI(request.content)
            .then(async result => {
                // Store result with timestamp
                const resultWithMeta = {
                    timestamp: Date.now(),
                    data: result
                };
                
                if (sender.tab) {
                    analysisCache.set(sender.tab.id, resultWithMeta);
                }

                // Broadcast result to all components
                await safeSendMessage('runtime', {
                    action: 'analysisResult',
                    result: result,
                    timestamp: Date.now()
                });

                // Send to content script if available
                if (sender.tab?.id) {
                    await safeSendMessage(sender.tab.id, {
                        action: 'analysisResult',
                        result: result,
                        timestamp: Date.now()
                    });
                }

                // Send response to the original request
                sendResponse({ success: true });
            })
            .catch(async error => {
                console.error('Error in analysis:', error);
                const errorResult = {
                    isCrisprExperiment: null,
                    confidence: "Error",
                    explanation: `Error analyzing content: ${error.message}. Please try again.`,
                    methodology: null,
                    crisprTerms: [],
                    relevantFiles: []
                };

                // Broadcast error to all components
                await safeSendMessage('runtime', {
                    action: 'analysisResult',
                    result: errorResult,
                    timestamp: Date.now()
                });

                // Send to content script if available
                if (sender.tab?.id) {
                    await safeSendMessage(sender.tab.id, {
                        action: 'analysisResult',
                        result: errorResult,
                        timestamp: Date.now()
                    });
                }

                // Send response to the original request
                sendResponse({ success: false, error: error.message });
            });

        // Return true to indicate we'll send response asynchronously
        return true;
    } else if (request.action === 'getLastAnalysis') {
        // Return cached result for the tab if available
        if (sender.tab && analysisCache.has(sender.tab.id)) {
            const cached = analysisCache.get(sender.tab.id);
            // Only return if cache is less than 30 seconds old
            if (Date.now() - cached.timestamp < 30000) {
                sendResponse({ result: cached.data });
                return false;
            }
        }
        sendResponse({ result: null });
        return false;
    }
    return false;
}); 
