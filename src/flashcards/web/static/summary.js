// AI Document Summarizer - Main JavaScript
// Professional interactions and animations

class SummarizerApp {
    constructor() {
        this.currentGenerationId = null;
        this.pollingInterval = null;
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.setupDragAndDrop();
        this.setupMobileMenu();
        this.setupConfigurationHandlers();
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
                    const icon = mobileMenuToggle.querySelector('i');
                    icon.className = 'fas fa-bars';
                }
            });
        }
    }

    setupConfigurationHandlers() {
        // Slider value updates
        const sliders = [
            { id: 'chunkSize', valueId: 'chunkSizeValue' },
            { id: 'overlapWords', valueId: 'overlapWordsValue' },
            { id: 'summaryLength', valueId: 'summaryLengthValue' },
            { id: 'finalSummaryLength', valueId: 'finalSummaryLengthValue' }
        ];

        sliders.forEach(({ id, valueId }) => {
            const slider = document.getElementById(id);
            const valueDisplay = document.getElementById(valueId);
            
            if (slider && valueDisplay) {
                slider.addEventListener('input', (e) => {
                    valueDisplay.textContent = e.target.value;
                    this.updateOverlapWarning();
                });
            }
        });

        // Preset buttons
        const presetButtons = document.querySelectorAll('.preset-btn');
        presetButtons.forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                const preset = btn.dataset.preset;
                this.applyPreset(preset);
                
                // Update active state
                presetButtons.forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
            });
        });

        // Advanced toggle (if needed)
        const advancedToggle = document.getElementById('advancedToggle');
        if (advancedToggle) {
            advancedToggle.addEventListener('click', (e) => {
                e.preventDefault();
                // Could expand/collapse advanced options
                console.log('🔧 Advanced settings toggled');
            });
        }

        // Initialize overlap warning
        this.updateOverlapWarning();
    }

    applyPreset(preset) {
        const presets = {
            fast: {
                chunkSize: 150,
                overlapWords: 5,
                summaryLength: 75,
                finalSummaryLength: 200,
                processingQuality: 'fast'
            },
            balanced: {
                chunkSize: 200,
                overlapWords: 10,
                summaryLength: 120,
                finalSummaryLength: 350,
                processingQuality: 'balanced'
            },
            detailed: {
                chunkSize: 300,
                overlapWords: 15,
                summaryLength: 150,
                finalSummaryLength: 500,
                processingQuality: 'high'
            }
        };

        const config = presets[preset];
        if (!config) return;

        // Apply settings
        Object.entries(config).forEach(([key, value]) => {
            const element = document.getElementById(key);
            if (element) {
                element.value = value;
                
                // Update slider displays
                if (element.type === 'range') {
                    const valueDisplay = document.getElementById(`${key}Value`);
                    if (valueDisplay) {
                        valueDisplay.textContent = value;
                    }
                }
            }
        });

        this.updateOverlapWarning();
        console.log(`🎯 Applied ${preset} preset`);
    }

    updateOverlapWarning() {
        const overlapInput = document.getElementById('overlapWords');
        const overlapGroup = overlapInput?.closest('.config-group');
        const helpText = overlapGroup?.querySelector('.help-text');
        
        if (!overlapInput || !helpText) return;

        const overlap = parseInt(overlapInput.value);
        
        if (overlap > 15) {
            helpText.style.color = 'var(--warning)';
            helpText.textContent = '⚠️ High overlap (>15 words) may slow processing';
        } else if (overlap === 0) {
            helpText.style.color = 'var(--info)';
            helpText.textContent = 'ℹ️ Zero overlap may lose context between chunks';
        } else {
            helpText.style.color = 'var(--gray)';
            helpText.textContent = 'Recommended: 10 words for optimal context';
        }
    }

    // Configuration handlers restored with working functionality

    getConfiguration() {
        // Always use QWEN3 30B A3B model, but read other settings from the form
        return {
            model: 'qwen/qwen3-30b-a3b-2507', // Fixed to the best model
            chunkSize: parseInt(document.getElementById('chunkSize')?.value) || 200,
            overlapWords: parseInt(document.getElementById('overlapWords')?.value) || 10,
            summaryLength: parseInt(document.getElementById('summaryLength')?.value) || 120,
            finalSummaryLength: parseInt(document.getElementById('finalSummaryLength')?.value) || 350,
            processingQuality: document.getElementById('processingQuality')?.value || 'balanced'
        };
    }

    async handleFileUpload(file) {
        console.log('📁 File selected:', file.name, `(${(file.size / 1024 / 1024).toFixed(2)} MB)`);
        
        // Validate file
        const maxSize = 50 * 1024 * 1024; // 50MB
        if (file.size > maxSize) {
            this.showError('File size too large. Maximum size is 50MB.');
            return;
        }

        const allowedTypes = ['.pdf', '.docx', '.txt', '.md', '.html'];
        const fileExtension = '.' + file.name.split('.').pop().toLowerCase();
        if (!allowedTypes.includes(fileExtension)) {
            this.showError('Unsupported file type. Please use PDF, DOCX, TXT, MD, or HTML files.');
            return;
        }

        try {
            // Show processing UI
            this.showProcessing(file.name);
            
            // Get configuration settings
            const config = this.getConfiguration();
            console.log('⚙️ Configuration:', config);
            
            // Prepare form data
            const formData = new FormData();
            formData.append('file', file);
            
            // Add configuration as JSON
            formData.append('config', JSON.stringify(config));
            
            console.log('🚀 Starting summary generation...');
            
            // Upload and start generation
            const response = await fetch('/api/generate-summary', {
                method: 'POST',
                body: formData
            });
            
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({ error: 'Upload failed' }));
                throw new Error(errorData.error || `HTTP ${response.status}`);
            }
            
            const data = await response.json();
            console.log('✅ Summary generation started:', data);
            
            this.currentGenerationId = data.generation_id;
            this.startPolling();
            
        } catch (error) {
            console.error('❌ Upload error:', error);
            this.showError(`Upload failed: ${error.message}`);
            this.hideProcessing();
        }
    }

    showProcessing(filename) {
        const uploadSection = document.querySelector('.upload-section');
        const processingSection = document.getElementById('processingSection');
        
        if (uploadSection) uploadSection.style.display = 'none';
        if (processingSection) {
            processingSection.style.display = 'block';
            
            // Set filename
            const processingFile = document.getElementById('processingFile');
            if (processingFile) {
                processingFile.textContent = `Summarizing: ${filename}`;
            }
            
            // Reset progress
            this.updateProgress(0, 'Starting summary generation...');
            this.resetSteps();
        }
    }

    hideProcessing() {
        const uploadSection = document.querySelector('.upload-section');
        const processingSection = document.getElementById('processingSection');
        
        if (uploadSection) uploadSection.style.display = 'block';
        if (processingSection) processingSection.style.display = 'none';
    }

    resetSteps() {
        const steps = document.querySelectorAll('.step');
        steps.forEach(step => {
            step.classList.remove('active', 'completed');
        });
    }

    updateProgress(percent, status) {
        const progressFill = document.getElementById('progressFill');
        const progressPercent = document.getElementById('progressPercent');
        const progressStatus = document.getElementById('progressStatus');
        
        if (progressFill) {
            progressFill.style.width = `${percent}%`;
        }
        
        if (progressPercent) {
            progressPercent.textContent = `${Math.round(percent)}%`;
        }
        
        if (progressStatus) {
            progressStatus.textContent = status;
        }
        
        // Update steps based on progress
        this.updateSteps(percent);
    }

    updateSteps(progress) {
        const steps = {
            'step-load': { threshold: 0, text: 'Loading document' },
            'step-process': { threshold: 25, text: 'AI processing content' },
            'step-generate': { threshold: 50, text: 'Creating summary' },
            'step-complete': { threshold: 100, text: 'Complete!' }
        };
        
        Object.entries(steps).forEach(([stepId, config]) => {
            const step = document.getElementById(stepId);
            if (step) {
                if (progress >= config.threshold) {
                    step.classList.add('completed');
                    step.classList.remove('active');
                } else if (progress >= config.threshold - 25) {
                    step.classList.add('active');
                    step.classList.remove('completed');
                } else {
                    step.classList.remove('active', 'completed');
                }
            }
        });
    }

    getProgressStatus(progress) {
        if (progress < 25) return 'Loading document...';
        if (progress < 50) return 'AI processing content...';
        if (progress < 100) return 'Creating summary...';
        return 'Redirecting to results...';
    }

    async startPolling() {
        if (this.pollingInterval) {
            clearInterval(this.pollingInterval);
        }
        
        console.log('📊 Starting status polling...');
        
        this.pollingInterval = setInterval(async () => {
            try {
                await this.pollStatus();
            } catch (error) {
                console.error('❌ Polling error:', error);
                this.stopPolling();
                this.showError('Connection lost. Please try again.');
            }
        }, 2000);
        
        // Initial poll
        setTimeout(() => this.pollStatus(), 500);
    }

    async pollStatus() {
        if (!this.currentGenerationId) return;
        
        const response = await fetch(`/api/status/${this.currentGenerationId}`);
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        
        const status = await response.json();
        console.log('📈 Status update:', status);
        
        // Update progress
        const progress = status.progress || 0;
        const statusText = status.status || this.getProgressStatus(progress);
        this.updateProgress(progress, statusText);
        
        // Check if complete
        if (status.status === 'completed' && status.result_url) {
            console.log('✅ Summary generation completed!');
            this.stopPolling();
            
            // Small delay for final animation
            setTimeout(() => {
                window.location.href = status.result_url;
            }, 1500);
        } else if (status.status === 'failed') {
            console.error('❌ Summary generation failed:', status.error);
            this.stopPolling();
            this.showError(status.error || 'Summary generation failed');
        }
    }

    stopPolling() {
        if (this.pollingInterval) {
            clearInterval(this.pollingInterval);
            this.pollingInterval = null;
        }
    }

    showError(message) {
        // Create or update error message
        let errorDiv = document.querySelector('.error-message');
        
        if (!errorDiv) {
            errorDiv = document.createElement('div');
            errorDiv.className = 'error-message';
            
            const uploadSection = document.querySelector('.upload-section');
            if (uploadSection) {
                uploadSection.appendChild(errorDiv);
            }
        }
        
        errorDiv.innerHTML = `
            <div class="error-content">
                <i class="fas fa-exclamation-triangle"></i>
                <span>${message}</span>
                <button class="error-dismiss" onclick="this.parentElement.parentElement.remove()">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        `;
        
        errorDiv.style.display = 'block';
        
        // Auto-dismiss after 10 seconds
        setTimeout(() => {
            if (errorDiv && errorDiv.parentElement) {
                errorDiv.remove();
            }
        }, 10000);
    }

    animateOnLoad() {
        // Animate elements on page load
        const animatedElements = document.querySelectorAll('.hero-title, .hero-description, .upload-container, .feature-card');
        
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.style.opacity = '1';
                    entry.target.style.transform = 'translateY(0)';
                }
            });
        });
        
        animatedElements.forEach((el, index) => {
            el.style.opacity = '0';
            el.style.transform = 'translateY(30px)';
            el.style.transition = `opacity 0.6s ease ${index * 0.1}s, transform 0.6s ease ${index * 0.1}s`;
            observer.observe(el);
        });
    }
}

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    console.log('🚀 AI Document Summarizer initialized');
    new SummarizerApp();
});

// Global error handler
window.addEventListener('error', (e) => {
    console.error('💥 Global error:', e.error);
});

// Handle page visibility changes
document.addEventListener('visibilitychange', () => {
    if (document.hidden) {
        console.log('📱 Page hidden');
    } else {
        console.log('📱 Page visible');
    }
});
