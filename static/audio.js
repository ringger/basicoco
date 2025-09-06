class CoCoAudio {
    constructor() {
        this.audioContext = null;
        this.currentOscillator = null;
        this.initialized = false;
    }
    
    async initialize() {
        if (this.initialized) return;
        
        try {
            this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
            this.initialized = true;
            console.log('Audio system initialized');
        } catch (error) {
            console.error('Failed to initialize audio:', error);
        }
    }
    
    async playSound(frequency, duration) {
        if (!this.initialized) {
            await this.initialize();
        }
        
        if (!this.audioContext) {
            console.warn('Audio not available');
            return;
        }
        
        // Stop any currently playing sound
        if (this.currentOscillator) {
            this.currentOscillator.stop();
            this.currentOscillator = null;
        }
        
        try {
            // Create oscillator for the tone
            const oscillator = this.audioContext.createOscillator();
            const gainNode = this.audioContext.createGain();
            
            // Connect oscillator -> gain -> destination
            oscillator.connect(gainNode);
            gainNode.connect(this.audioContext.destination);
            
            // Configure the oscillator
            oscillator.type = 'square'; // TRS-80 used square waves
            oscillator.frequency.setValueAtTime(frequency, this.audioContext.currentTime);
            
            // Configure the gain envelope
            const now = this.audioContext.currentTime;
            const durationInSeconds = duration / 60; // CoCo duration is in 60ths of a second
            
            gainNode.gain.setValueAtTime(0, now);
            gainNode.gain.linearRampToValueAtTime(0.1, now + 0.01); // Quick attack
            gainNode.gain.exponentialRampToValueAtTime(0.01, now + durationInSeconds - 0.01); // Decay
            gainNode.gain.linearRampToValueAtTime(0, now + durationInSeconds); // Release
            
            // Start and schedule stop
            oscillator.start(now);
            oscillator.stop(now + durationInSeconds);
            
            this.currentOscillator = oscillator;
            
            // Clean up when finished
            oscillator.onended = () => {
                if (this.currentOscillator === oscillator) {
                    this.currentOscillator = null;
                }
            };
            
        } catch (error) {
            console.error('Error playing sound:', error);
        }
    }
    
    stopSound() {
        if (this.currentOscillator) {
            this.currentOscillator.stop();
            this.currentOscillator = null;
        }
    }
}