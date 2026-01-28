import os
import asyncio
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
from openrouter import SocialMediaPost


# Global state for async workflow
feedback_decision = None
feedback_reason = None
feedback_done = asyncio.Event()
has_image = False  # Track if the message has an image


async def handle_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle Approve/Reject button presses."""
    global feedback_decision, feedback_reason, has_image
    
    query = update.callback_query
    await query.answer()  # Acknowledge the button press
    
    if query.data == "approve":
        feedback_decision = "approve"
        # Use the right edit method based on message type
        try:
            if has_image:
                await query.edit_message_caption(caption="✅ Post approved! Publishing now...")
            else:
                await query.edit_message_text("✅ Post approved! Publishing now...")
        except Exception as e:
            # If edit fails, just send a new message
            await query.message.reply_text("✅ Post approved! Publishing now...")
        feedback_done.set()
        
    elif query.data == "reject":
        feedback_decision = "reject"
        try:
            if has_image:
                await query.edit_message_caption(
                    caption="❌ Post rejected. Please reply with the reason why you rejected this post:"
                )
            else:
                await query.edit_message_text(
                    "❌ Post rejected. Please reply with the reason why you rejected this post:"
                )
        except Exception as e:
            # If edit fails, just send a new message
            await query.message.reply_text(
                "❌ Post rejected. Please reply with the reason why you rejected this post:"
            )
        # Don't set feedback_done yet - wait for the text reason


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text feedback after rejection."""
    global feedback_reason
    
    if feedback_decision == "reject" and not feedback_done.is_set():
        feedback_reason = update.message.text
        await update.message.reply_text(
            f"📝 Feedback recorded: '{feedback_reason}'\n\n"
            "Thanks! This will help improve future posts."
        )
        feedback_done.set()


async def send_for_approval(post: SocialMediaPost, image_path: str | None = None) -> tuple[str, str | None]:
    """
    Send a post to Telegram for human approval.
    
    Args:
        post: The SocialMediaPost object to approve
        image_path: Optional path to the generated image
        
    Returns:
        tuple: (decision, reason) where decision is "approve" or "reject"
               and reason is the feedback text (only if rejected)
    """
    global feedback_decision, feedback_reason, has_image
    
    # Reset state
    feedback_decision = None
    feedback_reason = None
    feedback_done.clear()
    has_image = image_path is not None and os.path.exists(image_path)
    
    # Prepare the message
    post_content = f"{post.caption}\n\n{post.hashtags}"
    message_text = (
        "📝 **New Post for Approval**\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"{post_content}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📊 Characters: {len(post_content)}\n"
        f"🖼️ Image: {'Yes' if has_image else 'No'}\n"
        f"💡 Image prompt: {post.image_prompt if post.image_prompt else 'N/A'}"
    )
    
    # Create approval buttons
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Approve", callback_data="approve"),
            InlineKeyboardButton("❌ Reject", callback_data="reject"),
        ]
    ])
    
    # Send to Telegram
    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    
    # Send image if available
    if has_image:
        with open(image_path, "rb") as img:
            await bot.send_photo(
                chat_id=int(TELEGRAM_CHAT_ID),
                photo=img,
                caption=message_text,
                reply_markup=keyboard,
            )
    else:
        await bot.send_message(
            chat_id=int(TELEGRAM_CHAT_ID),
            text=message_text,
            reply_markup=keyboard,
        )
    
    print("📱 Sent to Telegram. Waiting for approval...")
    
    # Set up the bot application
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CallbackQueryHandler(handle_button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    
    # Start polling
    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    
    # Wait for human decision
    await feedback_done.wait()
    
    # Cleanup
    await app.updater.stop()
    await app.stop()
    await app.shutdown()
    
    print(f"\n✅ Decision received: {feedback_decision}")
    if feedback_reason:
        print(f"💬 Feedback: {feedback_reason}")
    
    return feedback_decision, feedback_reason


async def send_simple_notification(text: str):
    """Send a simple notification message to Telegram."""
    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    message = await bot.send_message(
        chat_id=int(TELEGRAM_CHAT_ID),
        text=text,
    )
    print(f"✅ Notification sent! ID: {message.message_id}")
    return message


# Synchronous wrapper for use in non-async contexts
def request_approval(post: SocialMediaPost, image_path: str | None = None) -> tuple[str, str | None]:
    """
    Synchronous wrapper for send_for_approval.
    Use this in your main.py file.
    """
    return asyncio.run(send_for_approval(post, image_path))


def send_notification(text: str):
    """Synchronous wrapper for send_simple_notification."""
    return asyncio.run(send_simple_notification(text))