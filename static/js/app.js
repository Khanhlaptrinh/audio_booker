class AudioBookApp {
    constructor() {
        this.socket = null;
        this.currentSession = null;
        this.isPlaying = false;
        this.currentPage = 0;
        this.totalPages = 0;
        this.audioPlayer = null;
        
        this.initializeElements();
        this.setupEventListeners();
        this.initializeSocket();
    }
    
    initializeElements() {
        this.uploadArea = document.getElementById('upload-area');
        this.fileInput = document.getElementById('file-input');
        this.uploadSection = document.getElementById('upload-section');
        this.bookSection = document.getElementById('book-section');
        this.loading = document.getElementById('loading');
        
        this.bookTitle = document.getElementById('book-title');
        this.bookProgress = document.getElementById('book-progress');
        this.playBtn = document.getElementById('play-btn');
        this.pauseBtn = document.getElementById('pause-btn');
        this.stopBtn = document.getElementById('stop-btn');
        this.homeBtn = document.getElementById('home-btn');
        this.dialectLiveInputs = document.querySelectorAll('input[name="dialect-live"]');
        
        this.leftPage = document.getElementById('left-page');
        this.rightPage = document.getElementById('right-page');
        this.leftText = document.getElementById('left-text');
        this.rightText = document.getElementById('right-text');
        this.book = document.getElementById('book');
        
        this.audioPlayer = document.getElementById('audio-player');
        this.pendingPageData = null;
    }
    
    setupEventListeners() {
        // File upload
        this.uploadArea.addEventListener('click', () => this.fileInput.click());
        this.fileInput.addEventListener('change', (e) => this.handleFileSelect(e));
        
        // Drag and drop
        this.uploadArea.addEventListener('dragover', (e) => this.handleDragOver(e));
        this.uploadArea.addEventListener('dragleave', (e) => this.handleDragLeave(e));
        this.uploadArea.addEventListener('drop', (e) => this.handleDrop(e));
        
        // Control buttons
        this.playBtn.addEventListener('click', () => this.startReading());
        this.pauseBtn.addEventListener('click', () => this.pauseReading());
        this.stopBtn.addEventListener('click', () => this.stopReading());
        this.homeBtn.addEventListener('click', () => this.goHome());
        this.dialectLiveInputs.forEach((el) => {
            el.addEventListener('change', () => this.changeDialect(el.value));
        });
        
        // Audio events
        this.audioPlayer.addEventListener('ended', () => this.onAudioEnded());
        this.audioPlayer.addEventListener('error', (e) => this.onAudioError(e));
        this.audioPlayer.addEventListener('canplay', () => this.onAudioCanPlay());
    }

    changeDialect(dialect) {
        if (!this.currentSession) return;
        // Notify server to apply new dialect for next pages
        this.socket.emit('change_dialect', {
            session_id: this.currentSession,
            dialect
        });
        this.showMessage(`Đã chuyển giọng: ${dialect}`, 'success');
    }
    
    initializeSocket() {
        this.socket = io();
        
        this.socket.on('connect', () => {
            console.log('Connected to server');
        });
        
        this.socket.on('new_page', (data) => {
            this.handleNewPage(data);
        });
        
        this.socket.on('error', (data) => {
            this.showError(data.message);
        });
        
        this.socket.on('disconnect', () => {
            console.log('Disconnected from server');
        });
    }
    
    handleDragOver(e) {
        e.preventDefault();
        this.uploadArea.classList.add('dragover');
    }
    
    handleDragLeave(e) {
        e.preventDefault();
        this.uploadArea.classList.remove('dragover');
    }
    
    handleDrop(e) {
        e.preventDefault();
        this.uploadArea.classList.remove('dragover');
        
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            this.fileInput.files = files;
            this.handleFileSelect({ target: { files: files } });
        }
    }
    
    handleFileSelect(e) {
        const file = e.target.files[0];
        if (!file) return;
        
        const dialect = document.querySelector('input[name="dialect"]:checked').value;
        this.uploadFile(file, dialect);
    }
    
    async uploadFile(file, dialect) {
        this.showLoading(true);
        
        const formData = new FormData();
        formData.append('file', file);
        formData.append('dialect', dialect);
        
        try {
            const response = await fetch('/upload', {
                method: 'POST',
                body: formData
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.currentSession = result.session_id;
                this.totalPages = result.total_pages;
                this.bookTitle.textContent = result.filename;
                
                // Join socket room
                this.socket.emit('join_session', { session_id: this.currentSession });
                
                this.showBookSection();
                this.showMessage('File uploaded successfully!', 'success');
            } else {
                this.showError(result.error);
            }
        } catch (error) {
            this.showError('Upload failed: ' + error.message);
        } finally {
            this.showLoading(false);
        }
    }
    
    startReading() {
        if (!this.currentSession) return;
        
        this.isPlaying = true;
        this.playBtn.style.display = 'none';
        this.pauseBtn.style.display = 'inline-block';
        
        // Start reading from server
        fetch(`/start_reading/${this.currentSession}`)
            .then(response => response.json())
            .then(result => {
                if (!result.success) {
                    this.showError(result.message);
                }
            })
            .catch(error => {
                this.showError('Failed to start reading: ' + error.message);
            });
    }
    
    pauseReading() {
        this.isPlaying = false;
        this.audioPlayer.pause();
        this.playBtn.style.display = 'inline-block';
        this.pauseBtn.style.display = 'none';
    }
    
    stopReading() {
        this.isPlaying = false;
        this.audioPlayer.pause();
        this.audioPlayer.currentTime = 0;
        this.playBtn.style.display = 'inline-block';
        this.pauseBtn.style.display = 'none';
        this.currentPage = 0;
        this.updateProgress();
    }

    goHome() {
        // Stop audio and leave session
        this.stopReading();
        if (this.currentSession) {
            try {
                this.socket.emit('leave_session', { session_id: this.currentSession });
                fetch(`/cancel/${this.currentSession}`).catch(() => {});
            } catch (_) {}
        }
        this.currentSession = null;
        // Reset UI
        this.bookSection.style.display = 'none';
        this.uploadSection.style.display = 'block';
        // Clear texts
        this.leftText.textContent = 'Nội dung trang trước...';
        this.rightText.textContent = 'Nội dung trang hiện tại...';
        this.bookTitle.textContent = 'Tên Truyện';
        this.bookProgress.textContent = 'Trang 1 / 1';
    }
    
    handleNewPage(data) {
        console.log('New page received:', data);
        // Defer UI update until audio can play to keep text strictly in sync
        this.pendingPageData = data;
        this.audioPlayer.src = data.audio_url;
        this.audioPlayer.load();
    }
    
    animatePageFlip() {
        this.book.classList.add('flipping');
        
        setTimeout(() => {
            // Move current content to left page
            this.leftText.textContent = this.rightText.textContent;
            
            // Reset animation
            this.book.classList.remove('flipping');
        }, 300);
    }
    
    onAudioEnded() {
        console.log('Audio ended');
        // Flip page and request the next page from server
        this.animatePageFlip();
        if (this.currentSession != null) {
            this.socket.emit('page_finished', {
                session_id: this.currentSession,
                page_number: this.currentPage
            });
        }
    }

    onAudioCanPlay() {
        // Apply pending page text exactly when audio is ready to start
        if (!this.pendingPageData) return;
        const data = this.pendingPageData;
        this.pendingPageData = null;
        // Update page content and progress now
        this.rightText.textContent = data.text;
        this.currentPage = data.page_number;
        this.updateProgress();
        // Start playback
        if (this.isPlaying) {
            this.audioPlayer.play().catch(error => {
                console.error('Error playing audio:', error);
                this.showError('Error playing audio: ' + error.message);
            });
        }
    }
    
    onAudioError(e) {
        console.error('Audio error:', e);
        this.showError('Error playing audio');
    }
    
    updateProgress() {
        this.bookProgress.textContent = `Trang ${this.currentPage + 1} / ${this.totalPages}`;
    }
    
    showBookSection() {
        this.uploadSection.style.display = 'none';
        this.bookSection.style.display = 'block';
    }
    
    showLoading(show) {
        this.loading.style.display = show ? 'block' : 'none';
    }
    
    showMessage(message, type = 'success') {
        // Remove existing messages
        const existingMessages = document.querySelectorAll('.message');
        existingMessages.forEach(msg => msg.remove());
        
        // Create new message
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}`;
        messageDiv.textContent = message;
        
        // Insert at top of container
        const container = document.querySelector('.container');
        container.insertBefore(messageDiv, container.firstChild);
        
        // Auto remove after 5 seconds
        setTimeout(() => {
            messageDiv.remove();
        }, 5000);
    }
    
    showError(message) {
        this.showMessage(message, 'error');
    }
}

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new AudioBookApp();
});
