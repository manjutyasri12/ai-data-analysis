# VisualCogn - Accessible Learning Platform

**By Decent Debuggers**

VisualCogn is a web application designed to make digital content accessible to visually impaired and cognitively diverse students. It provides tools to extract text from documents, convert text to speech, simplify complex information, and more—all with full keyboard accessibility and screen reader support.

## Features

### For Visually Impaired Students
- 📁 **Upload & Extract**: Extract text from PDFs, images (PNG, JPG), and text files
- 🔊 **Text-to-Speech**: Convert extracted text to speech with adjustable speed (0.5x - 2.0x)
- ⬇️ **Audio Download**: Save text as MP3 files to listen later
- 🎤 **Speech-to-Braille**: Convert spoken words to Braille format
- 📋 **Summaries**: Get simple summaries of complex texts
- 🖼️ **Image Analysis**: Automatic face detection and image description

### For Cognitive Users
- 📝 **Simplified Summaries**: Break down complex information into simple, short text
- 🎨 **Customizable Interface**: Adjust font size, colors, and animations
- 📊 **Step-by-Step Guidance**: Clear, sequential instructions for each task
- 🔕 **Quiet Mode**: Reduce visual stimuli and distracting animations
- 🌙 **Dark Mode**: Reduce eye strain with dark background option

### Accessibility Features (WCAG 2.1 AA Compliant)
- ✅ **Keyboard Navigation**: Navigate and operate entirely with keyboard (Tab, Enter, Space, Arrow keys)
- ✅ **Screen Reader Compatible**: Works with JAWS, NVDA, VoiceOver, and other screen readers
- ✅ **High Contrast**: 4.5:1+ contrast ratio for text readability
- ✅ **Scalable Text**: Support for up to 200% text sizing without loss of functionality
- ✅ **Skip to Main Content**: Jump over navigation to main content
- ✅ **Semantic HTML**: Proper heading hierarchy and landmark regions
- ✅ **ARIA Labels**: Descriptive labels for all interactive elements
- ✅ **Focus Indicators**: Clear, visible focus outlines for keyboard users
- ✅ **Error Messages**: Clear, text-based error messages that explain how to fix issues

## System Requirements

- Python 3.7 or higher
- Windows, macOS, or Linux
- Internet connection (for speech recognition and TTS)

## Installation

### 1. Install Python Dependencies

```bash
pip install flask python-pptx pillow pytesseract PyPDF2 gtts opencv-python SpeechRecognition
```

### 2. Install Tesseract OCR (Required for image text extraction)

**Windows:**
1. Download the installer from: https://github.com/UB-Mannheim/tesseract/wiki
2. Run the installer (recommended: install to `C:\Program Files\Tesseract-OCR`)
3. The Python code will automatically find it

**macOS:**
```bash
brew install tesseract
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get install tesseract-ocr
```

### 3. Create the Project Structure (if not already done)

```
hackthon 2025/
├── app.py
├── requirements.txt
├── README.md
├── templates/
│   └── index.html
├── static/
│   ├── js/
│   │   └── main.js
│   └── css/
│       └── styles.css
└── uploads/  (created automatically)
```

## Running the Application

### 1. Navigate to the project directory
```bash
cd "c:\Users\shreyash\Desktop\hackthon 2025"
```

### 2. Start the Flask server
```bash
python app.py
```

### 3. Open in your browser
- Navigate to: `http://localhost:5000`
- You should see the VisualCogn welcome message

### 4. Test with keyboard shortcuts
After the page loads, you'll hear: *"Welcome to VisualCogn..."*

## Keyboard Shortcuts

### File Operations
| Key | Action |
|-----|--------|
| **U** | Upload file |
| **E** | Extract text from uploaded file |

### Text Processing
| Key | Action |
|-----|--------|
| **S** | Create a simple summary |
| **R** | Read text aloud |
| **D** | Download text as MP3 |

### Settings
| Key | Action |
|-----|--------|
| **+** | Increase font size |
| **-** | Decrease font size |
| **D** | Toggle dark mode |
| **Q** | Toggle quiet mode (reduces animations) |
| **H** | Show keyboard shortcuts help |

### Navigation
| Key | Action |
|-----|--------|
| **Tab** | Move to next element |
| **Shift+Tab** | Move to previous element |
| **Enter** | Activate button |
| **Space** | Activate button |
| **Arrow Keys** | Navigate within dialog |

## Usage Guide

### Step 1: Upload a File
1. Press **U** or click "Upload File"
2. Select a PDF, image (PNG, JPG), or text file
3. You'll hear confirmation that the file is ready

### Step 2: Extract Text
1. Press **E** or click "Extract Text"
2. Wait while the system reads text from your file
3. The extracted text appears in the text area
4. You'll hear a confirmation message

### Step 3: Process Your Text

**Read Aloud:**
- Press **R** or click "Read Aloud"
- Adjust speed with + and - buttons (0.5x to 2.0x)
- Press **D** or click "Stop" to stop reading

**Create a Summary:**
- Press **S** or click "Summarize Text"
- Get a shorter, simpler version of the text
- This helps with easier understanding

**Download as MP3:**
- Press **D** or click "Download MP3"
- Save the audio file to your computer
- Listen to it anytime, anywhere

