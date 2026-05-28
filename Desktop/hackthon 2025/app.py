from flask import Flask, render_template, request, jsonify, send_file
from werkzeug.utils import secure_filename
import os
import io
from PIL import Image
import pytesseract
import PyPDF2
from gtts import gTTS
import uuid
import cv2
import numpy as np
import speech_recognition as sr
import re
import mimetypes

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Simple summarizer: score sentences by word frequency
def simple_summarize(text, max_sentences=3):
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    sentences = [s.strip() for s in sentences if s.strip()]
    
    if len(sentences) <= max_sentences:
        return text.strip()
    
    words = re.findall(r"\w+", text.lower())
    freq = {}
    for w in words:
        freq[w] = freq.get(w, 0) + 1
    
    scores = []
    for idx, s in enumerate(sentences):
        ws = re.findall(r"\w+", s.lower())
        score = sum(freq.get(w, 0) for w in ws)
        scores.append((score, idx, s))
    
    # Keep sentences in original order
    selected = sorted(scores[:max_sentences], key=lambda x: x[1])
    summary = ' '.join(s for _, _, s in selected)
    return summary.strip()

def extract_text_from_pdf(path):
    """Extract text from PDF file."""
    text = ''
    try:
        with open(path, 'rb') as f:
            try:
                reader = PyPDF2.PdfReader(f)
                for page_num, page in enumerate(reader.pages):
                    try:
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text + '\n'
                    except Exception as e:
                        app.logger.error(f"Error extracting page {page_num}: {e}")
                        continue
            except Exception as e:
                app.logger.error(f"Error reading PDF: {e}")
                return "Could not read PDF file content."
    except Exception as e:
        app.logger.error(f"Error opening PDF: {e}")
        return "Could not open PDF file."
    
    return text.strip() if text.strip() else "PDF file is empty or contains no extractable text."

def extract_text_from_image(path):
    """Extract text from image using OCR."""
    try:
        image = Image.open(path)
        # Convert to RGB if necessary
        if image.mode != 'RGB':
            image = image.convert('RGB')
        try:
            text = pytesseract.image_to_string(image)
            return text.strip() if text.strip() else "Image loaded. No readable text found."
        except Exception as ocr_error:
            # If Tesseract fails, just return a basic message
            return "Image loaded successfully. (Note: Tesseract OCR not available for text extraction. Install it for full OCR support.)"
    except Exception as e:
        app.logger.error(f"Error extracting text from image: {e}")
        return "Could not read image file."

def analyze_image(path):
    """Analyze image for faces, color, and text content."""
    try:
        img = cv2.imread(path)
        if img is None:
            return "Could not read image file."
        
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )
        faces = face_cascade.detectMultiScale(gray, 1.1, 4)
        
        # Face information
        face_info = f"Found {len(faces)} face(s)." if len(faces) > 0 else "No faces found."
        
        # Dominant color
        small = cv2.resize(img, (50, 50))
        avg_color = small.mean(axis=0).mean(axis=0)
        color_names = {
            'Blue': avg_color[0],
            'Green': avg_color[1],
            'Red': avg_color[2]
        }
        dominant = max(color_names, key=color_names.get)
        color_info = f"Dominant color: {dominant}."
        
        # OCR text
        ocr_info = "Tesseract not installed for text extraction."
        try:
            pil = Image.open(path)
            if pil.mode != 'RGB':
                pil = pil.convert('RGB')
            ocr_text = pytesseract.image_to_string(pil).strip()
            if ocr_text:
                ocr_info = f"Text found: {ocr_text[:100]}..."
        except Exception:
            pass
        
        return ' '.join([face_info, color_info, ocr_info])
    except Exception as e:
        app.logger.error(f"Error analyzing image: {e}")
        return "Could not analyze image."

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/upload', methods=['POST'])
def upload():
    """Upload and extract text from file."""
    try:
        file = request.files.get('file')
        if not file or file.filename == '':
            return jsonify({'filename': '', 'text': 'No file selected', 'image_info': ''})
        
        filename = secure_filename(file.filename)
        if not filename:
            return jsonify({'filename': '', 'text': 'Invalid filename', 'image_info': ''})
        
        # Create unique filepath
        path = os.path.join(
            app.config['UPLOAD_FOLDER'],
            f"{uuid.uuid4().hex}_{filename}"
        )
        
        try:
            file.save(path)
        except Exception as e:
            app.logger.error(f"Error saving file: {e}")
            return jsonify({'filename': filename, 'text': 'Could not save file', 'image_info': ''})
        
        # Determine file type and extract text
        ext = filename.lower().split('.')[-1]
        result = {'filename': filename, 'text': '', 'image_info': ''}
        
        try:
            if ext == 'pdf':
                text = extract_text_from_pdf(path)
                result['text'] = str(text)
            elif ext in ['png', 'jpg', 'jpeg', 'bmp', 'tiff', 'gif']:
                text = extract_text_from_image(path)
                image_desc = analyze_image(path)
                result['text'] = str(text)
                result['image_info'] = str(image_desc)
            elif ext in ['txt', 'docx', 'doc']:
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        text = f.read()
                    result['text'] = str(text) if text.strip() else "File is empty."
                except Exception:
                    result['text'] = "Could not read text file."
            else:
                result['text'] = f"Unsupported file type: {ext}"
        except Exception as e:
            app.logger.error(f"Error processing file: {e}")
            result['text'] = "Error processing file."
        
        return jsonify(result)
    except Exception as e:
        app.logger.error(f"Upload error: {e}")
        return jsonify({'filename': '', 'text': 'Server error', 'image_info': ''})

