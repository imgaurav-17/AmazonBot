import logging
import os
import requests
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from amazon_paapi import get_asin
from utils.create_message import amazon_message
from utils.product_amazon import Product
from utils.tools import check_domain

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)

def start(update, context):
    update.message.reply_text('Send me links from Amazon! I will give you back a nice post.')

def message_url(update, context):
    amazon_valid_urls = ['www.amzn.to/', 'amzn.to/', 'www.amzn.in/', 'amzn.in/',
                     'www.amazon.', 'amazon.']

    message_text = update.message.text
    logger.info(f"Received URL: {message_text}")

    # Extract URL from the message text
    url = None
    words = message_text.split()
    for word in words:
        if any(valid_url in word for valid_url in amazon_valid_urls):
            url = word
            break

    if not url:
        logger.error("No valid URL found in the message.")
        update.message.reply_text("No valid URL found in the message.")
        return

    domain = check_domain(url)
    logger.info(f"Domain: {domain}")

    if domain.startswith(tuple(amazon_valid_urls)):
        if 'amzn.to/' in domain:
            try:
                # Follow redirection to get the actual URL
                logger.info("Shortened URL detected, following redirection...")
                response = requests.get(url)
                logger.info(f"HTTP status code: {response.status_code}")
                logger.info(f"Response headers: {response.headers}")
                url = response.url
                logger.info(f"Expanded URL: {url}")
                domain = check_domain(url)  # Update the domain
            except requests.exceptions.RequestException as e:
                logger.error(f"Error resolving URL: {e}")
                update.message.reply_text("There was an error resolving the shortened URL.")
                return

        asin = get_asin(url)
        logger.info(f"Extracted ASIN: {asin}")
        product = Product(asin)
        message = amazon_message(product, update)
        context.bot.send_message(update.message.chat_id, message[0], reply_markup=message[1], parse_mode='HTML')
        context.bot.delete_message(update.message.chat_id, update.message.message_id)

def main():
    # Load Telegram BOT-TOKEN from environment variables
    bot_token = os.getenv('BOT_TOKEN')
    port = int(os.environ.get('PORT', '8443'))

    updater = Updater(bot_token, use_context=True)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(MessageHandler(Filters.regex(r'(https?://)?(www\.)?(amzn\.to/|amzn\.in/|amazon\.[a-z]{2,3}(\.[a-z]{2})?/[^ ]*)'), message_url))

    # Start the webhook
    updater.start_webhook(listen="0.0.0.0",
                          port=port,
                          url_path=bot_token,
                          webhook_url=f"https://{os.getenv('RENDER_EXTERNAL_HOSTNAME')}/{bot_token}")

    updater.idle()

if __name__ == '__main__':
    main()
