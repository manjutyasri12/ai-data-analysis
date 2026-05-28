// VisualCogn - Accessible Learning Platform
// WCAG 2.1 AA Compliant

document.addEventListener('DOMContentLoaded', () => {
  // ====== CONFIGURATION & STATE ======
  const state = {
    currentFile: null,
    currentAudio: null,
    speechRate: 1.0,
    isSpeaking: false,
    fontSizeLevel: 0, // 0 = normal, 1 = large, 2 = xlarge
    darkMode: localStorage.getItem('visualcogn-dark-mode') === 'true',
    quietMode: localStorage.getItem('visualcogn-quiet-mode') === 'true',
  };

  // ====== DOM ELEMENTS ======
  const elements = {
    // Announcement/status
    srAnnouncement: document.getElementById('screen-reader-announcement'),
    siteGreeting: document.getElementById('site-greeting'),
    fileStatus: document.getElementById('file-status'),
    progressIndicator: document.getElementById('progress-indicator'),

    // File inputs
    fileInput: document.getElementById('file-input'),
    audioInput: document.getElementById('audio-input'),

    // Buttons
    uploadBtn: document.getElementById('upload-btn'),
    audioUploadBtn: document.getElementById('audio-upload-btn'),
    extractBtn: document.getElementById('extract-btn'),
    summaryBtn: document.getElementById('summary-btn'),
    playTtsBtn: document.getElementById('play-tts-btn'),
    stopTtsBtn: document.getElementById('stop-tts-btn'),
    downloadMp3Btn: document.getElementById('download-mp3-btn'),
    readExtractedBtn: document.getElementById('read-extracted-btn'),
    speedIncrBtn: document.getElementById('speed-incr'),
    speedDecrBtn: document.getElementById('speed-decr'),

    // Settings buttons
    fontSizeIncreaseBtn: document.getElementById('font-size-increase'),
    fontSizeDecreaseBtn: document.getElementById('font-size-decrease'),
    toggleDarkModeBtn: document.getElementById('toggle-dark-mode'),
    toggleQuietModeBtn: document.getElementById('toggle-quiet-mode'),
    showHelpBtn: document.getElementById('show-help'),

    // Text areas and output
    extractedText: document.getElementById('extracted-text'),
    imageInfo: document.getElementById('image-info'),
    summaryDiv: document.getElementById('summary'),
    brailleSection: document.getElementById('braille-section'),
    recognizedText: document.getElementById('recognized-text'),
    brailleDiv: document.getElementById('braille'),

    // Other
    speedDisplay: document.getElementById('speed-display'),
    helpDialog: document.getElementById('help-dialog'),
    closeHelpBtn: document.getElementById('close-help'),
  };

  // ====== ACCESSIBILITY: SCREEN READER & SPEECH ======
  const speak = (text, priority = 'polite') => {
    // Announce to screen reader
    if (elements.srAnnouncement) {
      elements.srAnnouncement.setAttribute('aria-live', priority);
      elements.srAnnouncement.textContent = text;
    }

    // Also use Web Speech API for audio announcement
    if (state.quietMode) return; // Skip speech in quiet mode
    try {
      speechSynthesis.cancel();
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.rate = state.speechRate;
      utterance.lang = 'en-US';
      speechSynthesis.speak(utterance);
    } catch (e) {
      console.warn('Speech synthesis not available:', e);
    }
  };

  // Announce site name and greeting on page load
  const announcePageLoad = () => {
    const greeting = 'Welcome to VisualCogn. A website for accessible learning and document processing. Press H for keyboard shortcuts.';
    speak(greeting);
  };

  // Display status messages
  const showStatus = (message, type = 'info') => {
    if (!elements.fileStatus) return;
    elements.fileStatus.textContent = message;
    elements.fileStatus.className = `status-message show ${type}`;
    speak(message);
  };

  // Show progress
  const showProgress = (message) => {
    if (!elements.progressIndicator) return;
    elements.progressIndicator.textContent = message;
    elements.progressIndicator.classList.add('show');
  };

  const hideProgress = () => {
    if (elements.progressIndicator) {
      elements.progressIndicator.classList.remove('show');
    }
  };

  // ====== FONT SIZE CONTROL ======
  const updateFontSize = () => {
    document.body.classList.remove('text-scale-large', 'text-scale-xlarge');
    if (state.fontSizeLevel === 1) {
      document.body.classList.add('text-scale-large');
      speak('Font size increased to 112 percent');
    } else if (state.fontSizeLevel === 2) {
      document.body.classList.add('text-scale-xlarge');
      speak('Font size increased to 125 percent');
    } else {
      state.fontSizeLevel = 0;
      speak('Font size reset to normal');
    }
    localStorage.setItem('visualcogn-font-size', state.fontSizeLevel);
  };

  elements.fontSizeIncreaseBtn?.addEventListener('click', () => {
    state.fontSizeLevel = (state.fontSizeLevel + 1) % 3;
    updateFontSize();
  });

  elements.fontSizeDecreaseBtn?.addEventListener('click', () => {
    state.fontSizeLevel = (state.fontSizeLevel - 1 + 3) % 3;
    updateFontSize();
  });

  // ====== DARK MODE & QUIET MODE ======
  const applyTheme = () => {
    if (state.darkMode) {
      document.body.classList.add('dark-mode');
      speak('Dark mode enabled');
    } else {
      document.body.classList.remove('dark-mode');
      speak('Light mode enabled');
    }
  };

  const applyQuietMode = () => {
    if (state.quietMode) {
      document.body.classList.add('quiet-mode');
      speak('Quiet mode enabled. Animations and sounds reduced.');
    } else {
      document.body.classList.remove('quiet-mode');
      speak('Quiet mode disabled.');
    }
  };

  elements.toggleDarkModeBtn?.addEventListener('click', () => {
    state.darkMode = !state.darkMode;
    localStorage.setItem('visualcogn-dark-mode', state.darkMode);
    applyTheme();
  });

  elements.toggleQuietModeBtn?.addEventListener('click', () => {
    state.quietMode = !state.quietMode;
    localStorage.setItem('visualcogn-quiet-mode', state.quietMode);
    applyQuietMode();
  });

  // ====== HELP DIALOG ======
  elements.showHelpBtn?.addEventListener('click', () => {
    elements.helpDialog?.showModal?.();
    speak('Keyboard shortcuts dialog opened');
    elements.closeHelpBtn?.focus();
  });

  elements.closeHelpBtn?.addEventListener('click', () => {
    elements.helpDialog?.close?.();
    speak('Help dialog closed');
    elements.showHelpBtn?.focus();
  });

  elements.helpDialog?.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      elements.helpDialog.close();
    }
  });

  // ====== SPEED CONTROL ======
  const setSpeed = (newRate) => {
    state.speechRate = Math.min(2.0, Math.max(0.5, Math.round(newRate * 2) / 2));
    elements.speedDisplay.textContent = state.speechRate.toFixed(1) + 'x';
    speak(`Speech speed set to ${state.speechRate} times`);
  };

  elements.speedIncrBtn?.addEventListener('click', () => {
    setSpeed(state.speechRate + 0.5);
  });

  elements.speedDecrBtn?.addEventListener('click', () => {
    setSpeed(state.speechRate - 0.5);
  });

  setSpeed(1.0); // Initialize

  // ====== FILE UPLOAD ======
  elements.uploadBtn?.addEventListener('click', () => {
    elements.fileInput?.click?.();
  });

  elements.fileInput?.addEventListener('change', async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    state.currentFile = file;
    const filename = file.name;
    showStatus(`File selected: ${filename}. Press E to extract text.`, 'success');
  });

  // ====== TEXT EXTRACTION ======
  elements.extractBtn?.addEventListener('click', async () => {
    if (!state.currentFile) {
      showStatus('Please upload a file first by pressing U or clicking the Upload button.', 'error');
      return;
    }

    showProgress('Extracting text from your file. Please wait...');
    speak('Uploading and extracting text. This may take a moment.');

    try {
      const formData = new FormData();
      formData.append('file', state.currentFile);

      const response = await fetch('/api/upload', {
        method: 'POST',
        body: formData,
      });

      // Check if response is ok
      if (!response.ok) {
        throw new Error(`Server error: ${response.status}`);
      }

      // Check if response has content
      const contentType = response.headers.get('content-type');
      if (!contentType || !contentType.includes('application/json')) {
        throw new Error('Server returned invalid response format');
      }

      const data = await response.json();

      if (data.error) {
        throw new Error(data.error);
      }

      // Update extracted text
      elements.extractedText.value = data.text || '';
      elements.extractedText.setAttribute('aria-label', `Extracted text: ${(data.text || '').substring(0, 100)}...`);

      // Show image info if available
      if (data.image_info) {
        elements.imageInfo.textContent = data.image_info;
        speak(data.image_info);
      }

      hideProgress();
      showStatus('Text extraction complete. You can now summarize or read aloud.', 'success');
      elements.extractedText.focus();
    } catch (error) {
      hideProgress();
      console.error('Extraction error:', error);
      showStatus(`Error: ${error.message}`, 'error');
      speak(`Extraction failed: ${error.message}`);
    }
  });

  // ====== TEXT SUMMARIZATION ======
  elements.summaryBtn?.addEventListener('click', async () => {
    const text = elements.extractedText.value?.trim();

    if (!text) {
      showStatus('No text to summarize. Please extract text first.', 'error');
      return;
    }

    showProgress('Creating a simple summary for easier understanding. Please wait...');
    speak('Generating summary');

    try {
      const response = await fetch('/api/summarize', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text, max_sentences: 3 }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || 'Summarization failed');
      }

      elements.summaryDiv.textContent = data.summary || '';
      elements.summaryDiv.setAttribute('aria-label', `Summary: ${(data.summary || '').substring(0, 100)}...`);

      hideProgress();
      showStatus('Summary created. This is a shorter, easier to read version.', 'success');
      speak('Summary ready. ' + (data.summary || ''));
      elements.summaryDiv.focus();
    } catch (error) {
      hideProgress();
      showStatus(`Error: ${error.message}`, 'error');
      speak(`Summarization failed: ${error.message}`);
    }
  });

  // ====== TEXT TO SPEECH ======
  elements.playTtsBtn?.addEventListener('click', () => {
    const text = elements.extractedText.value?.trim() || elements.summaryDiv.textContent?.trim();

    if (!text) {
      showStatus('No text available to read. Please extract text first.', 'error');
      return;
    }

    showStatus('Starting to read the text aloud...', 'info');
    state.isSpeaking = true;
    elements.stopTtsBtn?.removeAttribute('disabled');

    try {
      speechSynthesis.cancel();
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.rate = state.speechRate;
      utterance.lang = 'en-US';

      utterance.onend = () => {
        state.isSpeaking = false;
        elements.stopTtsBtn?.setAttribute('disabled', 'true');
        showStatus('Reading finished.', 'success');
      };

      utterance.onerror = (e) => {
        state.isSpeaking = false;
        elements.stopTtsBtn?.setAttribute('disabled', 'true');
        showStatus(`Reading error: ${e.error}`, 'error');
      };

      speechSynthesis.speak(utterance);
    } catch (e) {
      showStatus(`Speech synthesis error: ${e.message}`, 'error');
      state.isSpeaking = false;
      elements.stopTtsBtn?.setAttribute('disabled', 'true');
    }
  });

  elements.stopTtsBtn?.addEventListener('click', () => {
    speechSynthesis.cancel();
    state.isSpeaking = false;
    elements.stopTtsBtn?.setAttribute('disabled', 'true');
    showStatus('Reading stopped.', 'info');
  });

  // ====== MP3 DOWNLOAD ======
  elements.downloadMp3Btn?.addEventListener('click', async () => {
    const text = elements.extractedText.value?.trim() || elements.summaryDiv.textContent?.trim();

    if (!text) {
      showStatus('No text available. Please extract text first.', 'error');
      return;
    }

    // Disable the button and show generating state
    const downloadBtn = elements.downloadMp3Btn;
    const originalBtnText = downloadBtn.textContent;
    try {
      downloadBtn.setAttribute('disabled', 'true');
      downloadBtn.setAttribute('aria-busy', 'true');
      downloadBtn.textContent = '⏳ Generating file...';

      showProgress('Generating MP3 file from your text. This may take a moment...');
      showStatus('Generating MP3 file...', 'info');
      speak('Generating the audio file. This may take a moment.');

      const response = await fetch('/api/tts', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text, speed: state.speechRate }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || 'MP3 generation failed');
      }

      if (data.mp3_url) {
        // Fetch the mp3 as a blob to ensure download works across browsers
        const mp3Response = await fetch(data.mp3_url);
        if (!mp3Response.ok) throw new Error('Failed to fetch generated MP3');

        const blob = await mp3Response.blob();
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = data.filename || 'visualcogn-audio.mp3';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        window.URL.revokeObjectURL(url);

        hideProgress();
        showStatus('MP3 generated and downloaded successfully!', 'success');
        speak('MP3 file generated and downloaded.');
      } else {
        throw new Error('No MP3 URL returned');
      }
    } catch (error) {
      hideProgress();
      showStatus(`Download failed: ${error.message}`, 'error');
      speak(`MP3 generation failed: ${error.message}`);
    } finally {
      // Restore button state
      try {
        elements.downloadMp3Btn.removeAttribute('disabled');
        elements.downloadMp3Btn.removeAttribute('aria-busy');
        elements.downloadMp3Btn.textContent = originalBtnText;
      } catch (e) {
        // ignore
      }
    }
  });

  // ====== READ EXTRACTED TEXT ======
  elements.readExtractedBtn?.addEventListener('click', () => {
    const text = elements.extractedText.value?.trim();
    if (!text) {
      showStatus('No extracted text to read. Please extract first.', 'error');
      return;
    }

    showStatus('Reading extracted text aloud...', 'info');
    speak('Reading extracted text.');

    try {
      speechSynthesis.cancel();
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.rate = state.speechRate;
      utterance.lang = 'en-US';

      utterance.onend = () => {
        showStatus('Finished reading extracted text.', 'success');
      };

      utterance.onerror = (e) => {
        showStatus(`Reading error: ${e.error || e.message}`, 'error');
      };

      speechSynthesis.speak(utterance);
    } catch (e) {
      showStatus(`Speech synthesis error: ${e.message}`, 'error');
    }
  });

  // ====== SPEECH TO BRAILLE ======
  elements.audioUploadBtn?.addEventListener('click', () => {
    elements.audioInput?.click?.();
  });

  elements.audioInput?.addEventListener('change', async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    state.currentAudio = file;
    showProgress('Uploading audio for speech to Braille conversion. Please wait...');
    speak('Uploading your audio for speech to Braille conversion');

    try {
      const formData = new FormData();
      formData.append('audio', file);

      const response = await fetch('/api/speech-to-braille', {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || 'Speech to Braille conversion failed');
      }

      // Display results
      elements.brailleSection.style.display = 'block';
      elements.recognizedText.textContent = data.text || '';
      elements.brailleDiv.textContent = data.braille || '';

      elements.brailleSection.setAttribute('aria-label', `Recognized text: ${data.text}. Braille: ${data.braille}`);

      hideProgress();
      showStatus('Speech converted to Braille successfully!', 'success');
      speak(`Recognized text: ${data.text}. Braille conversion complete.`);
      elements.brailleSection.focus();
    } catch (error) {
      hideProgress();
      showStatus(`Conversion failed: ${error.message}`, 'error');
      speak(`Speech to Braille failed: ${error.message}`);
    }
  });

  // ====== KEYBOARD SHORTCUTS ======
  const shortcutActions = {
    'u': () => elements.uploadBtn?.click?.(),
    'e': () => elements.extractBtn?.click?.(),
    's': () => elements.summaryBtn?.click?.(),
    'r': () => elements.playTtsBtn?.click?.(),
    'd': () => elements.downloadMp3Btn?.click?.(),
    'h': () => elements.showHelpBtn?.click?.(),
    'q': () => elements.toggleQuietModeBtn?.click?.(),
    '+': () => elements.fontSizeIncreaseBtn?.click?.(),
    '-': () => elements.fontSizeDecreaseBtn?.click?.(),
  };

  document.addEventListener('keydown', (e) => {
    const key = e.key.toLowerCase();

    // Skip if focused on input/textarea (to allow natural typing)
    if (['INPUT', 'TEXTAREA'].includes(e.target.tagName)) {
      return;
    }

    // Check for shortcuts
    if (shortcutActions[key]) {
      e.preventDefault();
      shortcutActions[key]();
    }

    // Help message for first-time users (announce shortcut on keypress)
    if (key === 'h') {
      speak('Keyboard shortcuts dialog opened. Use arrow keys to navigate, Enter to activate buttons.');
    }
  });

  // ====== KEYBOARD NAVIGATION SETUP ======
  const focusableElements = document.querySelectorAll(
    'button, [href], input, textarea, [tabindex]:not([tabindex="-1"])'
  );

  // Ensure all buttons are keyboard accessible
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && e.target.tagName === 'BUTTON') {
      e.target.click();
    }
  });

  // ====== INITIALIZATION ======
  // Load saved preferences
  if (state.darkMode) applyTheme();
  if (state.quietMode) applyQuietMode();
  const savedFontSize = localStorage.getItem('visualcogn-font-size');
  if (savedFontSize) {
    state.fontSizeLevel = parseInt(savedFontSize);
    updateFontSize();
  }

  // Announce page load
  announcePageLoad();

  // Make state globally accessible for debugging
  window.visualCognState = state;
});