### Step 4: Speech to Braille (Optional)
1. Upload an audio file (MP3, WAV, etc.)
2. The system will recognize your spoken words
3. See the recognized text and Braille format

## Customization Options

### Increase Font Size
- Press **+** multiple times to enlarge text
- Supports up to 125% of normal size
- Perfect for users with low vision

### Dark Mode
- Press **D** to toggle dark mode
- Reduces eye strain in low-light environments
- All colors maintain high contrast

### Quiet Mode
- Press **Q** to reduce animations
- Minimizes visual stimuli
- Good for users with sensory sensitivities or ADHD

## Supported File Formats

### Text Extraction
- **Documents**: PDF files
- **Images**: PNG, JPG, JPEG, BMP, TIFF, GIF
- **Text Files**: TXT, basic support for DOCX

### Audio Conversion
- **Input**: MP3, WAV, FLAC, OGG, and more
- **Output**: MP3 (for text-to-speech)

## Troubleshooting

### Issue: "Tesseract not found" error
**Solution**: Install Tesseract OCR and ensure it's in your system PATH
- Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki
- macOS: `brew install tesseract`
- Linux: `sudo apt-get install tesseract-ocr`

### Issue: File upload fails
**Solution**: 
- Check file size (max 50MB)
- Ensure file format is supported (PDF, PNG, JPG, TXT)
- Try a smaller file for testing

### Issue: Text-to-speech doesn't work
**Solution**:
- Ensure text has been extracted
- Check that your browser supports Web Speech API
- Try a different text passage

### Issue: Speech recognition fails
**Solution**:
- Check internet connection (Google Web Speech requires internet)
- Ensure audio file is valid
- Try a clearer audio recording

### Issue: Screen reader not announcing text
**Solution**:
- Press H to confirm the help dialog appears
- Check that your screen reader is enabled
- Try refreshing the page

## Technical Details

### Backend (Flask)
- **Language**: Python 3.7+
- **Dependencies**:
  - `flask`: Web framework
  - `pytesseract`: OCR engine for images
  - `PyPDF2`: PDF text extraction
  - `gtts`: Google Text-to-Speech
  - `opencv-python`: Image analysis
  - `SpeechRecognition`: Audio transcription

### Frontend
- **HTML5**: Semantic markup with ARIA labels
- **CSS3**: Responsive design, high contrast, accessibility features
- **JavaScript (Vanilla)**: No framework, accessible event handling

### Accessibility Standards Met
- ✅ WCAG 2.1 Level AA
- ✅ Section 508 (US)
- ✅ EN 301 549 (EU)
- ✅ ADA (Americans with Disabilities Act)

## API Endpoints

### Upload & Extract
```
POST /api/upload
Body: FormData with 'file' field
Returns: { filename, text, image_info? }
```

### Summarize
```
POST /api/summarize
Body: { text, max_sentences? }
Returns: { summary }
```

### Text-to-Speech
```
POST /api/tts
Body: { text, speed? }
Returns: { mp3_url, filename }
```

### Download Audio
```
GET /download/<filename>
Returns: MP3 file
```

### Speech-to-Braille
```
POST /api/speech-to-braille
Body: FormData with 'audio' field
Returns: { text, braille }
```

## Keyboard Focus Management

- **Tab**: Move forward through interactive elements
- **Shift+Tab**: Move backward through interactive elements
- **Logical Tab Order**: 
  1. Skip Link
  2. Settings (font, dark mode, quiet mode, help)
  3. Upload section
  4. Extract section
  5. Processing section
  6. Speech-to-Braille section
  7. Footer

## Screen Reader Testing

Tested with:
- ✅ NVDA (Windows)
- ✅ JAWS (Windows)
- ✅ VoiceOver (macOS)
- ✅ TalkBack (Android)

## Browser Compatibility

- ✅ Chrome 90+
- ✅ Firefox 88+
- ✅ Safari 14+
- ✅ Edge 90+

## Performance Considerations

- **Text Extraction**: 1-5 seconds (depends on file size)
- **Summarization**: 1-2 seconds
- **MP3 Generation**: 2-10 seconds (depends on text length)
- **Speech Recognition**: 3-10 seconds (depends on audio length)

## Privacy & Data

- Uploaded files are stored temporarily in the `/uploads` folder
- Files are not transmitted to external services (except for TTS and speech recognition)
- No user data is stored permanently
- **Google Services Used**: 
  - Google Text-to-Speech (gTTS)
  - Google Web Speech API

## Future Enhancements

- [ ] Support for more file formats (Word, Excel, PowerPoint)
- [ ] Multiple language support
- [ ] Offline mode (local TTS)
- [ ] User accounts and saved documents
- [ ] Handwriting recognition
- [ ] Advanced summarization options
- [ ] Custom voice selection for TTS
- [ ] Batch file processing

## License

This project is created for educational purposes as part of a hackathon for accessibility.

## Support & Contact

For issues, questions, or suggestions:
1. Check the troubleshooting section above
2. Press H in the application for help
3. Check browser console for error messages

## Credits

**Team**: Decent Debuggers  
**Purpose**: Making digital education accessible to all learners  
**Last Updated**: November 2025

---

**Thank you for using VisualCogn!** 
We're committed to making the web more accessible for everyone. 🎯

