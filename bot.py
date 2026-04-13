import os
import re
import json
import asyncio
import asyncpg
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

# Database configuration
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "hkbu_bot")
DB_USER = os.getenv("DB_USER", "bot_user")
DB_PASSWORD = os.getenv("DB_PASSWORD", "bot_password")

# Database connection pool
db_pool = None

# User-specific conversation managers (fallback when DB is not available)
conversation_managers = {}


async def init_db():
    """Initialize database connection pool and create tables"""
    global db_pool
    try:
        db_pool = await asyncpg.create_pool(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            min_size=1,
            max_size=5
        )
        print("✅ Database connected")

        # Create tables if not exists
        async with db_pool.acquire() as conn:
            # Create chat logs table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS chat_logs (
                    id SERIAL PRIMARY KEY,
                    user_id VARCHAR(100) NOT NULL,
                    user_message TEXT,
                    bot_response TEXT,
                    sources TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Create user sessions table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS user_sessions (
                    user_id VARCHAR(100) PRIMARY KEY,
                    history JSONB DEFAULT '[]',
                    last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Create indexes for better performance
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_chat_logs_user_id ON chat_logs(user_id);
                CREATE INDEX IF NOT EXISTS idx_chat_logs_created_at ON chat_logs(created_at);
            """)

        print("✅ Database tables ready")
        return True
    except Exception as e:
        print(f"⚠️ Database connection failed: {e}")
        print("Bot will run without database (using in-memory storage)")
        return False


async def save_chat_log(user_id: str, user_message: str, bot_response: str, sources: str = None):
    """Save chat log to database"""
    if db_pool is None:
        return
    try:
        async with db_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO chat_logs (user_id, user_message, bot_response, sources)
                VALUES ($1, $2, $3, $4)
            """, user_id, user_message, bot_response, sources)
    except Exception as e:
        print(f"Failed to save chat log: {e}")


async def save_session(user_id: str, history: list):
    """Save user session to database"""
    if db_pool is None:
        return
    try:
        async with db_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO user_sessions (user_id, history, last_active)
                VALUES ($1, $2, CURRENT_TIMESTAMP)
                ON CONFLICT (user_id) 
                DO UPDATE SET history = $2, last_active = CURRENT_TIMESTAMP
            """, user_id, json.dumps(history))
    except Exception as e:
        print(f"Failed to save session: {e}")


async def load_session(user_id: str):
    """Load user session from database"""
    if db_pool is None:
        return None
    try:
        async with db_pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT history FROM user_sessions WHERE user_id = $1
            """, user_id)
            if row:
                return json.loads(row["history"])
    except Exception as e:
        print(f"Failed to load session: {e}")
    return None


async def start(update: Update, context):
    """Handle /start command"""
    user_id = str(update.effective_user.id)

    # Initialize session in database
    await save_session(user_id, [])

    await update.message.reply_text(
        "🎓 **HKBU Buddy** is online!\n\n"
        "I am your HKBU campus study assistant. I can help you with:\n"
        "📚 Course information\n"
        "🏫 Campus facilities\n"
        "📅 Semester schedule\n\n"
        "Just send me your questions!\n\n"
        "**Commands:**\n"
        "/clear - Clear conversation history\n"
        "/help - Show help\n"
        "/stats - Show your usage statistics",
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
        "/stats - Show your usage statistics\n"
        "/help - Show this help\n\n"
        "**Example questions:**\n"
        "• What courses does Computer Science department offer?\n"
        "• When does the library open?\n"
        "• When is the final exam week?",
        parse_mode="Markdown"
    )


async def stats_command(update: Update, context):
    """Handle /stats command - show user statistics"""
    user_id = str(update.effective_user.id)

    if db_pool is None:
        await update.message.reply_text("📊 Database is not available. No statistics to show.")
        return

    try:
        async with db_pool.acquire() as conn:
            # Get total messages count
            row = await conn.fetchrow("""
                SELECT COUNT(*) as total_messages FROM chat_logs WHERE user_id = $1
            """, user_id)
            total_messages = row["total_messages"] if row else 0

            # Get today's messages
            row = await conn.fetchrow("""
                SELECT COUNT(*) as today_messages FROM chat_logs 
                WHERE user_id = $1 AND DATE(created_at) = CURRENT_DATE
            """, user_id)
            today_messages = row["today_messages"] if row else 0

        await update.message.reply_text(
            f"📊 **Your Statistics**\n\n"
            f"💬 Total messages: {total_messages}\n"
            f"📅 Messages today: {today_messages}\n\n"
            f"Keep asking questions about HKBU! 🎓",
            parse_mode="Markdown"
        )
    except Exception as e:
        print(f"Failed to get stats: {e}")
        await update.message.reply_text("❌ Failed to retrieve statistics.")


