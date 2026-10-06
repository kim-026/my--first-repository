/**
 * Bingo Deluxe Audio System
 * Synthesized Web Audio API sound effects + Web Speech API voice caller.
 * 100% self-contained, no external audio files required!
 */

class SoundController {
  constructor() {
    this.audioCtx = null;
    this.isMuted = false;
    this.voiceEnabled = true;
    this.volume = 0.7;
    this.speechSynth = typeof window !== 'undefined' && 'speechSynthesis' in window ? window.speechSynthesis : null;
    this.selectedVoice = null;

    if (this.speechSynth) {
      // Pick best English voice if available
      const loadVoices = () => {
        const voices = this.speechSynth.getVoices();
        this.selectedVoice = voices.find(v => v.lang.startsWith('en') && (v.name.includes('Google') || v.name.includes('Natural') || v.name.includes('Samantha') || v.name.includes('David'))) 
          || voices.find(v => v.lang.startsWith('en')) 
          || voices[0];
      };
      loadVoices();
      if (this.speechSynth.onvoiceschanged !== undefined) {
        this.speechSynth.onvoiceschanged = loadVoices;
      }
    }
  }

  initAudio() {
    if (!this.audioCtx) {
      const AudioContext = window.AudioContext || window.webkitAudioContext;
      if (AudioContext) {
        this.audioCtx = new AudioContext();
      }
    }
    if (this.audioCtx && this.audioCtx.state === 'suspended') {
      this.audioCtx.resume();
    }
  }

  playPop() {
    if (this.isMuted) return;
    this.initAudio();
    if (!this.audioCtx) return;

    const t = this.audioCtx.currentTime;
    const osc = this.audioCtx.createOscillator();
    const gain = this.audioCtx.createGain();

    osc.type = 'sine';
    // Rapid pitch drop gives a juicy wooden/bubble "pop"
    osc.frequency.setValueAtTime(580, t);
    osc.frequency.exponentialRampToValueAtTime(140, t + 0.12);

    gain.gain.setValueAtTime(this.volume * 0.8, t);
    gain.gain.exponentialRampToValueAtTime(0.001, t + 0.12);

    osc.connect(gain);
    gain.connect(this.audioCtx.destination);

    osc.start(t);
    osc.stop(t + 0.12);
  }

  playDaub() {
    if (this.isMuted) return;
    this.initAudio();
    if (!this.audioCtx) return;

    const t = this.audioCtx.currentTime;
    
    // Thump oscillator
    const osc = this.audioCtx.createOscillator();
    const gain = this.audioCtx.createGain();

    osc.type = 'triangle';
    osc.frequency.setValueAtTime(220, t);
    osc.frequency.exponentialRampToValueAtTime(55, t + 0.09);

    gain.gain.setValueAtTime(this.volume * 0.9, t);
    gain.gain.exponentialRampToValueAtTime(0.01, t + 0.09);

    osc.connect(gain);
    gain.connect(this.audioCtx.destination);

    osc.start(t);
    osc.stop(t + 0.09);

    // High snap
    const snapOsc = this.audioCtx.createOscillator();
    const snapGain = this.audioCtx.createGain();
    snapOsc.type = 'sine';
    snapOsc.frequency.setValueAtTime(880, t);
    snapOsc.frequency.exponentialRampToValueAtTime(300, t + 0.04);
    snapGain.gain.setValueAtTime(this.volume * 0.3, t);
    snapGain.gain.exponentialRampToValueAtTime(0.001, t + 0.04);

    snapOsc.connect(snapGain);
    snapGain.connect(this.audioCtx.destination);
    snapOsc.start(t);
    snapOsc.stop(t + 0.04);
  }

  playHopperTumble() {
    if (this.isMuted) return;
    this.initAudio();
    if (!this.audioCtx) return;

    // Series of 3 quick rhythmic clatters
    const t0 = this.audioCtx.currentTime;
    [0, 0.06, 0.13, 0.2].forEach((offset, idx) => {
      const t = t0 + offset;
      const osc = this.audioCtx.createOscillator();
      const gain = this.audioCtx.createGain();

      osc.type = 'triangle';
      const baseFreq = 400 + (idx % 2 === 0 ? 150 : -80);
      osc.frequency.setValueAtTime(baseFreq, t);
      osc.frequency.exponentialRampToValueAtTime(100, t + 0.05);

      gain.gain.setValueAtTime(this.volume * 0.4, t);
      gain.gain.exponentialRampToValueAtTime(0.001, t + 0.05);

      osc.connect(gain);
      gain.connect(this.audioCtx.destination);

      osc.start(t);
      osc.stop(t + 0.05);
    });
  }

