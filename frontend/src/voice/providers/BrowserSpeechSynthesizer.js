/**
 * Synthesizer provider backed by window.speechSynthesis. Replaceable.
 * speak() resolves when speech ends, errors, is cancelled, or a safety timeout
 * elapses (some browsers never fire `end`). It never rejects.
 */
export class BrowserSpeechSynthesizer {
  constructor({ lang = 'en-US', rate = 1, pitch = 1, globalObj = globalThis } = {}) {
    this._synth = globalObj && globalObj.speechSynthesis;
    this._Utterance = globalObj && globalObj.SpeechSynthesisUtterance;
    this.lang = lang;
    this.rate = rate;
    this.pitch = pitch;
    this._pending = null;
  }

  isSupported() {
    return !!(this._synth && typeof this._Utterance === 'function');
  }

  _pickVoice() {
    try {
      const voices = this._synth.getVoices() || [];
      const english = voices.filter((v) => (v.lang || '').toLowerCase().startsWith('en'));
      return (
        english.find((v) => (v.lang || '').toLowerCase() === this.lang.toLowerCase() && v.default) ||
        english.find((v) => (v.lang || '').toLowerCase() === this.lang.toLowerCase()) ||
        english[0] ||
        null
      );
    } catch (_) {
      return null;
    }
  }

  speak(text) {
    if (!this.isSupported() || !text) return Promise.resolve();
    this.cancel();
    return new Promise((resolve) => {
      const utterance = new this._Utterance(text);
      utterance.lang = this.lang;
      utterance.rate = this.rate;
      utterance.pitch = this.pitch;
      const voice = this._pickVoice();
      if (voice) utterance.voice = voice;

      let done = false;
      let timer = null;
      const entry = { finish: null, utterance }; // keeps a reference (avoids GC-cancelled speech in some browsers)
      const finish = () => {
        if (done) return;
        done = true;
        clearTimeout(timer);
        utterance.onend = null;
        utterance.onerror = null;
        if (this._pending === entry) this._pending = null;
        resolve();
      };
      entry.finish = finish;
      this._pending = entry;
      utterance.onend = finish;
      utterance.onerror = finish;
      timer = setTimeout(finish, Math.max(4000, text.length * 120));
      try {
        this._synth.speak(utterance);
      } catch (_) {
        finish();
      }
    });
  }

  cancel() {
    const pending = this._pending;
    this._pending = null;
    try {
      if (this._synth) this._synth.cancel();
    } catch (_) { /* ignore */ }
    if (pending) pending.finish();
  }
}
