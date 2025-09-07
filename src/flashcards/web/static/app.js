// AI Flashcards Generator - Main JavaScript
// Professional interactions and animations

class FlashcardsApp {
    constructor() {
        this.currentGenerationId = null;
        this.pollingInterval = null;
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.setupDragAndDrop();
        this.setupMobileMenu();
        this.animateOnLoad();
    }

    setupEventListeners() {
        // File input handling
        const fileInput = document.getElementById('fileInput');
        const uploadArea = document.getElementById('uploadArea');
        const browseLink = document.querySelector('.browse-link');

        if (fileInput && uploadArea && browseLink) {
            // Click to browse
            uploadArea.addEventListener('click', () => fileInput.click());
            browseLink.addEventListener('click', (e) => {
                e.stopPropagation();
                fileInput.click();
            });

            // File selection
            fileInput.addEventListener('change', (e) => {
                if (e.target.files.length > 0) {
                    this.handleFileUpload(e.target.files[0]);
                }
            });
        }
    }

    setupDragAndDrop() {
        const uploadArea = document.getElementById('uploadArea');
        if (!uploadArea) return;

        // Prevent default drag behaviors
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            uploadArea.addEventListener(eventName, this.preventDefaults, false);
            document.body.addEventListener(eventName, this.preventDefaults, false);
        });

        // Highlight drop area when item is dragged over it
        ['dragenter', 'dragover'].forEach(eventName => {
            uploadArea.addEventListener(eventName, () => {
                uploadArea.classList.add('dragover');
            }, false);
        });

        ['dragleave', 'drop'].forEach(eventName => {
            uploadArea.addEventListener(eventName, () => {
                uploadArea.classList.remove('dragover');
            }, false);
        });

        // Handle dropped files
        uploadArea.addEventListener('drop', (e) => {
            const dt = e.dataTransfer;
            const files = dt.files;
            
            if (files.length > 0) {
                this.handleFileUpload(files[0]);
            }
        }, false);
    }

    preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    setupMobileMenu() {
        const mobileMenuToggle = document.getElementById('mobileMenuToggle');
        const navLinks = document.querySelector('.nav-links');
        
        if (mobileMenuToggle && navLinks) {
            mobileMenuToggle.addEventListener('click', () => {
                navLinks.classList.toggle('mobile-open');
                
                // Animate icon
                const icon = mobileMenuToggle.querySelector('i');
                if (navLinks.classList.contains('mobile-open')) {
                    icon.className = 'fas fa-times';
                } else {
                    icon.className = 'fas fa-bars';
                }
            });
            
            // Close menu when clicking outside
            document.addEventListener('click', (e) => {
                if (!mobileMenuToggle.contains(e.target) && !navLinks.contains(e.target)) {
                    navLinks.classList.remove('mobile-open');
                    mobileMenuToggle.querySelector('i').className = 'fas fa-bars';
                }
            });
            
            // Close menu when clicking nav links
            navLinks.addEventListener('click', (e) => {
                if (e.target.classList.contains('nav-link')) {
                    navLinks.classList.remove('mobile-open');
                    mobileMenuToggle.querySelector('i').className = 'fas fa-bars';
                }
            });
        }
    }

    async handleFileUpload(file) {
        // Validate file type
        const allowedTypes = ['.pdf', '.docx', '.txt', '.md', '.html'];
        const fileExtension = '.' + file.name.split('.').pop().toLowerCase();
        
        if (!allowedTypes.includes(fileExtension)) {
            this.showError(`Unsupported file type. Please upload: ${allowedTypes.join(', ')}`);
            return;
        }

        // Validate file size (10MB limit)
        if (file.size > 10 * 1024 * 1024) {
            this.showError('File size too large. Please upload files smaller than 10MB.');
            return;
        }

        try {
            // Show processing UI
            this.showProcessingUI(file.name);
            
            // Create form data
            const formData = new FormData();
            formData.append('file', file);

            // Upload file
            const response = await fetch('/api/upload', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                throw new Error(`Upload failed: ${response.statusText}`);
            }

            const result = await response.json();
            this.currentGenerationId = result.generation_id;

            // Start polling for status
            this.startStatusPolling();

        } catch (error) {
            this.showError(`Upload failed: ${error.message}`);
            this.hideProcessingUI();
        }
    }

    showProcessingUI(filename) {
        const uploadSection = document.querySelector('.upload-section');
        const processingSection = document.getElementById('processingSection');
        const processingFile = document.getElementById('processingFile');

        if (uploadSection) uploadSection.style.display = 'none';
        if (processingSection) processingSection.style.display = 'block';
        if (processingFile) processingFile.textContent = `Processing: ${filename}`;

        // Animate in
        setTimeout(() => {
            if (processingSection) {
                processingSection.classList.add('fade-in-up');
            }
        }, 100);
    }

    hideProcessingUI() {
        const uploadSection = document.querySelector('.upload-section');
        const processingSection = document.getElementById('processingSection');

        if (processingSection) processingSection.style.display = 'none';
        if (uploadSection) uploadSection.style.display = 'block';
    }

    startStatusPolling() {
        if (this.pollingInterval) {
            clearInterval(this.pollingInterval);
        }

        this.pollingInterval = setInterval(async () => {
            try {
                const response = await fetch(`/api/status/${this.currentGenerationId}`);
                if (!response.ok) throw new Error('Status check failed');

                const status = await response.json();
                this.updateProcessingStatus(status);

                if (status.status === 'completed') {
                    clearInterval(this.pollingInterval);
                    this.redirectToResults();
                } else if (status.status === 'error') {
                    clearInterval(this.pollingInterval);
                    this.showError(`Generation failed: ${status.error}`);
                    this.hideProcessingUI();
                }
            } catch (error) {
                console.error('Status polling error:', error);
            }
        }, 1000);
    }

    updateProcessingStatus(status) {
        const progressFill = document.getElementById('progressFill');
        const progressPercent = document.getElementById('progressPercent');
        const progressStatus = document.getElementById('progressStatus');

        if (progressFill) {
            progressFill.style.width = `${status.progress}%`;
        }

        if (progressPercent) {
            progressPercent.textContent = `${status.progress}%`;
        }

        // Update status text and steps
        const statusText = this.getStatusText(status.progress);
        if (progressStatus) {
            progressStatus.textContent = statusText;
        }

        this.updateProcessingSteps(status.progress);
    }

    getStatusText(progress) {
        if (progress < 20) return 'Initializing...';
        if (progress < 40) return 'Loading document...';
        if (progress < 70) return 'AI processing content...';
        if (progress < 95) return 'Generating flashcards...';
        return 'Finalizing...';
    }

    updateProcessingSteps(progress) {
        const steps = ['step-load', 'step-process', 'step-generate', 'step-complete'];
        
        steps.forEach((stepId, index) => {
            const step = document.getElementById(stepId);
            if (!step) return;

            const threshold = (index + 1) * 25;
            
            if (progress >= threshold) {
                step.classList.add('completed');
                step.classList.remove('active');
            } else if (progress >= threshold - 25) {
                step.classList.add('active');
                step.classList.remove('completed');
            } else {
                step.classList.remove('active', 'completed');
            }
        });
    }

    redirectToResults() {
        // Add a nice transition effect
        document.body.style.opacity = '0';
        
        setTimeout(() => {
            window.location.href = `/results/${this.currentGenerationId}`;
        }, 500);
    }

    showError(message) {
        // Create error notification
        const errorDiv = document.createElement('div');
        errorDiv.className = 'error-notification';
        errorDiv.innerHTML = `
            <div class="error-content">
                <i class="fas fa-exclamation-triangle"></i>
                <span>${message}</span>
                <button class="error-close">&times;</button>
            </div>
        `;

        // Add styles
        errorDiv.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: var(--error);
            color: white;
            padding: 1rem;
            border-radius: var(--radius-md);
            box-shadow: var(--shadow-lg);
            z-index: 1000;
            animation: slideInRight 0.3s ease-out;
            max-width: 400px;
        `;

        document.body.appendChild(errorDiv);

        // Auto remove after 5 seconds
        setTimeout(() => {
            if (errorDiv.parentNode) {
                errorDiv.style.animation = 'slideOutRight 0.3s ease-in';
                setTimeout(() => errorDiv.remove(), 300);
            }
        }, 5000);

        // Manual close
        const closeBtn = errorDiv.querySelector('.error-close');
        closeBtn.addEventListener('click', () => {
            errorDiv.style.animation = 'slideOutRight 0.3s ease-in';
            setTimeout(() => errorDiv.remove(), 300);
        });
    }

    animateOnLoad() {
        // Add staggered animations to feature cards
        const featureCards = document.querySelectorAll('.feature-card');
        featureCards.forEach((card, index) => {
            card.style.opacity = '0';
            card.style.transform = 'translateY(30px)';
            
            setTimeout(() => {
                card.style.transition = 'all 0.6s ease-out';
                card.style.opacity = '1';
                card.style.transform = 'translateY(0)';
            }, 200 * index);
        });

        // Animate upload area on load
        const uploadArea = document.getElementById('uploadArea');
        if (uploadArea) {
            uploadArea.style.opacity = '0';
            uploadArea.style.transform = 'scale(0.95)';
            
            setTimeout(() => {
                uploadArea.style.transition = 'all 0.5s ease-out';
                uploadArea.style.opacity = '1';
                uploadArea.style.transform = 'scale(1)';
            }, 300);
        }
    }
}

// Utility functions
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// Add CSS animations dynamically
const animationCSS = `
    @keyframes slideInRight {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    @keyframes slideOutRight {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(100%);
            opacity: 0;
        }
    }
    
    .error-content {
        display: flex;
        align-items: center;
        gap: 0.75rem;
    }
    
    .error-close {
        background: none;
        border: none;
        color: white;
        font-size: 1.25rem;
        cursor: pointer;
        margin-left: auto;
        padding: 0.25rem;
        border-radius: 0.25rem;
        transition: background-color 0.2s;
    }
    
    .error-close:hover {
        background-color: rgba(255, 255, 255, 0.2);
    }
`;

const styleSheet = document.createElement('style');
styleSheet.textContent = animationCSS;
document.head.appendChild(styleSheet);

// Initialize the app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.flashcardsApp = new FlashcardsApp();
});
