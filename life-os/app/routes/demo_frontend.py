from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from typing import Optional, List, Dict, Any
import os
import uuid
import logging
from datetime import datetime

from ..services.ai_processor import AIProcessor
from ..services.memory_manager import MemoryManager
from ..services.file_storage import FileStorage
from ..config import settings

router = APIRouter()
logger = logging.getLogger(__name__)

# Initialize services with fallback handling
try:
    ai_processor = AIProcessor()
    memory_manager = MemoryManager()
    file_storage = FileStorage()
    logger.info("Demo services initialized successfully")
except Exception as e:
    logger.warning(f"Some services failed to initialize: {e}")
    ai_processor = None
    memory_manager = None
    file_storage = None

@router.get("/", response_class=HTMLResponse)
async def demo_home():
    """Serve the unified demo frontend"""
    html_content = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Life OS Demo - Enhanced Gemini 2.5 Pro</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
            color: #2d3748;
        }
        
        .container {
            max-width: 900px;
            margin: 0 auto;
            background: rgba(255, 255, 255, 0.98);
            border-radius: 24px;
            padding: 40px;
            box-shadow: 0 25px 50px rgba(0,0,0,0.15);
            backdrop-filter: blur(10px);
        }
        
        .header {
            text-align: center;
            margin-bottom: 40px;
        }
        
        .header h1 {
            font-size: 2.8rem;
            font-weight: 700;
            background: linear-gradient(135deg, #667eea, #764ba2);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 10px;
        }
        
        .header .subtitle {
            color: #718096;
            font-size: 1.2rem;
            margin-bottom: 25px;
            font-weight: 400;
        }
        
        .capabilities {
            display: flex;
            justify-content: center;
            flex-wrap: wrap;
            gap: 12px;
            margin-bottom: 40px;
        }
        
        .capability-tag {
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            padding: 10px 18px;
            border-radius: 25px;
            font-size: 0.9rem;
            font-weight: 500;
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
        }
        
        .main-interface {
            background: #f8fafc;
            border-radius: 20px;
            padding: 35px;
            margin-bottom: 30px;
            border: 1px solid #e2e8f0;
        }
        
        .input-section {
            margin-bottom: 25px;
        }
        
        .input-section label {
            display: block;
            margin-bottom: 12px;
            color: #4a5568;
            font-weight: 600;
            font-size: 1.1rem;
        }
        
        .unified-input {
            position: relative;
        }
        
        .main-textarea {
            width: 100%;
            min-height: 120px;
            padding: 20px;
            border: 2px solid #e2e8f0;
            border-radius: 15px;
            font-size: 1rem;
            font-family: inherit;
            resize: vertical;
            transition: all 0.3s ease;
            background: white;
        }
        
        .main-textarea:focus {
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }
        
        .file-drop-zone {
            margin-top: 15px;
            border: 2px dashed #cbd5e0;
            border-radius: 15px;
            padding: 30px;
            text-align: center;
            transition: all 0.3s ease;
            background: white;
            cursor: pointer;
        }
        
        .file-drop-zone:hover,
        .file-drop-zone.dragover {
            border-color: #667eea;
            background: rgba(102, 126, 234, 0.05);
            transform: translateY(-2px);
        }
        
        .file-drop-zone.has-file {
            border-color: #48bb78;
            background: rgba(72, 187, 120, 0.05);
        }
        
        .file-info {
            color: #4a5568;
            font-size: 0.95rem;
            margin-top: 8px;
        }
        
        .user-id-section {
            display: flex;
            align-items: center;
            gap: 15px;
            margin-bottom: 25px;
        }
        
        .user-id-input {
            flex: 1;
            padding: 12px 18px;
            border: 2px solid #e2e8f0;
            border-radius: 12px;
            font-size: 1rem;
            transition: border-color 0.3s ease;
            background: white;
        }
        
        .user-id-input:focus {
            outline: none;
            border-color: #667eea;
        }
        
        .action-section {
            display: flex;
            gap: 15px;
            justify-content: center;
            flex-wrap: wrap;
        }
        
        .primary-btn {
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            border: none;
            padding: 15px 30px;
            border-radius: 12px;
            font-size: 1.1rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            box-shadow: 0 8px 25px rgba(102, 126, 234, 0.3);
        }
        
        .primary-btn:hover:not(:disabled) {
            transform: translateY(-3px);
            box-shadow: 0 12px 35px rgba(102, 126, 234, 0.4);
        }
        
        .primary-btn:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
        }
        
        .secondary-btn {
            background: white;
            color: #667eea;
            border: 2px solid #667eea;
            padding: 13px 25px;
            border-radius: 12px;
            font-size: 1rem;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        
        .secondary-btn:hover {
            background: #667eea;
            color: white;
        }
        
        .response-section {
            margin-top: 30px;
        }
        
        .response-area {
            background: white;
            border: 2px solid #e2e8f0;
            border-radius: 15px;
            padding: 25px;
            min-height: 200px;
            white-space: pre-wrap;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, monospace;
            line-height: 1.6;
            max-height: 500px;
            overflow-y: auto;
        }
        
        .response-area.loading {
            display: flex;
            align-items: center;
            justify-content: center;
            color: #667eea;
            font-style: italic;
            font-family: inherit;
        }
        
        .loading-spinner {
            width: 20px;
            height: 20px;
            border: 2px solid #e2e8f0;
            border-top: 2px solid #667eea;
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin-right: 10px;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        .error {
            color: #e53e3e;
            background: #fed7d7;
            padding: 20px;
            border-radius: 12px;
            margin-top: 15px;
            border: 1px solid #fc8181;
        }
        
        .success {
            color: #38a169;
            background: #c6f6d5;
            padding: 20px;
            border-radius: 12px;
            margin-top: 15px;
            border: 1px solid #68d391;
        }
        
        .status-bar {
            background: #edf2f7;
            border-radius: 15px;
            padding: 20px;
            margin-top: 30px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 15px;
        }
        
        .status-item {
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 0.9rem;
            color: #4a5568;
        }
        
        .status-indicator {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: #48bb78;
        }
        
        .status-indicator.warning {
            background: #ed8936;
        }
        
        .status-indicator.error {
            background: #e53e3e;
        }
        
        .hidden {
            display: none;
        }
        
        .file-list {
            margin-top: 15px;
            max-height: 200px;
            overflow-y: auto;
        }
        
        .file-item {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 10px 15px;
            margin-bottom: 8px;
            background: white;
            border: 1px solid #e2e8f0;
            border-radius: 10px;
            font-size: 0.9rem;
        }
        
        .file-item-info {
            display: flex;
            align-items: center;
            gap: 10px;
            flex: 1;
        }
        
        .file-icon {
            font-size: 1.2rem;
        }
        
        .file-details {
            flex: 1;
        }
        
        .file-name {
            font-weight: 500;
            color: #2d3748;
            margin-bottom: 2px;
        }
        
        .file-meta {
            color: #718096;
            font-size: 0.8rem;
        }
        
        .remove-file {
            background: #fed7d7;
            color: #e53e3e;
            border: none;
            border-radius: 6px;
            padding: 4px 8px;
            cursor: pointer;
            font-size: 0.8rem;
            transition: all 0.2s ease;
        }
        
        .remove-file:hover {
            background: #fc8181;
            color: white;
        }
        
        @media (max-width: 768px) {
            .container {
                padding: 25px;
                margin: 10px;
            }
            
            .header h1 {
                font-size: 2.2rem;
            }
            
            .action-section {
                flex-direction: column;
            }
            
            .user-id-section {
                flex-direction: column;
                align-items: stretch;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🧠 Life OS</h1>
            <p class="subtitle">Enhanced AI Life Management with Gemini 2.5 Pro</p>
            <div class="capabilities">
                <div class="capability-tag">🎯 2M Token Context</div>
                <div class="capability-tag">🧠 Advanced Reasoning</div>
                <div class="capability-tag">💭 Thinking Model</div>
                <div class="capability-tag">🎬 Video Understanding</div>
                <div class="capability-tag">🎵 Native Audio</div>
                <div class="capability-tag">🖼️ Image Analysis</div>
                <div class="capability-tag">⚡ Memory Graph</div>
                <div class="capability-tag">🚀 Enhanced Coding</div>
            </div>
        </div>
        
        <div class="main-interface">
            <div class="input-section">
                <label for="mainInput">What can I help you with?</label>
                <div class="unified-input">
                    <textarea 
                        id="mainInput" 
                        class="main-textarea" 
                        placeholder="Ask me anything, upload a file, or query your memories...

Examples:
• Analyze this image for me
• What do you remember about my last meeting?
• Help me plan my day
• Summarize this document"
                    ></textarea>
                    
                    <div class="file-drop-zone" id="fileDropZone">
                        <input type="file" id="fileInput" style="display: none;" accept="*/*" multiple>
                        <div id="dropText">
                            <div style="font-size: 1.1rem; margin-bottom: 8px;">📁 Drop files here or click to upload</div>
                            <div class="file-info">Supports multiple files: images, audio, video, documents</div>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="user-id-section">
                <label for="userId" style="white-space: nowrap; font-weight: 500;">User ID:</label>
                <input type="text" id="userId" class="user-id-input" value="demo_user" placeholder="demo_user">
            </div>
            
            <div class="action-section">
                <button class="primary-btn" id="processBtn" onclick="processInput()">
                    Process Input
                </button>
                <button class="secondary-btn" onclick="getMemoryInsights()">
                    Memory Insights
                </button>
                <button class="secondary-btn" onclick="checkSystemStatus()">
                    System Status
                </button>
            </div>
            
            <div class="response-section">
                <div class="response-area" id="responseArea">
                    Welcome to Life OS! I'm ready to help you with text processing, file analysis, memory queries, and more.
                    
Try uploading a file or asking me something...
                </div>
            </div>
        </div>
        
        <div class="status-bar">
            <div class="status-item">
                <div class="status-indicator" id="aiStatus"></div>
                <span>AI Processor</span>
            </div>
            <div class="status-item">
                <div class="status-indicator warning" id="memoryStatus"></div>
                <span>Memory System</span>
            </div>
            <div class="status-item">
                <div class="status-indicator" id="storageStatus"></div>
                <span>File Storage</span>
            </div>
            <div class="status-item">
                <span style="font-weight: 500;">Model: Gemini 2.5 Pro</span>
            </div>
            <div class="status-item">
                <span style="font-weight: 500;">Context: 2M tokens</span>
            </div>
        </div>
    </div>

    <script>
        let selectedFiles = [];
        let isProcessing = false;
        
        // File handling
        const fileDropZone = document.getElementById('fileDropZone');
        const fileInput = document.getElementById('fileInput');
        const dropText = document.getElementById('dropText');
        
        fileDropZone.addEventListener('click', () => fileInput.click());
        
        fileDropZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            fileDropZone.classList.add('dragover');
        });
        
        fileDropZone.addEventListener('dragleave', () => {
            fileDropZone.classList.remove('dragover');
        });
        
        fileDropZone.addEventListener('drop', (e) => {
            e.preventDefault();
            fileDropZone.classList.remove('dragover');
            const files = Array.from(e.dataTransfer.files);
            if (files.length > 0) {
                addFiles(files);
            }
        });
        
        fileInput.addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                addFiles(Array.from(e.target.files));
            }
        });
        
        function addFiles(files) {
            files.forEach(file => {
                // Check if file already exists
                if (!selectedFiles.find(f => f.name === file.name && f.size === file.size)) {
                    selectedFiles.push(file);
                }
            });
            updateFileDisplay();
        }
        
        function removeFile(index) {
            selectedFiles.splice(index, 1);
            updateFileDisplay();
        }
        
        function clearFiles() {
            selectedFiles = [];
            updateFileDisplay();
            fileInput.value = '';
        }
        
        function updateFileDisplay() {
            if (selectedFiles.length === 0) {
                fileDropZone.classList.remove('has-file');
                dropText.innerHTML = `
                    <div style="font-size: 1.1rem; margin-bottom: 8px;">📁 Drop files here or click to upload</div>
                    <div class="file-info">Supports multiple files: images, audio, video, documents</div>
                `;
            } else {
                fileDropZone.classList.add('has-file');
                
                const totalSize = selectedFiles.reduce((sum, file) => sum + file.size, 0);
                const fileListHtml = selectedFiles.map((file, index) => {
                    const fileIcon = getFileIcon(file.type);
                    const fileSize = (file.size / 1024 / 1024).toFixed(2);
                    
                    return `
                        <div class="file-item">
                            <div class="file-item-info">
                                <div class="file-icon">${fileIcon}</div>
                                <div class="file-details">
                                    <div class="file-name">${file.name}</div>
                                    <div class="file-meta">${fileSize} MB • ${file.type || 'Unknown type'}</div>
                                </div>
                            </div>
                            <button class="remove-file" onclick="removeFile(${index})">✕</button>
                        </div>
                    `;
                }).join('');
                
                dropText.innerHTML = `
                    <div style="font-size: 1.1rem; margin-bottom: 12px; color: #48bb78;">
                        ✅ ${selectedFiles.length} file${selectedFiles.length > 1 ? 's' : ''} selected 
                        (${(totalSize / 1024 / 1024).toFixed(2)} MB total)
                    </div>
                    <div class="file-list">${fileListHtml}</div>
                    <div style="font-size: 0.85rem; margin-top: 12px; color: #718096;">
                        Click here to add more files or drag & drop additional files
                    </div>
                `;
            }
        }
        
        function getFileIcon(mimeType) {
            if (!mimeType) return '📄';
            
            if (mimeType.startsWith('image/')) return '🖼️';
            if (mimeType.startsWith('audio/')) return '🎵';
            if (mimeType.startsWith('video/')) return '🎬';
            if (mimeType.includes('pdf')) return '📕';
            if (mimeType.includes('text/')) return '📝';
            if (mimeType.includes('word') || mimeType.includes('document')) return '📄';
            if (mimeType.includes('sheet') || mimeType.includes('excel')) return '📊';
            if (mimeType.includes('presentation') || mimeType.includes('powerpoint')) return '📈';
            if (mimeType.includes('zip') || mimeType.includes('archive')) return '🗜️';
            
            return '📄';
        }
        
        async function processInput() {
            if (isProcessing) return;
            
            const text = document.getElementById('mainInput').value.trim();
            const userId = document.getElementById('userId').value || 'demo_user';
            
            if (!text && selectedFiles.length === 0) {
                showError('Please enter some text or upload files to process.');
                return;
            }
            
            isProcessing = true;
            const processBtn = document.getElementById('processBtn');
            const originalText = processBtn.textContent;
            
            processBtn.disabled = true;
            processBtn.textContent = 'Processing...';
            
            const fileCount = selectedFiles.length;
            const processingMessage = fileCount > 0 
                ? `🤖 Processing ${fileCount} file${fileCount > 1 ? 's' : ''} with enhanced Gemini 2.5 Pro capabilities...`
                : '🤖 Processing with enhanced Gemini 2.5 Pro capabilities...';
            
            showLoading(processingMessage);
            
            try {
                let response;
                
                if (selectedFiles.length > 0) {
                    // Process multiple files with optional text
                    const formData = new FormData();
                    
                    // Add all files
                    selectedFiles.forEach((file, index) => {
                        formData.append(`files`, file);
                    });
                    
                    formData.append('user_id', userId);
                    if (text) {
                        formData.append('text', text);
                    }
                    
                    response = await fetch('/demo/unified-process', {
                        method: 'POST',
                        body: formData
                    });
                } else {
                    // Process text only
                    response = await fetch('/demo/unified-process', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            text: text,
                            user_id: userId
                        })
                    });
                }
                
                const result = await response.json();
                
                if (response.ok) {
                    displayResponse(result);
                    // Clear inputs after successful processing
                    document.getElementById('mainInput').value = '';
                    clearFiles();
                } else {
                    showError(result.detail || 'An error occurred during processing');
                }
            } catch (error) {
                showError('Network error: ' + error.message);
            } finally {
                isProcessing = false;
                processBtn.disabled = false;
                processBtn.textContent = originalText;
            }
        }
        
        async function getMemoryInsights() {
            const userId = document.getElementById('userId').value || 'demo_user';
            
            showLoading('🧠 Analyzing memory patterns and insights...');
            
            try {
                const response = await fetch(`/demo/insights/${userId}`);
                const result = await response.json();
                
                if (response.ok) {
                    displayResponse(result);
                } else {
                    showError(result.detail || 'Failed to get memory insights');
                }
            } catch (error) {
                showError('Network error: ' + error.message);
            }
        }
        
        async function checkSystemStatus() {
            showLoading('⚙️ Checking system status and capabilities...');
            
            try {
                const response = await fetch('/demo/status');
                const result = await response.json();
                
                displayResponse(result);
                updateStatusIndicators(result);
            } catch (error) {
                showError('Network error: ' + error.message);
            }
        }
        
        function showLoading(message) {
            const responseArea = document.getElementById('responseArea');
            responseArea.className = 'response-area loading';
            responseArea.innerHTML = `
                <div class="loading-spinner"></div>
                ${message}
            `;
        }
        
        function displayResponse(data) {
            const responseArea = document.getElementById('responseArea');
            responseArea.className = 'response-area';
            
            if (typeof data === 'object' && data.response) {
                // Handle AI response format
                let content = data.response;
                
                // Show file processing information for multiple files
                if (data.files_processed && data.files_processed.length > 0) {
                    content += `\n\n📁 Files Processed (${data.files_processed.length}):\n`;
                    data.files_processed.forEach((file, index) => {
                        const sizeInMB = (file.size / 1024 / 1024).toFixed(2);
                        content += `  ${index + 1}. ${file.filename} (${file.media_type}, ${sizeInMB} MB)\n`;
                    });
                }
                
                // Show file analysis if available (from multiple file processing)
                if (data.file_analysis) {
                    if (data.file_analysis.unified_themes && data.file_analysis.unified_themes.length > 0) {
                        content += `\n🎯 Unified Themes:\n`;
                        data.file_analysis.unified_themes.forEach(theme => {
                            content += `  • ${theme}\n`;
                        });
                    }
                    
                    if (data.file_analysis.cross_file_connections && data.file_analysis.cross_file_connections.length > 0) {
                        content += `\n🔗 Cross-File Connections:\n`;
                        data.file_analysis.cross_file_connections.forEach(connection => {
                            content += `  • ${connection}\n`;
                        });
                    }
                }
                
                // Show legacy single file info for backward compatibility
                if (data.file_info && !data.files_processed) {
                    const sizeInMB = (data.file_info.size / 1024 / 1024).toFixed(2);
                    content += `\n\n📁 File: ${data.file_info.filename} (${data.file_info.media_type}, ${sizeInMB} MB)`;
                }
                
                // Show extracted information
                if (data.entities && data.entities.length > 0) {
                    content += `\n\n🏷️ Entities: ${data.entities.join(', ')}`;
                }
                
                if (data.keywords && data.keywords.length > 0) {
                    content += `\n🔑 Keywords: ${data.keywords.join(', ')}`;
                }
                
                if (data.sentiment) {
                    const sentimentEmoji = data.sentiment === 'positive' ? '😊' : 
                                         data.sentiment === 'negative' ? '😔' : '😐';
                    content += `\n${sentimentEmoji} Sentiment: ${data.sentiment}`;
                }
                
                // Show insights from AI processing
                if (data.insights && data.insights.length > 0) {
                    content += `\n\n💡 Insights:\n`;
                    data.insights.forEach(insight => {
                        content += `  • ${insight}\n`;
                    });
                }
                
                // Show memory context information
                if (data.memory_context) {
                    content += `\n\n🧠 Memory Context: ${data.memory_context.memories_retrieved} memories retrieved`;
                    if (data.memory_context.long_context_enabled) {
                        content += ` (Enhanced ${(data.memory_context.context_window_used / 1000).toFixed(0)}K context)`;
                    }
                }
                
                // Show processing metadata for multiple files
                if (data.enhanced_multimodal) {
                    content += `\n\n⚡ Enhanced Processing: ${data.total_files} files analyzed with Gemini 2.5 Pro`;
                }
                
                responseArea.textContent = content;
            } else if (typeof data === 'object') {
                responseArea.textContent = JSON.stringify(data, null, 2);
            } else {
                responseArea.textContent = data;
            }
        }
        
        function showError(message) {
            const responseArea = document.getElementById('responseArea');
            responseArea.className = 'response-area';
            responseArea.innerHTML = `<div class="error">❌ ${message}</div>`;
        }
        
        function updateStatusIndicators(statusData) {
            const indicators = {
                aiStatus: statusData?.ai_processor === '✅ Ready',
                memoryStatus: statusData?.memory_manager === '✅ Ready',
                storageStatus: statusData?.file_storage === '✅ Ready'
            };
            
            Object.entries(indicators).forEach(([id, isHealthy]) => {
                const indicator = document.getElementById(id);
                if (indicator) {
                    indicator.className = `status-indicator ${isHealthy ? '' : 'warning'}`;
                }
            });
        }
        
        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey || e.metaKey) {
                if (e.key === 'Enter') {
                    e.preventDefault();
                    processInput();
                } else if (e.key === 'u') {
                    e.preventDefault();
                    fileInput.click();
                }
            }
        });
        
        // Initialize status on load
        window.addEventListener('load', () => {
            setTimeout(checkSystemStatus, 1000);
        });
    </script>
