import os
import io
import hashlib
import requests
from datetime import datetime
from PIL import Image
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
import validators
import pyshorteners

# === CONFIGURATION ===
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
if not TOKEN:
    raise ValueError("No TELEGRAM_BOT_TOKEN found! Please set it in Railway environment variables.")

# === IMAGE GENERATION API (FREE - uses Pollinations.ai) ===
def generate_image(prompt: str) -> str:
    """Generate an image using the free Pollinations.ai API"""
    # Encode prompt for URL
    encoded_prompt = requests.utils.quote(prompt)
    # Pollinations generates images on the fly
    image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=512&height=512&nologo=true"
    return image_url

# === IMAGE CONVERSION ===
def convert_image(image_bytes: bytes, target_format: str) -> bytes:
    """Convert image to specified format (jpg, png, webp, etc.)"""
    try:
        img = Image.open(io.BytesIO(image_bytes))
        output = io.BytesIO()
        
        # Handle RGBA -> RGB for JPEG
        if target_format.lower() == 'jpeg' or target_format.lower() == 'jpg':
            if img.mode == 'RGBA':
                img = img.convert('RGB')
            target_format = 'JPEG'
        elif target_format.lower() == 'png':
            target_format = 'PNG'
        elif target_format.lower() == 'webp':
            target_format = 'WEBP'
        else:
            target_format = target_format.upper()
        
        img.save(output, format=target_format)
        return output.getvalue()
    except Exception as e:
        raise Exception(f"Conversion failed: {str(e)}")

# === URL SHORTENER ===
def shorten_url(long_url: str) -> str:
    """Shorten URL using multiple free services (fallback)"""
    try:
        # Try TinyURL first (free, no API key needed)
        s = pyshorteners.Shortener()
        return s.tinyurl.short(long_url)
    except:
        try:
            # Fallback to is.gd
            response = requests.get(f"https://is.gd/create.php?format=simple&url={long_url}")
            if response.status_code == 200:
                return response.text.strip()
        except:
            pass
        return f"Error: Could not shorten URL. Please try again."

# === KEYBOARD / MENU ===
def get_main_menu():
    keyboard = [
        [InlineKeyboardButton("📸 Image Converter", callback_data="convert")],
        [InlineKeyboardButton("🎨 Image Generator", callback_data="generate")],
        [InlineKeyboardButton("🔗 URL Shortener", callback_data="shorten")],
        [InlineKeyboardButton("ℹ️ Help", callback_data="help")]
    ]
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a welcome message with the main menu"""
    welcome_text = (
        "🤖 *Welcome to Nexa562 Bot!*\n\n"
        "I can help you with:\n"
        "📸 *Image Converter* - Convert images to JPG, PNG, WEBP\n"
        "🎨 *Image Generator* - Create images from text prompts\n"
        "🔗 *URL Shortener* - Shorten long URLs instantly\n\n"
        "Choose an option below:"
    )
    await update.message.reply_text(welcome_text, 
                                   parse_mode="Markdown",
                                   reply_markup=get_main_menu())

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button clicks from the menu"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "convert":
        await query.edit_message_text(
            "📸 *Image Converter*\n\n"
            "Send me an image, and I'll convert it to your preferred format.\n\n"
            "Supported formats: `JPG`, `PNG`, `WEBP`\n\n"
            "Just send an image and then tell me the format you want.",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Back to Menu", callback_data="menu")]
            ])
        )
        context.user_data['mode'] = 'convert'
    
    elif query.data == "generate":
        await query.edit_message_text(
            "🎨 *Image Generator*\n\n"
            "Send me a text description, and I'll generate an image for you.\n\n"
            "Example: `A beautiful sunset over mountains`\n\n"
            "The more detailed your prompt, the better the result!",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Back to Menu", callback_data="menu")]
            ])
        )
        context.user_data['mode'] = 'generate'
    
    elif query.data == "shorten":
        await query.edit_message_text(
            "🔗 *URL Shortener*\n\n"
            "Send me a long URL and I'll shorten it instantly.\n\n"
            "Example: `https://www.example.com/very/long/url/here`",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Back to Menu", callback_data="menu")]
            ])
        )
        context.user_data['mode'] = 'shorten'
    
    elif query.data == "help":
        help_text = (
            "ℹ️ *How to use Nexa562 Bot*\n\n"
            "1️⃣ *Image Converter*: Send an image, then reply with format (jpg/png/webp)\n"
            "2️⃣ *Image Generator*: Send a text prompt describing what you want\n"
            "3️⃣ *URL Shortener*: Send any URL and get a short link\n\n"
            "Use the main menu to switch between functions.\n\n"
            "Made with ❤️ using Python & Railway"
        )
        await query.edit_message_text(help_text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Back to Menu", callback_data="menu")]
        ]))
    
    elif query.data == "menu":
        await query.edit_message_text(
            "🤖 *Welcome back to Nexa562 Bot!*\n\n"
            "Choose an option below:",
            parse_mode="Markdown",
            reply_markup=get_main_menu()
        )
        context.user_data['mode'] = None

async def handle_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle user messages based on the current mode"""
    user = update.effective_user
    message = update.message
    mode = context.user_data.get('mode')
    
    # If no mode set, ask to choose from menu
    if not mode:
        await message.reply_text(
            "Please choose an option from the menu first!",
            reply_markup=get_main_menu()
        )
        return
    
    # === IMAGE CONVERSION ===
    if mode == 'convert':
        if message.photo:
            # Get the largest photo
            photo_file = await message.photo[-1].get_file()
            image_bytes = await photo_file.download_as_bytearray()
            
            # Store image in context for later
            context.user_data['image_bytes'] = image_bytes
            
            await message.reply_text(
                "✅ Image received!\n\n"
                "Now reply with the format you want:\n"
                "• `jpg` or `jpeg`\n"
                "• `png`\n"
                "• `webp`\n\n"
                "Example: `png`",
                parse_mode="Markdown"
            )
            context.user_data['awaiting_format'] = True
        else:
            await message.reply_text(
                "❌ Please send an image (photo), not text or other files."
            )
    
    # === IMAGE GENERATION ===
    elif mode == 'generate':
        prompt = message.text
        if not prompt or len(prompt) < 2:
            await message.reply_text(
                "❌ Please provide a valid text description (at least 2 characters)."
            )
            return
        
        await message.reply_text("🎨 Generating your image... This may take a moment.")
        
        try:
            # Generate image URL
            image_url = generate_image(prompt)
            
            # Download the generated image
            response = requests.get(image_url, timeout=30)
            if response.status_code == 200:
                await message.reply_photo(
                    photo=response.content,
                    caption=f"🎨 *Generated for: {prompt[:50]}...*\n\n"
                            f"Prompt: `{prompt}`\n"
                            f"Powered by Pollinations.ai",
                    parse_mode="Markdown"
                )
            else:
                await message.reply_text(
                    "❌ Failed to generate image. Please try a different prompt."
                )
        except Exception as e:
            await message.reply_text(f"❌ Error: {str(e)}")
    
    # === URL SHORTENER ===
    elif mode == 'shorten':
        url = message.text.strip()
        
        # Validate URL
        if not validators.url(url):
            await message.reply_text(
                "❌ That doesn't look like a valid URL.\n\n"
                "Make sure it starts with `http://` or `https://`",
                parse_mode="Markdown"
            )
            return
        
        await message.reply_text("🔗 Shortening your URL...")
        
        try:
            short_url = shorten_url(url)
            await message.reply_text(
                f"✅ *URL shortened successfully!*\n\n"
                f"🔗 Original: `{url}`\n"
                f"📎 Short URL: `{short_url}`",
                parse_mode="Markdown"
            )
        except Exception as e:
            await message.reply_text(f"❌ Error shortening URL: {str(e)}")

