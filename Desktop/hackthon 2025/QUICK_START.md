# Quick Start Guide - VisualCogn

## 🚀 Installation & Setup (5 minutes)

### Step 1: Install Python Packages
```bash
pip install -r requirements.txt
```

### Step 2: Install Tesseract OCR
**Windows:**
- Download: https://github.com/UB-Mannheim/tesseract/wiki
- Run the installer
- Add to PATH (if not automatic): `C:\Program Files\Tesseract-OCR`

**macOS:**
```bash
brew install tesseract
```

**Linux:**
```bash
sudo apt-get install tesseract-ocr
```

### Step 3: Run the Application
```bash
cd "c:\Users\shreyash\Desktop\hackthon 2025"
python app.py
```

### Step 4: Open in Browser
- URL: `http://localhost:5000`
- You'll hear: *"Welcome to VisualCogn..."*

---

## ⌨️ Essential Keyboard Shortcuts

| Key | Action | When to Use |
|-----|--------|-----------|
| **U** | Upload file | Start here - upload PDF, image, or text |
| **E** | Extract text | Get text from your file |
| **S** | Summarize | Create simpler version of text |
| **R** | Read aloud | Hear the text |
| **D** | Download MP3 | Save as audio file |
| **H** | Help | See all shortcuts |
| **+** | Bigger text | Enlarge font |
| **-** | Smaller text | Reduce font |
| **Q** | Quiet mode | Reduce animations |

---

## 📋 Workflow Example

### Scenario: Visually Impaired Student
1. **Press U** → Select a PDF file
2. **Press E** → Extract text (wait for confirmation)
3. **Press R** → Hear it read aloud
4. **Press -** → Slow down reading
5. **Press D** → Download as MP3

### Scenario: Cognitive Student
1. **Press U** → Upload a long document
2. **Press E** → Extract the text
3. **Press S** → Get a simple summary
4. **Press R** → Listen to summary
5. **Press +** → Make text bigger

---

## 🎯 Supported File Types

✅ **PDF** - Documents with text  
✅ **Images** - PNG, JPG, BMP, TIFF, GIF (text extraction via OCR)  
✅ **Text** - TXT files  
✅ **Audio** - MP3, WAV, FLAC (for speech-to-Braille)

---

## 🔊 Features Explained

### Extract Text
- Reads content from your file
- Text appears in the gray box
- Works on PDFs, images, text files

### Summarize
- Makes long text shorter
- Picks the 3 most important sentences
- Keeps the meaning

### Read Aloud
- Speaks the text for you
- Use **-** button to slow down
- Use **+** button to speed up
- Range: 0.5x (very slow) to 2.0x (very fast)

### Download MP3
- Saves text as an audio file
- Download starts automatically
- Play it later on any device

### Speech-to-Braille
- Record your voice
- App converts to Braille format
- See both the text and Braille

---

## 🎨 Customize Your Experience

### 1. Font Size
- **Press +** to enlarge (2 levels)
- **Press -** to shrink
- Perfect for low vision users

### 2. Dark Mode
- **Press D** to toggle
- Reduces eye strain
- Keeps high contrast

### 3. Quiet Mode
- **Press Q** to toggle
- Removes animations
- Good for sensory sensitivities

### 4. Settings Saved
Your preferences are saved automatically!

---

## 🆘 Troubleshooting

### "Tesseract not found"
→ Install Tesseract OCR (see Step 2 above)

### "File didn't extract"
→ Try a different file  
→ Ensure it's under 50MB  
→ Check file is not corrupted

### "Can't read aloud"
→ Ensure text is extracted first  
→ Check speaker volume  
→ Try a shorter text passage

### "Speech recognition failed"
→ Check internet connection  
→ Try clearer audio  
→ Check microphone permissions

### "Can't hear announcements"
→ Enable sound on your computer  
→ Check volume is not muted  
→ Press H to test sound

---

## 📞 Getting Help

1. **In the app**: Press **H** for keyboard shortcuts
2. **On the page**: See the help button (❓) in the top right
3. **Check README.md**: Full documentation
4. **Browser console**: Press F12, check for error messages

---

## ✨ Tips & Tricks

### Tip 1: Use Keyboard Only
Everything works without a mouse!  
Tab through, Enter to activate

### Tip 2: Check Shortcuts Help
Press **H** anytime to see what keys do what

### Tip 3: Combine Features
- Extract text
- Summarize it
- Read summary aloud
- Download as MP3

### Tip 4: Screen Reader Friendly
Works with NVDA, JAWS, VoiceOver  
Announces everything automatically

### Tip 5: Mobile Friendly
Works on phones and tablets  
Everything adapts to screen size

---

## 🎓 For Students

### Using with Screen Reader
1. Enable NVDA or JAWS
2. Press H for shortcuts
3. Use arrow keys to navigate
4. All content announced automatically

### Using with Low Vision
1. Press + to enlarge text
2. Press D to enable dark mode
3. Use dark theme if available
4. System will announce everything

### Using with Cognitive Differences
1. Press Q for quiet mode (less animations)
2. Press S to summarize long texts
3. Use simple language in your documents
4. Step-by-step instructions provided

---

## ⚙️ System Requirements

- Internet connection (for speech & TTS)
- Modern browser (Chrome, Firefox, Safari, Edge)
- Python 3.7 or higher
- Tesseract OCR installed
- 1GB minimum RAM
- Speakers or headphones

---

## 📱 Browser Compatibility

| Browser | Status | Notes |
|---------|--------|-------|
| Chrome | ✅ Recommended | Best compatibility |
| Firefox | ✅ Fully supported | No issues |
| Safari | ✅ Fully supported | Works well |
| Edge | ✅ Fully supported | Chromium-based |

---

## 🔒 Privacy

- Files uploaded to app only (not sent anywhere)
- No personal data collected
- Only Google Speech & TTS services used
- Temporary files deleted after session

---

## 📚 Learn More

- **Full Documentation**: See README.md
- **Implementation Details**: See IMPLEMENTATION_SUMMARY.md
- **API Reference**: See README.md API section

---

**Welcome to VisualCogn!** 🎉  
Press **H** for help anytime!

Made by Decent Debuggers  
For accessible learning
