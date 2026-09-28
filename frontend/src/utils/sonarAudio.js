/**
 * Sonar Sentry Audio Acoustic Synthesizer (Web Audio API)
 * Simulates active naval sonar chirps and target echo pings.
 */

class SonarAudioEngine {
  constructor() {
    this.ctx = null;
    this.muted = false;
  }

  init() {
    if (!this.ctx && typeof window !== 'undefined') {
      const AudioContext = window.AudioContext || window.webkitAudioContext;
      if (AudioContext) {
        this.ctx = new AudioContext();
      }
    }
  }

  playPing(frequency = 1040, duration = 0.35) {
    if (this.muted) return;
    try {
      this.init();
      if (!this.ctx) return;
      if (this.ctx.state === 'suspended') {
        this.ctx.resume();
      }

      const now = this.ctx.currentTime;
      const osc = this.ctx.createOscillator();
      const gain = this.ctx.createGain();

      // Sine wave with slight frequency sweep (acoustic chirp)
      osc.type = 'sine';
      osc.frequency.setValueAtTime(frequency, now);
      osc.frequency.exponentialRampToValueAtTime(frequency * 0.75, now + duration);

      // Attack & exponential decay
      gain.gain.setValueAtTime(0.01, now);
      gain.gain.linearRampToValueAtTime(0.18, now + 0.02);
      gain.gain.exponentialRampToValueAtTime(0.0001, now + duration);

      osc.connect(gain);
      gain.connect(this.ctx.destination);

      osc.start(now);
      osc.stop(now + duration);
    } catch (e) {
      // Ignore autoplay restrictions
    }
  }

  playDetectionAlert() {
    // Dual high-frequency alert chirp
    this.playPing(1420, 0.2);
    setTimeout(() => {
      this.playPing(1860, 0.3);
    }, 120);
  }

  toggleMute() {
    this.muted = !this.muted;
    return this.muted;
  }
}

export const sonarAudio = new SonarAudioEngine();
