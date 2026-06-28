"""LifeOS — Webhook-based bot for Render Web Service deployment."""
from __future__ import annotations

import logging
import os
import sys
from http import HTTPStatus

from aiohttp import web
from telegram import Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    MessageHandler,
    filters,
)

from config import BOT_TOKEN
from core.scheduler import build_scheduler
from core.streak import init_db
from handlers.done import callback_handler
from handlers.report import report_handler
from handlers.start import help_handler, start_handler
from handlers.stats import stats_handler
from handlers.today import today_handler, yesterday_handler, tomorrow_handler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

# Render sets PORT env var automatically
PORT = int(os.environ.get("PORT", 8080))

# Your Render web service URL — set this as env var on Render
# Example: https://lifeos-bot.onrender.com
WEBHOOK_URL = os.environ.get("WEBHOOK_URL", "").rstrip("/")


async def text_router(update: Update, ctx) -> None:
    """Route plain-text messages to correct handler."""
    text = (update.message.text or "").strip().lower()
    if text in ("today", "aaj"):
        await today_handler(update, ctx)
    elif text in ("yesterday", "kal"):
        await yesterday_handler(update, ctx)
    elif text == "tomorrow":
        await tomorrow_handler(update, ctx)
    elif text in ("stats", "dashboard"):
        await stats_handler(update, ctx)
    elif text in ("report", "weekly"):
        await report_handler(update, ctx)
    else:
        await update.message.reply_text(
            "❓ Samaj nahi aaya\\. /help try karo\\.",
            parse_mode="MarkdownV2",
        )


def build_app() -> Application:
    """Build and return the configured PTB Application."""
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start",     start_handler))
    app.add_handler(CommandHandler("help",      help_handler))
    app.add_handler(CommandHandler("today",     today_handler))
    app.add_handler(CommandHandler("yesterday", yesterday_handler))
    app.add_handler(CommandHandler("tomorrow",  tomorrow_handler))
    app.add_handler(CommandHandler("stats",     stats_handler))
    app.add_handler(CommandHandler("report",    report_handler))
    app.add_handler(CallbackQueryHandler(callback_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_router))

    return app


async def main() -> None:
    init_db()
    logger.info("LifeOS starting in WEBHOOK mode on port %d …", PORT)

    if not WEBHOOK_URL:
        logger.error(
            "WEBHOOK_URL env var not set! "
            "Set it to your Render URL e.g. https://lifeos-bot.onrender.com"
        )
        sys.exit(1)

    ptb_app = build_app()

    # Start scheduler
    scheduler = build_scheduler(ptb_app.bot)

    async def startup(app: web.Application) -> None:
        await ptb_app.initialize()
        await ptb_app.bot.set_webhook(
            url=f"{WEBHOOK_URL}/webhook",
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True,
        )
        scheduler.start()
        logger.info("Webhook set → %s/webhook", WEBHOOK_URL)
        logger.info("Scheduler started with %d jobs.", len(scheduler.get_jobs()))

    async def shutdown(app: web.Application) -> None:
        await ptb_app.shutdown()
        scheduler.shutdown(wait=False)
        logger.info("Bot shutdown complete.")

    # ── aiohttp web server ────────────────────────────────────────────────────
    async def webhook_handler(request: web.Request) -> web.Response:
        """Receive Telegram updates via webhook."""
        try:
            data = await request.json()
            update = Update.de_json(data, ptb_app.bot)
            await ptb_app.process_update(update)
            return web.Response(status=HTTPStatus.OK)
        except Exception as exc:
            logger.error("Webhook processing error: %s", exc)
            return web.Response(status=HTTPStatus.INTERNAL_SERVER_ERROR)

    async def health_handler(request: web.Request) -> web.Response:
        """Health check — Render pings this to keep service alive."""
        return web.Response(text="LifeOS is alive 🚀", status=HTTPStatus.OK)

    web_app = web.Application()
    web_app.router.add_post("/webhook", webhook_handler)
    web_app.router.add_get("/",         health_handler)
    web_app.router.add_get("/health",   health_handler)

    web_app.on_startup.append(startup)
    web_app.on_shutdown.append(shutdown)

    runner = web.AppRunner(web_app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()

    logger.info("Server running on 0.0.0.0:%d", PORT)

    # Keep running forever
    import asyncio
    await asyncio.Event().wait()


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