@app.route('/api/summarize', methods=['POST'])
def summarize():
    """Summarize extracted text for cognitive users."""
    data = request.json or {}
    text = data.get('text', '').strip()
    
    if not text:
        return jsonify({'error': 'No text to summarize', 'summary': ''}), 400
    
    try:
        max_sentences = int(data.get('max_sentences', 3))
        summary = simple_summarize(text, max_sentences)
        return jsonify({'summary': summary})
    except Exception as e:
        app.logger.error(f"Error summarizing: {e}")
        return jsonify({'error': str(e), 'summary': text}), 500

@app.route('/api/tts', methods=['POST'])
def tts():
    """Convert text to speech and return MP3."""
    data = request.json or {}
    text = data.get('text', '').strip()
    
    if not text:
        return jsonify({'error': 'No text provided'}), 400
    
    try:
        # Generate MP3 using gTTS
        tts_obj = gTTS(text=text, lang='en', slow=False)
        fname = os.path.join(
            app.config['UPLOAD_FOLDER'],
            f"audio_{uuid.uuid4().hex}.mp3"
        )
        tts_obj.save(fname)
        
        # Return download URL
        return jsonify({
            'success': True,
            'mp3_url': f'/download/{os.path.basename(fname)}',
            'filename': f'{os.path.basename(fname)}'
        })
    except Exception as e:
        app.logger.error(f"Error generating TTS: {e}")
        return jsonify({'error': f'TTS generation failed: {str(e)}'}), 500

@app.route('/download/<filename>')
def download(filename):
    """Download generated MP3 file."""
    # Validate filename (prevent directory traversal)
    if '..' in filename or '/' in filename or '\\' in filename:
        return jsonify({'error': 'Invalid filename'}), 400
    
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    
    if not os.path.exists(filepath):
        return jsonify({'error': 'File not found'}), 404
    
    try:
        return send_file(
            filepath,
            mimetype='audio/mpeg',
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        app.logger.error(f"Error downloading file: {e}")
        return jsonify({'error': 'Download failed'}), 500

@app.route('/api/speech-to-braille', methods=['POST'])
def speech_to_braille():
    """Convert speech to text and then to Braille."""
    file = request.files.get('audio')
    if not file:
        return jsonify({'error': 'No audio file provided'}), 400
    
    filename = secure_filename(file.filename)
    path = os.path.join(
        app.config['UPLOAD_FOLDER'],
        f"speech_{uuid.uuid4().hex}_{filename}"
    )
    
    try:
        file.save(path)
    except Exception as e:
        app.logger.error(f"Error saving audio: {e}")
        return jsonify({'error': f'Could not save file: {str(e)}'}), 500
    
    try:
        # Recognize speech
        recognizer = sr.Recognizer()
        with sr.AudioFile(path) as source:
            audio = recognizer.record(source)
        
        try:
            text = recognizer.recognize_google(audio)
        except sr.UnknownValueError:
            return jsonify({
                'error': 'Could not understand speech',
                'text': '',
                'braille': ''
            }), 400
        except sr.RequestError as e:
            return jsonify({
                'error': f'Speech recognition service error: {str(e)}',
                'text': '',
                'braille': ''
            }), 500
        
        # Convert to Braille
        def to_braille(s):
            mapping = {
                'a': '⠁', 'b': '⠃', 'c': '⠉', 'd': '⠙', 'e': '⠑', 'f': '⠋',
                'g': '⠛', 'h': '⠓', 'i': '⠊', 'j': '⠚', 'k': '⠅', 'l': '⠇',
                'm': '⠍', 'n': '⠝', 'o': '⠕', 'p': '⠏', 'q': '⠟', 'r': '⠗',
                's': '⠎', 't': '⠞', 'u': '⠥', 'v': '⠧', 'w': '⠺', 'x': '⠭',
                'y': '⠽', 'z': '⠵', ' ': ' ', '.': '⠲', ',': '⠂', '?': '⠦',
                '!': '⠖', '0': '⠴', '1': '⠂', '2': '⠆', '3': '⠒', '4': '⠐',
                '5': '⠑', '6': '⠠', '7': '⠡', '8': '⠣', '9': '⠩'
            }
            return ''.join(mapping.get(ch.lower(), '?') for ch in s)
        
        braille = to_braille(text)
        
        return jsonify({
            'success': True,
            'text': text,
            'braille': braille
        })
    
    except Exception as e:
        app.logger.error(f"Error in speech-to-braille: {e}")
        return jsonify({
            'error': f'Error processing speech: {str(e)}',
            'text': '',
            'braille': ''
        }), 500

if __name__ == '__main__':
    app.run(debug=True, host='localhost', port=5000)
