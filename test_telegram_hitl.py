import os
import asyncio
from telegram import Bot
from dotenv import load_dotenv

load_dotenv()


async def test_telegram_setup():
    """Test if Telegram bot can send messages."""
    print("🔍 Testing Telegram Bot Setup...\n")
    
    # Check environment variables
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    
    if not bot_token:
        print("❌ TELEGRAM_BOT_TOKEN not found in .env file")
        print("   Please add: TELEGRAM_BOT_TOKEN=your_bot_token_here")
        return False
    
    if not chat_id:
        print("❌ TELEGRAM_CHAT_ID not found in .env file")
        print("   Please add: TELEGRAM_CHAT_ID=your_chat_id_here")
        return False
    
    print("✅ Environment variables found")
    print(f"   Bot token: {bot_token[:10]}...{bot_token[-5:]}")
    print(f"   Chat ID: {chat_id}\n")
    
    # Try to send a test message
    try:
        bot = Bot(token=bot_token)
        
        # Get bot info
        bot_info = await bot.get_me()
        print(f"✅ Bot connected successfully!")
        print(f"   Bot name: {bot_info.first_name}")
        print(f"   Bot username: @{bot_info.username}\n")
        
        # Send test message
        message = await bot.send_message(
            chat_id=int(chat_id),
            text="🎉 Test successful! Your Telegram bot is working correctly.\n\n"
                 "You're ready to use the human-in-the-loop approval system!"
        )
        
        print(f"✅ Test message sent successfully!")
        print(f"   Message ID: {message.message_id}")
        print(f"\n✨ Check your Telegram to see the message!\n")
        return True
        
    except ValueError:
        print(f"❌ Invalid TELEGRAM_CHAT_ID format: {chat_id}")
        print("   Chat ID should be a number (e.g., 123456789)")
        print("\n💡 To find your chat ID:")
        print("   1. Send a message to your bot")
        print(f"   2. Visit: https://api.telegram.org/bot{bot_token}/getUpdates")
        print('   3. Look for "chat":{"id":XXXXXXXX}')
        return False
        
    except Exception as e:
        print(f"❌ Error connecting to Telegram: {e}")
        print("\n🔧 Troubleshooting:")
        print("   1. Make sure you've started a chat with your bot")
        print("   2. Verify your bot token is correct")
        print("   3. Check your internet connection")
        return False


def main():
    """Run the test."""
    print("=" * 50)
    print("TELEGRAM BOT SETUP TEST")
    print("=" * 50 + "\n")
    
    success = asyncio.run(test_telegram_setup())
    
    print("\n" + "=" * 50)
    if success:
        print("✅ ALL TESTS PASSED!")
        print("=" * 50)
        print("\n🚀 You can now run: python main_with_approval.py")
    else:
        print("❌ SETUP INCOMPLETE")
        print("=" * 50)
        print("\n📖 Please check the README_APPROVAL.md for setup instructions")


if __name__ == "__main__":
    main()