async def clear_command(update: Update, context):
    """Handle /clear command"""
    user_id = str(update.effective_user.id)

    # Clear in-memory conversation manager
    if user_id in conversation_managers:
        conversation_managers[user_id].clear_history()
        del conversation_managers[user_id]

    # Clear database session
    await save_session(user_id, [])

    await update.message.reply_text("🧹 Conversation history cleared!")


async def handle_message(update: Update, context):
    """Handle user messages"""
    user_id = str(update.effective_user.id)
    user_input = update.message.text.strip()

    if not user_input:
        return

    # Send "typing" indicator
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    try:
        # Try to load session from database first
        db_history = await load_session(user_id)

        # Get user's conversation manager
        if user_id not in conversation_managers:
            conversation_managers[user_id] = ConversationManager()
            # Restore history from database if available
            if db_history:
                for msg in db_history:
                    conversation_managers[user_id].add_message(msg.get("role", "User"), msg.get("content", ""))

        conv_manager = conversation_managers[user_id]
        history_str = conv_manager.get_history_string()

        # Check if it's a greeting - but NOT if it contains course-related keywords
        course_keywords = ['comp', 'course', 'class', 'lecture', 'professor', 'teaching', 'instructor', 'what is',
                           'tell me about']
        is_real_greeting = is_greeting(user_input)

        # Don't treat as greeting if it contains course-related terms
        if is_real_greeting and not any(keyword in user_input.lower() for keyword in course_keywords):
            answer = "Hello! How can I assist you with your studies today?"
            conv_manager.add_message("User", user_input)
            conv_manager.add_message("Assistant", answer)

            # Save to database
            await save_session(user_id, conv_manager.history)
            await save_chat_log(user_id, user_input, answer, None)

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
        sources = []
        if retrieval_context:
            context_str = "\n\n".join([
                f"[Source: {item.get('file_name', 'unknown')}]\n{item.get('content', '')}"
                for item in retrieval_context
            ])
            sources = list(set([item.get('file_name', 'unknown') for item in retrieval_context[:3]]))
            print(f"📚 Retrieved {len(retrieval_context)} relevant chunks")
        else:
            context_str = "No relevant documents found."
            print("📚 No relevant documents found")

        # 2. Generate prompt - add instruction for when no context found
        if not retrieval_context:
            prompt = f"""You are a helpful HKBU study assistant. The user asked a question but no relevant documents were found in the knowledge base.

Please respond with a message like:
"Sorry, I couldn't find any information about '{user_input}' in the available documents. Please try asking about HKBU courses, professors, or campus facilities."

Conversation History: {history_str}
User: {user_input}

Assistant:"""
        else:
            prompt = generate_prompt(
                context=context_str,
                history=history_str,
                query=user_input,
                use_cot=True
            )

        # 3. Call LLM API with timeout
        try:
            response = await asyncio.wait_for(
                asyncio.to_thread(complete_document_sdk, prompt=prompt, temperature=1.0),
                timeout=25.0
            )
        except asyncio.TimeoutError:
            await update.message.reply_text(
                "⏰ The request is taking too long. Please try again in a moment."
            )
            return

        answer = extract_answer(response.get("response", ""))

        # If answer is empty or too short, provide fallback
        if not answer or len(answer) < 10:
            answer = f"Sorry, I couldn't find specific information about '{user_input}'. Please try rephrasing your question or ask about HKBU courses and professors."

        # Save conversation history
        conv_manager.add_message("User", user_input)
        conv_manager.add_message("Assistant", answer)

        # Save to database
        await save_session(user_id, conv_manager.history)
        await save_chat_log(user_id, user_input, answer, ", ".join(sources) if sources else None)

        # Show sources if available
        if sources:
            answer += f"\n\n📖 *Sources:* {', '.join(sources)}"

        # Send reply - try Markdown first, fallback to plain text
        try:
            await update.message.reply_text(answer, parse_mode="Markdown")
        except Exception:
            await update.message.reply_text(answer)

    except Exception as e:
        print(f"Error: {e}")
        await update.message.reply_text(
            "❌ Sorry, an error occurred while processing your request. Please try again later.\n\n"
            "If the problem persists, try using /clear to clear history."
        )


def main():
    """Main function - fixed asyncio issue"""
    if not TELEGRAM_TOKEN:
        print("❌ Error: TELEGRAM_TOKEN not found")
        print("Please set TELEGRAM_TOKEN in .env file")
        return

    # Initialize database (run async function)
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(init_db())
    except Exception as e:
        print(f"Database init warning: {e}")

    # Create application
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    # Add handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("clear", clear_command))
    app.add_handler(CommandHandler("stats", stats_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("🤖 HKBU Buddy Telegram Bot started...")
    print("📱 Search for @HKBU_buddy_bot on Telegram to start using")
    print("Press Ctrl+C to stop")

    # Start the bot (this is blocking)
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()