// const API_URL = 'https://pdf-translator-78s1.onrender.com';
const API_URL = 'http://localhost:8000';

let currentFile = null;
let resultBlob = null;

// Navigation
function showHome() {
    document.getElementById('homePage').style.display = 'block';
    document.getElementById('extractPage').classList.remove('active');
    document.getElementById('translatePage').classList.remove('active');
}

function showExtract() {
    document.getElementById('homePage').style.display = 'none';
    document.getElementById('extractPage').classList.add('active');
    document.getElementById('translatePage').classList.remove('active');
}

function showTranslate() {
    document.getElementById('homePage').style.display = 'none';
    document.getElementById('extractPage').classList.remove('active');
    document.getElementById('translatePage').classList.add('active');
}

// File Upload Handlers
function setupFileUpload(inputId, uploadBoxId, optionsId, btnId) {
    const input = document.getElementById(inputId);
    const uploadBox = document.getElementById(uploadBoxId);
    const options = document.getElementById(optionsId);
    const btn = document.getElementById(btnId);

    input.addEventListener('change', (e) => {
        if (e.target.files[0]) {
            currentFile = e.target.files[0];
            uploadBox.querySelector('h3').textContent = e.target.files[0].name;
            options.classList.add('active');
            btn.classList.add('active');
        }
    });

    // Drag and drop
    uploadBox.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadBox.classList.add('dragover');
    });

    uploadBox.addEventListener('dragleave', () => {
        uploadBox.classList.remove('dragover');
    });

    uploadBox.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadBox.classList.remove('dragover');
        
        const files = e.dataTransfer.files;
        if (files.length > 0 && files[0].type === 'application/pdf') {
            currentFile = files[0];
            input.files = files;
            uploadBox.querySelector('h3').textContent = files[0].name;
            options.classList.add('active');
            btn.classList.add('active');
        }
    });
}

setupFileUpload('extractFileInput', 'extractUploadBox', 'extractOptions', 'extractBtn');
setupFileUpload('translateFileInput', 'translateUploadBox', 'translateOptions', 'translateBtn');

// Process Extract
async function processExtract() {
    if (!currentFile) return;

    const lang = document.getElementById('extractLang').value;
    const useOCR = document.getElementById('extractUseOCR').checked;
    const format = document.getElementById('extractFormat').value;

    const formData = new FormData();
    formData.append('file', currentFile);
    formData.append('source_lang', lang);
    formData.append('target_lang', lang === 'auto' ? 'en' : lang); // Same as source for extraction
    formData.append('use_ocr', useOCR);
    formData.append('format', format);

    document.getElementById('extractBtn').style.display = 'none';
    document.getElementById('extractOptions').style.display = 'none';
    document.getElementById('extractProgress').classList.add('active');

    try {
        const response = await fetch(`${API_URL}/translate`, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Extraction failed');
        }

        resultBlob = await response.blob();
        
        document.getElementById('extractProgress').classList.remove('active');
        document.getElementById('extractResult').classList.add('active');
    } catch (error) {
        alert('Error: ' + error.message);
        resetExtract();
    }
}

// Process Translate
async function processTranslate() {
    if (!currentFile) return;

    const sourceLang = document.getElementById('sourceLang').value;
    const targetLang = document.getElementById('targetLang').value;
    const useOCR = document.getElementById('translateUseOCR').checked;
    const format = document.getElementById('translateFormat').value;

    // Validation
    if (sourceLang !== 'auto' && sourceLang === targetLang) {
        alert('Source and target languages must be different for translation!');
        return;
    }

    const formData = new FormData();
    formData.append('file', currentFile);
    formData.append('source_lang', sourceLang);
    formData.append('target_lang', targetLang);
    formData.append('use_ocr', useOCR);
    formData.append('format', format);

    document.getElementById('translateBtn').style.display = 'none';
    document.getElementById('translateOptions').style.display = 'none';
    document.getElementById('translateProgress').classList.add('active');

    try {
        const response = await fetch(`${API_URL}/translate`, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Translation failed');
        }

        resultBlob = await response.blob();
        
        document.getElementById('translateProgress').classList.remove('active');
        document.getElementById('translateResult').classList.add('active');
    } catch (error) {
        alert('Error: ' + error.message);
        resetTranslate();
    }
}

// Download Result
function downloadResult() {
    if (!resultBlob) return;

    const url = window.URL.createObjectURL(resultBlob);
    const a = document.createElement('a');
    a.href = url;
    
    // Determine which format was used
    let format;
    if (document.getElementById('extractResult').classList.contains('active')) {
        format = document.getElementById('extractFormat').value;
    } else {
        format = document.getElementById('translateFormat').value;
    }
    
    a.download = `result.${format}`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
}

// Reset Functions
function resetExtract() {
    currentFile = null;
    resultBlob = null;
    document.getElementById('extractFileInput').value = '';
    document.getElementById('extractUploadBox').querySelector('h3').textContent = 'Select PDF file';
    document.getElementById('extractOptions').classList.remove('active');
    document.getElementById('extractBtn').classList.remove('active');
    document.getElementById('extractBtn').style.display = 'block';
    document.getElementById('extractOptions').style.display = 'block';
    document.getElementById('extractProgress').classList.remove('active');
    document.getElementById('extractResult').classList.remove('active');
}

function resetTranslate() {
    currentFile = null;
    resultBlob = null;
    document.getElementById('translateFileInput').value = '';
    document.getElementById('translateUploadBox').querySelector('h3').textContent = 'Select PDF file';
    document.getElementById('translateOptions').classList.remove('active');
    document.getElementById('translateBtn').classList.remove('active');
    document.getElementById('translateBtn').style.display = 'block';
    document.getElementById('translateOptions').style.display = 'block';
    document.getElementById('translateProgress').classList.remove('active');
    document.getElementById('translateResult').classList.remove('active');
}

// Optional: Load all supported languages dynamically
async function loadAllLanguages() {
    try {
        const response = await fetch(`${API_URL}/languages`);
        const data = await response.json();
        
        console.log('Supported languages:', data.total);
        // You can use data.languages to populate dropdowns with all languages
        // Example: populateLanguageDropdowns(data.languages);
    } catch (error) {
        console.error('Failed to load languages:', error);
    }
}

// Uncomment to load all languages on page load
// loadAllLanguages();