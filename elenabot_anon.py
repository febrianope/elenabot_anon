from telegram import BotCommand, Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
import logging

# Aktifkan logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# dictionary buat simpan pasangan yang sedang terhubung
connected_pairs = {}
# dictionary buat simpan message_id mapping antara pengirim dan penerima
message_id_mapping = {}

# fungsi untuk menyimpan mapping message ID
def save_message_mapping(sender_id, sender_message_id, receiver_id, receiver_message_id):
    if sender_id not in message_id_mapping:
        message_id_mapping[sender_id] = {}
    message_id_mapping[sender_id][sender_message_id] = receiver_message_id

# fungsi untuk mendapatkan message ID yang sesuai
def get_mapped_message_id(user_id, original_message_id):
    return message_id_mapping.get(user_id, {}).get(original_message_id)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("hiii, welcome to the vibes! ketik /search kalo mau nyari partner chat, atau /stop kalo udah mau end session. let’s vibe!")

async def search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id in connected_pairs and connected_pairs[user_id] is not None:
        await update.message.reply_text("yess! udah terhubung sama aku! happy chatting!")
        return

    for partner_id in list(connected_pairs.keys()):
        if connected_pairs[partner_id] is None and partner_id != user_id:
            connected_pairs[partner_id] = user_id
            connected_pairs[user_id] = partner_id
            await context.bot.send_message(user_id, "yesss, match found! you're now connected with a new vibe buddy. let’s get chatting!")
            await context.bot.send_message(partner_id, "yesss, match found! you're now connected with a new vibe buddy. let’s get chatting!")
            return

    connected_pairs[user_id] = None
    await context.bot.send_message(user_id, "chill dulu ya, still looking for your perfect match. just hang tight!")

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id in connected_pairs and connected_pairs[user_id] is not None:
        partner_id = connected_pairs[user_id]
        await context.bot.send_message(user_id, "alright, convo ended! kalau mau balik lagi, tinggal ketik /search aja, easy peasy!")
        await context.bot.send_message(partner_id, "partner decided to end the chat. it’s all good, still here if you wanna chat again!")
        del connected_pairs[partner_id]
        del connected_pairs[user_id]
        if user_id in message_id_mapping:
            del message_id_mapping[user_id]
        if partner_id in message_id_mapping:
            del message_id_mapping[partner_id]
    else:
        await context.bot.send_message(user_id, "eh kamu belum nyambung nih sama aku. sabar ya!")

async def partner_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    
    if user_id not in connected_pairs or connected_pairs[user_id] is None:
        if update.message.text and not update.message.text.startswith('/'):
            await update.message.reply_text("sorry nihh, tapi kamu belum connect. tekan /search buat connect yaa!")
        return

    partner_id = connected_pairs[user_id]
    reply_to_message_id = None

    # Handle reply messages
    if update.message.reply_to_message:
        original_message_id = update.message.reply_to_message.message_id
        mapped_message_id = get_mapped_message_id(user_id, original_message_id)
        if mapped_message_id:
            reply_to_message_id = mapped_message_id

    try:
        if update.message.text:
            # Handle text messages with bubble reply
            sent_message = await context.bot.send_message(
                partner_id,
                update.message.text,
                reply_to_message_id=reply_to_message_id
            )
            save_message_mapping(partner_id, sent_message.message_id, user_id, update.message.message_id)

        elif update.message.photo:
            # Handle photos with 'sekali lihat' (view once)
            sent_message = await context.bot.send_photo(
                partner_id,
                update.message.photo[-1].file_id,
                caption=update.message.caption,
                reply_to_message_id=reply_to_message_id,
                protect_content=True  # Foto sekali lihat
            )
            save_message_mapping(partner_id, sent_message.message_id, user_id, update.message.message_id)

        elif update.message.voice:
            # Handle voice notes with reply bubble
            sent_message = await context.bot.send_voice(
                partner_id,
                update.message.voice.file_id,
                caption=update.message.caption,
                reply_to_message_id=reply_to_message_id
            )
            save_message_mapping(partner_id, sent_message.message_id, user_id, update.message.message_id)

        elif update.message.video:
            # Handle videos with reply bubble
            sent_message = await context.bot.send_video(
                partner_id,
                update.message.video.file_id,
                caption=update.message.caption,
                reply_to_message_id=reply_to_message_id,
                protect_content=update.message.has_protected_content
            )
            save_message_mapping(partner_id, sent_message.message_id, user_id, update.message.message_id)

        elif update.message.sticker:
            # Handle stickers with reply bubble
            sent_message = await context.bot.send_sticker(
                partner_id,
                update.message.sticker.file_id,
                reply_to_message_id=reply_to_message_id
            )
            save_message_mapping(partner_id, sent_message.message_id, user_id, update.message.message_id)

        elif update.message.document:
            # Handle documents with reply bubble
            sent_message = await context.bot.send_document(
                partner_id,
                update.message.document.file_id,
                caption=update.message.caption,
                reply_to_message_id=reply_to_message_id
            )
            save_message_mapping(partner_id, sent_message.message_id, user_id, update.message.message_id)

    except Exception as e:
        logging.error(f"Error sending message: {e}")
        await context.bot.send_message(user_id, "uh-oh, something went wrong. coba lagi aja, siapa tau sekarang bisa.")

async def set_commands(application: Application):
    commands = [
        BotCommand('start', 'mulai the vibe'),
        BotCommand('search', 'cari aku di sini'),
        BotCommand('stop', 'end the convo vibes')

    ]
    await application.bot.set_my_commands(commands)

def main():
    application = Application.builder().token("7613165971:AAHvlvFOgk8LnE-1aKn62DXXASrazI0VzCQ").build()

    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('search', search))
    application.add_handler(CommandHandler('stop', stop))
    application.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, partner_chat))

    print("Bot started...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
