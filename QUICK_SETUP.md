# Quick Setup Guide - Gemini Integration

## Immediate Setup (5 minutes)

### 1. Install the Gemini package
```bash
pip install google-generativeai>=0.8.0
```

### 2. Get your API key
- Visit: https://aistudio.google.com/app/apikeys
- Click "Create API Key"
- Copy the key

### 3. Add to .env file
```bash
echo "GEMINI_API_KEY=your_key_here" >> .env
```

### 4. Apply database migrations
```bash
python manage.py migrate
```

### 5. Test the connection
```bash
python manage.py shell
from dataapp.services.ai_assistant import validate_gemini_setup
print(validate_gemini_setup())
```

Expected output:
```python
{
    'package_installed': True,
    'dotenv_loaded': True,
    'api_key_loaded': True,
    'configured': True,
    'status': 'ok'
}
```

## That's It! 🎉

Now you can:
1. Upload a CSV dataset
2. Go to "Gemini AI Assistant" page
3. Start asking questions about your data!

## Available Features

### From the AI Assistant Page:
- 📊 **Generate Reports** - Executive summaries, business insights, research papers
- 🔍 **Data Analysis** - Full dataset analysis, model comparison, accuracy suggestions  
- 💡 **Quick Questions** - Pre-built question templates
- 🤖 **Smart Chat** - Conversation with memory

### What Gemini Can Do:
✅ Explain your dataset  
✅ Identify data quality issues  
✅ Recommend preprocessing steps  
✅ Compare trained models  
✅ Suggest accuracy improvements  
✅ Generate business insights  
✅ Explain predictions  
✅ Answer follow-up questions (with memory)  

## Next Steps

### Learn More:
- Read: `GEMINI_INTEGRATION_GUIDE.md` for comprehensive documentation
- Run tests: `python test_gemini/run_all_tests.py`
- Check test coverage: See `test_gemini/README.md`

### Start Using:
1. Upload your CSV
2. Click "Gemini AI Assistant" in navigation
3. Ask anything about your data!

## Troubleshooting

**"API Key Missing" error:**
- Check `.env` file has `GEMINI_API_KEY=...`
- Restart Django server after adding key

**"Gemini timeout":**
- Ask shorter questions
- Check internet connection
- Check API quota at aistudio.google.com

**"No dataset loaded":**
- Upload a CSV first from home page
- Make sure you're using the AI Assistant page (not other pages)

## Support

For detailed documentation, see: `GEMINI_INTEGRATION_GUIDE.md`

For issues, check:
- Error messages in Django logs
- `GEMINI_INTEGRATION_GUIDE.md` troubleshooting section
- Test results from `test_gemini/run_all_tests.py`
