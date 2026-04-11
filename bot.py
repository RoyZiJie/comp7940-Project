import os
import re
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters

# Import RAG engine
from rag_engine import (
    retrieve_context,
    generate_prompt,
    complete_document_sdk,
    ConversationManager,
    nodes,
    is_greeting,
    extract_answer
)

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

# User-specific conversation managers
conversation_managers = {}


async def start(update: Update, context):
    """Handle /start command"""
    await update.message.reply_text(
        "🎓 **HKBU Buddy** is online!\n\n"
        "I am your HKBU campus study assistant. I can help you with:\n"
        "📚 Course information\n"
        "🏫 Campus facilities\n"
        "📅 Semester schedule\n\n"
        "Just send me your questions!\n\n"
        "**Commands:**\n"
        "/clear - Clear conversation history\n"
        "/help - Show help",
        parse_mode="Markdown"
    )


async def help_command(update: Update, context):
    """Handle /help command"""
    await update.message.reply_text(
        "📖 **Help**\n\n"
        "Send me any questions about HKBU, and I will answer based on school documents.\n\n"
        "**Commands:**\n"
        "/start - Restart conversation\n"
        "/clear - Clear conversation history\n"
        "/help - Show this help\n\n"
        "**Example questions:**\n"
        "• What courses does Computer Science department offer?\n"
        "• When does the library open?\n"
        "• When is the final exam week?",
        parse_mode="Markdown"
    )


async def clear_command(update: Update, context):
    """Handle /clear command"""
    user_id = update.effective_user.id
    if user_id in conversation_managers:
        conversation_managers[user_id].clear_history()
        del conversation_managers[user_id]
    await update.message.reply_text("🧹 Conversation history cleared!")


async def handle_message(update: Update, context):
    """Handle user messages"""
    user_id = update.effective_user.id
    user_input = update.message.text.strip()

    if not user_input:
        return

    # Send "typing" indicator
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    try:
        # Get user's conversation manager
        if user_id not in conversation_managers:
            conversation_managers[user_id] = ConversationManager()
        conv_manager = conversation_managers[user_id]
        history_str = conv_manager.get_history_string()

        # Check if it's a greeting
        if is_greeting(user_input):
            answer = "Hello! How can I assist you with your studies today?"
            conv_manager.add_message("User", user_input)
            conv_manager.add_message("Assistant", answer)
            await update.message.reply_text(answer)
            return

        # 1. Retrieve relevant context from documents
        retrieval_context = retrieve_context(
            nodes=nodes,
            query=user_input,
            method="keyword",
            top_k=5
        )

        # Build context string
        if retrieval_context:
            context_str = "\n\n".join([
                f"[Source: {item.get('file_name', 'unknown')}]\n{item.get('content', '')}"
                for item in retrieval_context
            ])
            print(f"📚 Retrieved {len(retrieval_context)} relevant chunks")
        else:
            context_str = "No relevant documents found. Answer based on your knowledge."
            print("📚 No relevant documents found")

        # 2. Generate prompt
        prompt = generate_prompt(
            context=context_str,
            history=history_str,
            query=user_input,
            use_cot=True
        )

        # 3. Call LLM API - temperature must be 1.0 for GPT-5
        response = complete_document_sdk(
            prompt=prompt,
            temperature=1.0  # Changed from 0.0 to 1.0
        )

        answer = extract_answer(response.get("response", ""))

        # Save conversation history
        conv_manager.add_message("User", user_input)
        conv_manager.add_message("Assistant", answer)

        # Show sources if available
        if retrieval_context:
            sources = list(set([item.get('file_name', 'unknown') for item in retrieval_context[:3]]))
            if sources:
                answer += f"\n\n📖 *Sources:* {', '.join(sources)}"

        # Send reply
        await update.message.reply_text(answer, parse_mode="Markdown")

    except Exception as e:
        print(f"Error: {e}")
        await update.message.reply_text(
            "❌ Sorry, an error occurred while processing your request. Please try again later.\n\n"
            "If the problem persists, try using /clear to clear history."
        )


def main():
    """Main function"""
    if not TELEGRAM_TOKEN:
        print("❌ Error: TELEGRAM_TOKEN not found")
        print("Please set TELEGRAM_TOKEN in .env file")
        return

    # Create application
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    # Add handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("clear", clear_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("🤖 HKBU Buddy Telegram Bot started...")
    print("📱 Search for @HKBU_buddy_bot on Telegram to start using")
    print("Press Ctrl+C to stop")

    # Start the bot
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()