</body>
</html>
    '''
    return HTMLResponse(content=html_content)

@router.post("/unified-process")
async def unified_process(
    request: Request = None,
    files: List[UploadFile] = File(None),
    user_id: str = Form("demo_user"),
    text: Optional[str] = Form(None)
):
    """Unified processing endpoint for text, files, and memory queries"""
    try:
        # Handle JSON requests (text only)
        if request and not files:
            try:
                json_data = await request.json()
                text = json_data.get("text", "")
                user_id = json_data.get("user_id", "demo_user")
            except:
                pass  # Continue with form data
        
        # Filter out None files
        if files:
            files = [f for f in files if f and f.filename]
        
        if not text and not files:
            raise HTTPException(status_code=400, detail="Either text or files are required")
        
        if not ai_processor:
            return {
                "response": "Demo Mode: AI processor not available. Please configure GEMINI_API_KEY and restart.",
                "demo_mode": True,
                "capabilities": {
                    "long_context": settings.ENABLE_LONG_CONTEXT,
                    "video_processing": settings.ENABLE_VIDEO_PROCESSING,
                    "native_audio": settings.ENABLE_AUDIO_NATIVE,
                    "max_context_tokens": settings.MAX_CONTEXT_TOKENS
                }
            }
        
        # Process files if provided
        processed_files = []
        temp_file_paths = []
        
        if files:
            for file in files:
                # Save file temporarily
                temp_path = f"/tmp/{uuid.uuid4()}_{file.filename}"
                content = await file.read()
                
                with open(temp_path, "wb") as f:
                    f.write(content)
                
                temp_file_paths.append(temp_path)
                
                # Determine media type
                media_type = "document"
                if file.content_type:
                    if file.content_type.startswith("image/"):
                        media_type = "image"
                    elif file.content_type.startswith("audio/"):
                        media_type = "audio"
                    elif file.content_type.startswith("video/"):
                        media_type = "video"
                
                file_info = {
                    "filename": file.filename,
                    "content_type": file.content_type,
                    "size": len(content),
                    "media_type": media_type,
                    "temp_path": temp_path
                }
                processed_files.append(file_info)
        
        # Create comprehensive analysis prompt
        if files and not text:
            if len(files) == 1:
                text = f"Please analyze this {processed_files[0]['media_type']} file and provide insights."
            else:
                file_types = [f['media_type'] for f in processed_files]
                unique_types = list(set(file_types))
                text = f"Please analyze these {len(files)} files ({', '.join(unique_types)}) and provide a comprehensive analysis."
        elif files and text:
            text += f"\n\nAdditionally, please analyze the {len(files)} uploaded file{'s' if len(files) > 1 else ''}."
        
        # Get context memories if memory manager is available
        context_memories = []
        if memory_manager:
            try:
                # Check if this is a memory query
                memory_keywords = ["remember", "recall", "memory", "memories", "what did", "tell me about"]
                is_memory_query = any(keyword in text.lower() for keyword in memory_keywords)
                
                if is_memory_query:
                    # Enhanced memory retrieval for memory queries
                    context_memories = await memory_manager.retrieve_context(
                        query=text,
                        user_id=user_id,
                        k=20,
                        use_long_context=True
                    )
                else:
                    # Standard proactive context
                    context_memories = await memory_manager.get_proactive_context(
                        user_id=user_id,
                        current_input=text,
                        max_memories=15
                    )
            except Exception as e:
                logger.warning(f"Memory retrieval failed: {e}")
        
        # Process with AI
        try:
            if len(processed_files) <= 1:
                # Single file or no file processing
                file_path = processed_files[0]['temp_path'] if processed_files else None
                media_type = processed_files[0]['media_type'] if processed_files else "text"
                
                result = await ai_processor.process_input(
                    text=text,
                    media_path=file_path,
                    media_type=media_type,
                    user_id=user_id,
                    context_memories=context_memories
                )
            else:
                # Multiple files - process them together with enhanced context
                result = await ai_processor.process_multiple_inputs(
                    text=text,
                    files_data=processed_files,
                    user_id=user_id,
                    context_memories=context_memories
                )
            
            # Add file info to result
            if processed_files:
                result["files_processed"] = [{
                    "filename": f["filename"],
                    "content_type": f["content_type"],
                    "size": f["size"],
                    "media_type": f["media_type"]
                } for f in processed_files]
            
            # Add memory context info
            if context_memories:
                result["memory_context"] = {
                    "memories_retrieved": len(context_memories),
                    "context_window_used": settings.MAX_CONTEXT_TOKENS,
                    "long_context_enabled": settings.ENABLE_LONG_CONTEXT
                }
            
        finally:
            # Clean up temp files
            for temp_path in temp_file_paths:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
        
        # Store in memory if available
        if memory_manager:
            try:
                content_to_store = text
                if processed_files:
                    file_names = [f["filename"] for f in processed_files]
                    if len(file_names) == 1:
                        content_to_store += f" [Processed {processed_files[0]['media_type']}: {file_names[0]}]"
                    else:
                        content_to_store += f" [Processed {len(file_names)} files: {', '.join(file_names)}]"
                
                await memory_manager.store_memory(
                    content=content_to_store,
                    content_type="multimodal" if processed_files else "text",
                    user_id=user_id,
                    media_url=', '.join([f["filename"] for f in processed_files]) if processed_files else None,
                    ai_response=result
                )
            except Exception as e:
                logger.warning(f"Memory storage failed: {e}")
        
        return result
        
    except Exception as e:
        logger.error(f"Unified processing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Keep existing endpoints for backward compatibility
@router.post("/process-text")
async def demo_process_text(request: dict):
    """Legacy text processing endpoint"""
    return await unified_process(text=request.get("text"), user_id=request.get("user_id", "demo_user"))

@router.post("/process-file")
async def demo_process_file(
    file: UploadFile = File(...),
    user_id: str = Form("demo_user"),
    description: Optional[str] = Form(None)
):
    """Legacy file processing endpoint"""
    return await unified_process(file=file, user_id=user_id, text=description)

@router.post("/query-memory")
async def demo_query_memory(request: dict):
    """Query memory for demo"""
    try:
        query = request.get("query", "")
        user_id = request.get("user_id", "demo_user")
        
        if not query.strip():
            raise HTTPException(status_code=400, detail="Query is required")
        
        if not memory_manager:
            return {
                "message": "Demo Mode: Memory manager not available. Database connections required.",
                "query": query,
                "user_id": user_id,
                "demo_mode": True
            }
        
        # Retrieve context
        memories = await memory_manager.retrieve_context(
            query=query,
            user_id=user_id,
            k=15,
            use_long_context=True
        )
        
        # Get proactive context
        proactive_memories = await memory_manager.get_proactive_context(
            user_id=user_id,
            current_input=query,
            max_memories=10
        )
        
        return {
            "query": query,
            "user_id": user_id,
            "memories_found": len(memories),
            "proactive_memories": len(proactive_memories),
            "memories": memories[:10],  # Limit for demo
            "proactive_context": proactive_memories[:5],
            "long_context_enabled": settings.ENABLE_LONG_CONTEXT,
            "context_window": f"{settings.MAX_CONTEXT_TOKENS:,} tokens"
        }
        
    except Exception as e:
        logger.error(f"Memory query failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/insights/{user_id}")
async def demo_get_insights(user_id: str):
    """Get memory insights for demo"""
    try:
        if not memory_manager:
            return {
                "message": "Demo Mode: Memory manager not available. Database connections required.",
                "user_id": user_id,
                "demo_mode": True,
                "total_memories": 0,
                "entity_network_size": 0,
                "trending_entities": [],
                "enhanced_features": {
                    "long_context_enabled": settings.ENABLE_LONG_CONTEXT,
                    "video_processing_enabled": settings.ENABLE_VIDEO_PROCESSING,
                    "native_audio_enabled": settings.ENABLE_AUDIO_NATIVE,
                    "max_context_tokens": settings.MAX_CONTEXT_TOKENS
                }
            }
        
        insights = await memory_manager.get_memory_insights(user_id)
        return insights
        
    except Exception as e:
        logger.error(f"Insights retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status")
async def demo_status():
    """Get demo system status"""
    return {
        "demo_frontend": "✅ Active",
        "ai_processor": "✅ Ready" if ai_processor else "❌ Not configured",
        "memory_manager": "✅ Ready" if memory_manager else "❌ Databases required",
        "file_storage": "✅ Ready" if file_storage else "❌ Not configured",
        "enhanced_capabilities": {
            "gemini_2_5_pro": True,
            "context_window": f"{settings.MAX_CONTEXT_TOKENS:,} tokens",
            "multimodal_support": True,
            "video_processing": settings.ENABLE_VIDEO_PROCESSING,
            "native_audio": settings.ENABLE_AUDIO_NATIVE,
            "long_context": settings.ENABLE_LONG_CONTEXT
        },
        "model_info": {
            "default_model": settings.DEFAULT_MODEL,
            "long_context_model": settings.LONG_CONTEXT_MODEL,
            "sdk_version": "google-genai-0.3.0"
        }
    } 