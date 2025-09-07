// Results Page JavaScript
// Interactive flashcard functionality

class ResultsPage {
    constructor() {
        this.flashcards = [];
        this.viewMode = 'grid'; // 'grid' or 'list'
        this.init();
    }

    init() {
        this.loadFlashcardsData();
        this.setupEventListeners();
        this.setupMobileMenu();
        this.animateCardsOnLoad();
    }

    loadFlashcardsData() {
        const dataElement = document.getElementById('flashcards-data');
        if (dataElement) {
            try {
                this.flashcards = JSON.parse(dataElement.textContent);
            } catch (error) {
                console.error('Failed to load flashcards data:', error);
            }
        }
    }

    setupEventListeners() {
        // View toggle
        const toggleBtn = document.querySelector('button[onclick="toggleViewMode()"]');
        if (toggleBtn) {
            toggleBtn.onclick = () => this.toggleViewMode();
        }

        // Copy all button
        const copyAllBtn = document.querySelector('button[onclick="copyToClipboard()"]');
        if (copyAllBtn) {
            copyAllBtn.onclick = () => this.copyAllToClipboard();
        }

        // Individual copy buttons in list view
        document.querySelectorAll('button[onclick^="copyCard"]').forEach(btn => {
            const match = btn.onclick.toString().match(/copyCard\((\d+)\)/);
            if (match) {
                const index = parseInt(match[1]);
                btn.onclick = () => this.copyCard(index);
            }
        });

        // Keyboard navigation
        document.addEventListener('keydown', (e) => this.handleKeyboardNavigation(e));
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
        }
    }

    animateCardsOnLoad() {
        const cards = document.querySelectorAll('.flashcard');
        cards.forEach((card, index) => {
            card.style.opacity = '0';
            card.style.transform = 'translateY(30px) scale(0.95)';
            
            setTimeout(() => {
                card.style.transition = 'all 0.6s ease-out';
                card.style.opacity = '1';
                card.style.transform = 'translateY(0) scale(1)';
            }, 100 * index);
        });

        // Animate list items if in list view
        const listItems = document.querySelectorAll('.flashcard-item');
        listItems.forEach((item, index) => {
            item.style.opacity = '0';
            item.style.transform = 'translateX(-30px)';
            
            setTimeout(() => {
                item.style.transition = 'all 0.5s ease-out';
                item.style.opacity = '1';
                item.style.transform = 'translateX(0)';
            }, 150 * index);
        });
    }

    flipCard(cardElement) {
        // Add flipping animation class
        cardElement.classList.add('flipping');
        
        // Toggle flipped state after a short delay
        setTimeout(() => {
            cardElement.classList.toggle('flipped');
            cardElement.classList.remove('flipping');
        }, 100);

        // Add subtle sound effect (if audio is available)
        this.playFlipSound();
    }

    toggleViewMode() {
        const gridView = document.getElementById('flashcardsGrid');
        const listView = document.getElementById('flashcardsList');
        const toggleIcon = document.getElementById('viewToggleIcon');
        const toggleText = document.getElementById('viewToggleText');

        if (this.viewMode === 'grid') {
            // Switch to list view
            this.viewMode = 'list';
            if (gridView) gridView.style.display = 'none';
            if (listView) listView.style.display = 'block';
            if (toggleIcon) toggleIcon.className = 'fas fa-th';
            if (toggleText) toggleText.textContent = 'Grid View';
            
            // Animate list items
            this.animateViewTransition('list');
        } else {
            // Switch to grid view
            this.viewMode = 'grid';
            if (listView) listView.style.display = 'none';
            if (gridView) gridView.style.display = 'grid';
            if (toggleIcon) toggleIcon.className = 'fas fa-th-large';
            if (toggleText) toggleText.textContent = 'List View';
            
            // Animate grid items
            this.animateViewTransition('grid');
        }

        // Store preference
        localStorage.setItem('flashcards-view-mode', this.viewMode);
    }

    animateViewTransition(mode) {
        const container = mode === 'grid' ? 
            document.getElementById('flashcardsGrid') : 
            document.getElementById('flashcardsList');
        
        if (!container) return;

        // Reset and animate
        const items = container.children;
        Array.from(items).forEach((item, index) => {
            item.style.opacity = '0';
            item.style.transform = mode === 'grid' ? 
                'scale(0.8) translateY(20px)' : 
                'translateX(-30px)';
            
            setTimeout(() => {
                item.style.transition = 'all 0.4s ease-out';
                item.style.opacity = '1';
                item.style.transform = 'scale(1) translateY(0) translateX(0)';
            }, 50 * index);
        });
    }

    copyAllToClipboard() {
        if (!this.flashcards || this.flashcards.length === 0) {
            this.showNotification('No flashcards to copy', 'warning');
            return;
        }

        let copyText = '# Flashcards\n\n';
        this.flashcards.forEach((card, index) => {
            copyText += `## Card ${index + 1}\n\n`;
            copyText += `**Question:** ${card.front}\n\n`;
            copyText += `**Answer:** ${card.back}\n\n`;
            copyText += '---\n\n';
        });

        this.copyToClipboard(copyText, 'All flashcards copied to clipboard!');
    }

    copyCard(index) {
        if (!this.flashcards || !this.flashcards[index]) {
            this.showNotification('Card not found', 'error');
            return;
        }

        const card = this.flashcards[index];
        const copyText = `**Question:** ${card.front}\n\n**Answer:** ${card.back}`;
        
        this.copyToClipboard(copyText, `Card #${index + 1} copied!`);
    }

    async copyToClipboard(text, successMessage) {
        try {
            await navigator.clipboard.writeText(text);
            this.showNotification(successMessage, 'success');
        } catch (error) {
            // Fallback for older browsers
            const textArea = document.createElement('textarea');
            textArea.value = text;
            textArea.style.position = 'fixed';
            textArea.style.opacity = '0';
            document.body.appendChild(textArea);
            textArea.select();
            
            try {
                document.execCommand('copy');
                this.showNotification(successMessage, 'success');
            } catch (fallbackError) {
                this.showNotification('Failed to copy to clipboard', 'error');
            }
            
            document.body.removeChild(textArea);
        }
    }

    handleKeyboardNavigation(e) {
        // Space bar to flip cards in grid view
        if (e.code === 'Space' && this.viewMode === 'grid') {
            e.preventDefault();
            const focusedCard = document.activeElement.closest('.flashcard');
            if (focusedCard) {
                this.flipCard(focusedCard);
            } else {
                // Flip a random card if none focused
                const cards = document.querySelectorAll('.flashcard');
                if (cards.length > 0) {
                    const randomCard = cards[Math.floor(Math.random() * cards.length)];
                    this.flipCard(randomCard);
                }
            }
        }

        // Arrow keys to navigate cards
        if (['ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown'].includes(e.code)) {
            this.navigateCards(e.code);
        }

        // V key to toggle view mode
        if (e.code === 'KeyV' && !e.ctrlKey && !e.altKey) {
            this.toggleViewMode();
        }

        // C key to copy all
        if (e.code === 'KeyC' && e.ctrlKey && e.shiftKey) {
            e.preventDefault();
            this.copyAllToClipboard();
        }
    }

    navigateCards(direction) {
        const cards = this.viewMode === 'grid' ? 
            document.querySelectorAll('.flashcard') :
            document.querySelectorAll('.flashcard-item');
        
        if (cards.length === 0) return;

        const currentIndex = Array.from(cards).findIndex(card => 
            card === document.activeElement || card.contains(document.activeElement)
        );

        let nextIndex;
        const cols = this.viewMode === 'grid' ? Math.floor(window.innerWidth / 350) : 1;

        switch (direction) {
            case 'ArrowLeft':
                nextIndex = currentIndex > 0 ? currentIndex - 1 : cards.length - 1;
                break;
            case 'ArrowRight':
                nextIndex = currentIndex < cards.length - 1 ? currentIndex + 1 : 0;
                break;
            case 'ArrowUp':
                nextIndex = currentIndex - cols;
                if (nextIndex < 0) nextIndex = currentIndex;
                break;
            case 'ArrowDown':
                nextIndex = currentIndex + cols;
                if (nextIndex >= cards.length) nextIndex = currentIndex;
                break;
            default:
                return;
        }

        if (cards[nextIndex]) {
            cards[nextIndex].focus();
            cards[nextIndex].scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
    }

    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        
        const icon = {
            success: 'fa-check-circle',
            warning: 'fa-exclamation-triangle',
            error: 'fa-times-circle',
            info: 'fa-info-circle'
        }[type] || 'fa-info-circle';

        notification.innerHTML = `
            <div class="notification-content">
                <i class="fas ${icon}"></i>
                <span>${message}</span>
                <button class="notification-close">&times;</button>
            </div>
        `;

        // Add styles
        const colors = {
            success: '#10b981',
            warning: '#f59e0b',
            error: '#ef4444',
            info: '#3b82f6'
        };

        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: ${colors[type] || colors.info};
            color: white;
            padding: 1rem 1.5rem;
            border-radius: var(--radius-md);
            box-shadow: var(--shadow-lg);
            z-index: 1000;
            animation: slideInRight 0.3s ease-out;
            max-width: 350px;
            font-weight: 500;
        `;

        document.body.appendChild(notification);

        // Auto remove
        setTimeout(() => {
            if (notification.parentNode) {
                notification.style.animation = 'slideOutRight 0.3s ease-in';
                setTimeout(() => notification.remove(), 300);
            }
        }, 3000);

        // Manual close
        const closeBtn = notification.querySelector('.notification-close');
        closeBtn.addEventListener('click', () => {
            notification.style.animation = 'slideOutRight 0.3s ease-in';
            setTimeout(() => notification.remove(), 300);
        });
    }

    playFlipSound() {
        // Create a subtle audio cue for card flips
        try {
            const audioContext = new (window.AudioContext || window.webkitAudioContext)();
            const oscillator = audioContext.createOscillator();
            const gainNode = audioContext.createGain();
            
            oscillator.connect(gainNode);
            gainNode.connect(audioContext.destination);
            
            oscillator.frequency.setValueAtTime(800, audioContext.currentTime);
            oscillator.frequency.exponentialRampToValueAtTime(400, audioContext.currentTime + 0.1);
            
            gainNode.gain.setValueAtTime(0.1, audioContext.currentTime);
            gainNode.gain.exponentialRampToValueAtTime(0.001, audioContext.currentTime + 0.1);
            
            oscillator.start(audioContext.currentTime);
            oscillator.stop(audioContext.currentTime + 0.1);
        } catch (error) {
            // Audio not supported, ignore silently
        }
    }

    // Restore user preferences
    restorePreferences() {
        const savedViewMode = localStorage.getItem('flashcards-view-mode');
        if (savedViewMode && savedViewMode !== this.viewMode) {
            this.toggleViewMode();
        }
    }
}

// Global functions for HTML onclick handlers
function flipCard(element) {
    if (window.resultsPage) {
        window.resultsPage.flipCard(element);
    }
}

function toggleViewMode() {
    if (window.resultsPage) {
        window.resultsPage.toggleViewMode();
    }
}

function copyToClipboard() {
    if (window.resultsPage) {
        window.resultsPage.copyAllToClipboard();
    }
}

function copyCard(index) {
    if (window.resultsPage) {
        window.resultsPage.copyCard(index);
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.resultsPage = new ResultsPage();
    window.resultsPage.restorePreferences();
    
    // Add keyboard shortcut hints
    console.log('Keyboard shortcuts:');
    console.log('Space: Flip random card (grid view)');
    console.log('Arrow keys: Navigate cards');
    console.log('V: Toggle view mode');
    console.log('Ctrl+Shift+C: Copy all flashcards');
});

// Add notification styles
const notificationCSS = `
    .notification-content {
        display: flex;
        align-items: center;
        gap: 0.75rem;
    }
    
    .notification-close {
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
    
    .notification-close:hover {
        background-color: rgba(255, 255, 255, 0.2);
    }
    
    .flashcard {
        outline: none;
        border: 2px solid transparent;
        transition: all 0.3s ease;
    }
    
    .flashcard:focus {
        border-color: var(--primary-purple);
        box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.2);
    }
    
    .flashcard-item {
        outline: none;
        transition: all 0.3s ease;
    }
    
    .flashcard-item:focus {
        outline: 2px solid var(--primary-purple);
        outline-offset: 2px;
    }
`;

const notificationStyleSheet = document.createElement('style');
notificationStyleSheet.textContent = notificationCSS;
document.head.appendChild(notificationStyleSheet);
