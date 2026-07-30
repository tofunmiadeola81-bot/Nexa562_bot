# 🤖 Nexa562 Bot

A multi-purpose Telegram bot that can:
- 📸 Convert images (JPG, PNG, WEBP)
- 🎨 Generate images from text prompts
- 🔗 Shorten URLs

## 🚀 Features

### Image Converter
- Supports: JPG, PNG, WEBP
- Just send an image and specify the format

### Image Generator
- Uses Pollinations.ai API (free, no API key needed)
- Generate images from text descriptions

### URL Shortener
- Shorten long URLs instantly
- Uses TinyURL (fallback: is.gd)

## 🛠️ Technologies

- Python 3.11+
- python-telegram-bot
- Pillow
- Railway (Hosting)
- GitHub (Version Control)

## 📦 Installation

### Local Development

```bash
# Clone the repository
git clone https://github.com/yourusername/nexa562-bot.git
cd nexa562-bot

# Install dependencies
pip install -r requirements.txt

# Set up environment variable
export TELEGRAM_BOT_TOKEN="your_bot_token_here"

# Run the bot
python bot.py
