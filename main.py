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

    amazon_valid_urls = ['www.amzn.to', 'amzn.to',
                         'www.amazon.', 'amazon.']

    url = update.message.text
    domain = check_domain(update.message.text)

    if domain.startswith(tuple(amazon_valid_urls)):

        if 'amzn.to/' in domain:
    try:
        # Follow redirection to get the actual URL
        url = requests.get(url).url
        domain = check_domain(url)  # Update the domain
    except requests.exceptions.RequestException as e:
        logger.error(f"Error resolving URL: {e}")
        update.message.reply_text("There was an error resolving the shortened URL.")
        return


        product = Product(get_asin(url))
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

    dispatcher.add_handler(MessageHandler(Filters.regex('(?i)((?:https?://|www\d{0,3}[.])?[a-z0-9.\-]+[.](?:(?:com.br/)|(?:ca/)|(?:com.mx/)|(?:com/)|(?:cn/)|(?:in/)|(?:co.jp/)|(?:sg/)|(?:com.tr/)|(?:ae/)|(?:sa/)|(?:fr/)|(?:de/)|(?:it/)|(?:nl/)|(?:pl/)|(?:es/)|(?:se/)|(?:co.uk/)|(?:com.au/))(?:/[^\s()<>]+[^\s`!()\[\]{};:\'".,<>?\xab\xbb\u201c\u201d\u2018\u2019])?)'), message_url))


    updater.start_webhook(listen="0.0.0.0", port=port, url_path=bot_token, webhook_url=f"https://{os.getenv('RENDER_EXTERNAL_HOSTNAME')}/{bot_token}")
    
    updater.idle()

if __name__ == '__main__':
    main()