  playWinFanfare() {
    if (this.isMuted) return;
    this.initAudio();
    if (!this.audioCtx) return;

    const t = this.audioCtx.currentTime;
    // Major chord arpeggio celebration: C5, E5, G5, C6
    const notes = [
      { f: 523.25, time: 0.0, dur: 0.18 }, // C5
      { f: 659.25, time: 0.18, dur: 0.18 }, // E5
      { f: 783.99, time: 0.36, dur: 0.22 }, // G5
      { f: 1046.50, time: 0.58, dur: 0.8 }, // C6
      { f: 1318.51, time: 0.72, dur: 0.9 }  // E6 Harmony
    ];

    notes.forEach(n => {
      const osc = this.audioCtx.createOscillator();
      const gain = this.audioCtx.createGain();

      osc.type = 'sine';
      osc.frequency.setValueAtTime(n.f, t + n.time);

      gain.gain.setValueAtTime(this.volume * 0.7, t + n.time);
      gain.gain.exponentialRampToValueAtTime(0.001, t + n.time + n.dur);

      osc.connect(gain);
      gain.connect(this.audioCtx.destination);

      osc.start(t + n.time);
      osc.stop(t + n.time + n.dur);
    });
  }

  playError() {
    if (this.isMuted) return;
    this.initAudio();
    if (!this.audioCtx) return;

    const t = this.audioCtx.currentTime;
    const osc = this.audioCtx.createOscillator();
    const gain = this.audioCtx.createGain();

    osc.type = 'sawtooth';
    osc.frequency.setValueAtTime(140, t);
    osc.frequency.setValueAtTime(110, t + 0.12);

    gain.gain.setValueAtTime(this.volume * 0.5, t);
    gain.gain.exponentialRampToValueAtTime(0.001, t + 0.25);

    osc.connect(gain);
    gain.connect(this.audioCtx.destination);

    osc.start(t);
    osc.stop(t + 0.25);
  }

  playClick() {
    if (this.isMuted) return;
    this.initAudio();
    if (!this.audioCtx) return;

    const t = this.audioCtx.currentTime;
    const osc = this.audioCtx.createOscillator();
    const gain = this.audioCtx.createGain();

    osc.type = 'sine';
    osc.frequency.setValueAtTime(900, t);
    osc.frequency.exponentialRampToValueAtTime(200, t + 0.03);

    gain.gain.setValueAtTime(this.volume * 0.3, t);
    gain.gain.exponentialRampToValueAtTime(0.001, t + 0.03);

    osc.connect(gain);
    gain.connect(this.audioCtx.destination);

    osc.start(t);
    osc.stop(t + 0.03);
  }

  speakBall(ball) {
    if (!this.voiceEnabled || !this.speechSynth) return;

    try {
      this.speechSynth.cancel(); // cancel any lingering utterance
      const text = ball.nickname 
        ? `${ball.letter} ${ball.number}. ${ball.nickname}!` 
        : `${ball.letter} ${ball.number}`;

      const utterance = new SpeechSynthesisUtterance(text);
      if (this.selectedVoice) {
        utterance.voice = this.selectedVoice;
      }
      utterance.rate = 1.05;
      utterance.pitch = 1.05;
      utterance.volume = this.isMuted ? 0 : this.volume;
      this.speechSynth.speak(utterance);
    } catch (e) {
      console.warn("Speech synthesis error:", e);
    }
  }

  speakText(text) {
    if (!this.voiceEnabled || !this.speechSynth) return;
    try {
      this.speechSynth.cancel();
      const utterance = new SpeechSynthesisUtterance(text);
      if (this.selectedVoice) {
        utterance.voice = this.selectedVoice;
      }
      utterance.rate = 1.05;
      utterance.pitch = 1.1;
      utterance.volume = this.isMuted ? 0 : this.volume;
      this.speechSynth.speak(utterance);
    } catch (e) {
      console.warn("Speech synthesis error:", e);
    }
  }
}

if (typeof window !== 'undefined') {
  window.SoundController = SoundController;
}
