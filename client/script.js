const API_URL = 'https://your-render-app.onrender.com';

const form = document.getElementById('form');
const fileInput = document.getElementById('file');
const uploadBox = document.getElementById('uploadBox');
const btn = document.getElementById('btn');
const msg = document.getElementById('msg');
const filename = document.getElementById('filename');

// Handle file selection via click
uploadBox.addEventListener('click', () => {
    fileInput.click();
});

// Handle drag and drop
uploadBox.addEventListener('dragover', (e) => {
    e.preventDefault();
    uploadBox.style.borderColor = '#667eea';
    uploadBox.style.background = '#f0f2ff';
});

uploadBox.addEventListener('dragleave', () => {
    uploadBox.style.borderColor = '#ddd';
    uploadBox.style.background = 'transparent';
});

uploadBox.addEventListener('drop', (e) => {
    e.preventDefault();
    uploadBox.style.borderColor = '#ddd';
    uploadBox.style.background = 'transparent';
    
    const files = e.dataTransfer.files;
    if (files.length > 0 && files[0].type === 'application/pdf') {
        fileInput.files = files;
        filename.textContent = files[0].name;
    }
});

// Update filename display
fileInput.addEventListener('change', (e) => {
    if (e.target.files[0]) {
        filename.textContent = e.target.files[0].name;
    }
});

// Handle form submission
form.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const file = fileInput.files[0];
    if (!file) {
        showMessage('Please select a PDF file', 'error');
        return;
    }

    const direction = document.querySelector('input[name="direction"]:checked').value;
    
    const formData = new FormData();
    formData.append('file', file);
    formData.append('direction', direction);
    
    // Update UI - processing state
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner"></span>Processing...';
    msg.style.display = 'block';
    msg.className = 'message info';
    msg.textContent = 'Translating PDF... This may take several minutes for large files.';

    try {
        const response = await fetch(`${API_URL}/translate`, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({ detail: 'Translation failed' }));
            throw new Error(errorData.detail || 'Translation failed. Please try again.');
        }

        // Download the translated file
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'translated.docx';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);

        // Update UI - success state
        showMessage('✓ Translation complete! File downloaded successfully.', 'success');
        
    } catch (error) {
        console.error('Translation error:', error);
        showMessage('✗ Error: ' + error.message, 'error');
        
    } finally {
        // Reset button state
        btn.disabled = false;
        btn.textContent = 'Translate PDF';
    }
});

function showMessage(text, type) {
    msg.style.display = 'block';
    msg.className = `message ${type}`;
    msg.textContent = text;
}