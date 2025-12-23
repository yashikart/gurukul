# Ngrok URL Auto-Update System

This system automatically updates your ngrok URLs in configuration files and ensures Ollama integration works properly.

## Features

1. **Automatic ngrok URL detection** - Tries to get the current ngrok URL from the ngrok API or accepts manual input
2. **Configuration file updates** - Automatically updates all relevant configuration files:
   - Frontend `.env` file
   - Frontend `.env.local` file
   - Backend `.env` file
3. **Ollama integration testing** - Verifies that Ollama is properly configured and working
4. **Easy execution** - Run with either batch or PowerShell scripts

## Usage

### Method 1: Using Batch Script (Windows)
Double-click on `update_ngrok.bat` or run from command prompt:
```cmd
update_ngrok.bat
```

### Method 2: Using PowerShell Script (Windows)
Right-click on `update_ngrok.ps1` and select "Run with PowerShell" or run from PowerShell:
```powershell
.\update_ngrok.ps1
```

### Method 3: Direct Python Execution
From the project root directory:
```bash
python update_ngrok_url.py
```

## How It Works

1. The script first attempts to automatically detect your current ngrok URL by querying the ngrok API (if ngrok is running locally)
2. If automatic detection fails, it prompts you to manually enter your current ngrok URL
3. It updates all configuration files with the new ngrok URL:
   - Updates `GROQ_API_ENDPOINT`, `UNIGURU_NGROK_ENDPOINT`, `UNIGURU_API_BASE_URL`, etc. in frontend `.env`
   - Updates `VITE_NGROK_URL`, `VITE_CHAT_API_BASE_URL`, `VITE_CHATBOT_API_URL` in frontend `.env.local`
   - Updates `NGROK_URL`, `UNIGURU_NGROK_ENDPOINT`, `UNIGURU_API_BASE_URL` in backend `.env`
4. Tests Ollama integration to ensure local LLM models are working properly

## Ollama Integration

The system includes Ollama integration for local LLM support:

1. **Model Requirements**: The system uses `llama3.2:3b` model by default
2. **Installation**: Make sure Ollama is installed and running on your system
3. **Model Pull**: If the required model is not available, pull it using:
   ```bash
   ollama pull llama3.2:3b
   ```
4. **Testing**: The update script automatically tests Ollama connectivity

## Scheduling Daily Updates

To automatically update the ngrok URL daily, you can schedule the script using Windows Task Scheduler:

1. Open Task Scheduler
2. Create a new task
3. Set trigger to daily
4. Set action to run `update_ngrok.bat`
5. Set the start directory to your project root

## Troubleshooting

### Common Issues

1. **Ngrok URL Not Detected**: Make sure ngrok is running locally on port 4040, or manually enter the URL
2. **Configuration Files Not Updated**: Check file permissions and ensure the script is run from the project root
3. **Ollama Not Working**: 
   - Ensure Ollama is installed: https://ollama.ai/download
   - Check if the required model is pulled: `ollama list`
   - Verify Ollama is running: `ollama serve`

### Manual Configuration

If the automatic update fails, you can manually update the URLs in these files:

**Frontend `.env`:**
```
GROQ_API_ENDPOINT=https://YOUR_NGROK_URL.ngrok-free.app
UNIGURU_NGROK_ENDPOINT=https://YOUR_NGROK_URL.ngrok-free.app
UNIGURU_API_BASE_URL=https://YOUR_NGROK_URL.ngrok-free.app
VITE_CHATBOT_API_URL=https://YOUR_NGROK_URL.ngrok-free.app
```

**Frontend `.env.local`:**
```
VITE_NGROK_URL=https://YOUR_NGROK_URL.ngrok-free.app
VITE_CHAT_API_BASE_URL=https://YOUR_NGROK_URL.ngrok-free.app
VITE_CHATBOT_API_URL=https://YOUR_NGROK_URL.ngrok-free.app
```

**Backend `.env`:**
```
NGROK_URL=https://YOUR_NGROK_URL.ngrok-free.app
UNIGURU_NGROK_ENDPOINT=${NGROK_URL}
UNIGURU_API_BASE_URL=${NGROK_URL}
```

## Support

For issues with this system, please check:
1. Ensure all paths are correct
2. Verify Python and required packages are installed
3. Check that ngrok is properly configured
4. Confirm Ollama is installed and running with the required models