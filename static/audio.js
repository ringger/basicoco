class CoCoAudio {
    constructor() {
        this.audioContext = null;
        this.initialized = false;
        // Notes are queued back to back on the AudioContext timeline, so
        // several SOUNDs arriving in one output batch (a melody in a FOR
        // loop) play in sequence instead of cutting each other off.
        this.nextStartTime = 0;
        this.scheduled = new Set();
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

        try {
            // Create oscillator for the tone
            const oscillator = this.audioContext.createOscillator();
            const gainNode = this.audioContext.createGain();

            // Connect oscillator -> gain -> destination
            oscillator.connect(gainNode);
            gainNode.connect(this.audioContext.destination);

            // Start after any notes already queued
            const start = Math.max(this.audioContext.currentTime, this.nextStartTime);
            const durationInSeconds = Math.max(duration / 60, 0.03); // CoCo duration is in 60ths of a second
            this.nextStartTime = start + durationInSeconds;

            // Configure the oscillator
            oscillator.type = 'square'; // TRS-80 used square waves
            oscillator.frequency.setValueAtTime(frequency, start);

            // Configure the gain envelope
            gainNode.gain.setValueAtTime(0, start);
            gainNode.gain.linearRampToValueAtTime(0.1, start + 0.01); // Quick attack
            gainNode.gain.exponentialRampToValueAtTime(0.01, start + durationInSeconds - 0.01); // Decay
            gainNode.gain.linearRampToValueAtTime(0, start + durationInSeconds); // Release

            // Start and schedule stop
            oscillator.start(start);
            oscillator.stop(start + durationInSeconds);

            this.scheduled.add(oscillator);
            oscillator.onended = () => this.scheduled.delete(oscillator);

        } catch (error) {
            console.error('Error playing sound:', error);
        }
    }

    stopSound() {
        // Ctrl+C: silence the current note and everything still queued
        for (const oscillator of this.scheduled) {
            try {
                oscillator.stop();
            } catch (error) {
                // already stopped
            }
        }
        this.scheduled.clear();
        this.nextStartTime = 0;
    }
}