async def handle_format_response(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the format selection after an image is received"""
    if not context.user_data.get('awaiting_format'):
        return
    
    format_input = update.message.text.strip().lower()
    valid_formats = ['jpg', 'jpeg', 'png', 'webp']
    
    if format_input not in valid_formats:
        await update.message.reply_text(
            f"❌ Invalid format. Please choose from: {', '.join(valid_formats)}"
        )
        return
    
    image_bytes = context.user_data.get('image_bytes')
    if not image_bytes:
        await update.message.reply_text("❌ Image not found. Please send the image again.")
        context.user_data['awaiting_format'] = False
        return
    
    await update.message.reply_text(f"🔄 Converting to {format_input.upper()}...")
    
    try:
        # Convert the image
        converted = convert_image(image_bytes, format_input)
        
        # Determine the correct mimetype for sending
        mime_type = 'image/jpeg' if format_input in ['jpg', 'jpeg'] else f'image/{format_input}'
        file_ext = 'jpg' if format_input in ['jpg', 'jpeg'] else format_input
        
        await update.message.reply_document(
            document=io.BytesIO(converted),
            filename=f"converted.{file_ext}",
            caption=f"✅ Converted successfully!\n\nFormat: `{format_input.upper()}`",
            parse_mode="Markdown"
        )
        
        # Reset state
        context.user_data['image_bytes'] = None
        context.user_data['awaiting_format'] = False
        
    except Exception as e:
        await update.message.reply_text(f"❌ Conversion failed: {str(e)}")
        context.user_data['awaiting_format'] = False

# === ERROR HANDLER ===
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Log errors and notify user"""
    print(f"Error: {context.error}")
    try:
        if update and update.effective_message:
            await update.effective_message.reply_text(
                "❌ An error occurred. Please try again or use /start to reset."
            )
    except:
        pass

# === MAIN ===
def main():
    """Start the bot"""
    if not TOKEN:
        raise ValueError("TELEGRAM_BOT_TOKEN environment variable is not set!")
    
    print("🚀 Starting Nexa562 Bot...")
    
    # Create application
    application = Application.builder().token(TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.PHOTO, handle_messages))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_messages))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_format_response))
    application.add_error_handler(error_handler)
    
    # Start the bot (using long polling for Railway)
    print("✅ Bot is running...")
    application.run_polling()

if __name__ == "__main__":
    main()
