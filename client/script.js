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
    
    const formData = new FormData(form);
    
    // Update UI - processing state
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner"></span>Processing...';
    msg.style.display = 'block';
    msg.className = 'message info';
    msg.textContent = 'Translating PDF... This may take several minutes for large files.';

    try {
        const response = await fetch('/translate', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            throw new Error('Translation failed. Please try again.');
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
        msg.className = 'message success';
        msg.textContent = '✓ Translation complete! File downloaded successfully.';
        
    } catch (error) {
        // Update UI - error state
        msg.className = 'message error';
        msg.textContent = '✗ Error: ' + error.message;
        
    } finally {
        // Reset button state
        btn.disabled = false;
        btn.textContent = 'Translate PDF';
    }
});