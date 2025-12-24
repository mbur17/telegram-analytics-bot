import asyncio
import logging

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message

from app.config import settings
from app.db import db
from app.cache import cache
from app.llm_processor import llm_processor

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
dp = Dispatcher()


@dp.message(Command('start'))
async def cmd_start(message: Message):
    await message.answer(
        '👋 Привет! Я бот для аналитики видео.\n\n'
        'Задавай мне вопросы о видео и их статистике.\n\n'
        'Примеры вопросов:\n'
        '• Сколько всего видео есть в системе?\n'
        '• Сколько видео набрало больше 100000 просмотров?\n'
        '• На сколько просмотров выросли все видео 28 ноября 2025?\n'
        '• Сколько видео получали новые просмотры 27 ноября 2025?\n'
        'Узнать больше /help'
    )


@dp.message(Command('help'))
async def cmd_help(message: Message):
    await message.answer(
        'Помощь\n\n'
        'Я понимаю вопросы на русском языке о статистике видео.\n\n'
        'Доступные данные:\n'
        '• Количество видео\n'
        '• Просмотры, лайки, комментарии\n'
        '• Статистика по креаторам\n'
        '• Динамика изменений по дням\n\n'
        'Просто напиши свой вопрос!'
    )


@dp.message(Command('clear_cache'))
async def cmd_clear_cache(message: Message):
    await cache.clear()
    await message.answer('Кэш очищен!')


@dp.message(F.text)
async def process_query(message: Message):
    """Process natural language query."""
    user_query = message.text.strip()
    if not user_query:
        await message.answer('Пожалуйста, задайте вопрос')
        return
    logger.info(f'User query from {message.from_user.id}: {user_query}')
    await bot.send_chat_action(message.chat.id, 'typing')
    try:
        # Check cache first
        cached_result = await cache.get(user_query)
        if cached_result is not None:
            await message.answer(f'{cached_result}')
            logger.info(f'Returned cached result: {cached_result}')
            return
        # Convert natural language to SQL
        sql_query = await llm_processor.text_to_sql(user_query)
        # Execute SQL query
        result = await db.execute_raw_query(sql_query)
        # Cache the result
        await cache.set(user_query, result)
        # Send result
        await message.answer(f'{result}')
        logger.info(f'Query result: {result}')
    except ValueError as e:
        logger.error(f'Validation error: {e}')
        await message.answer(
            'Не удалось обработать запрос.\n'
            'Пожалуйста, переформулируйте вопрос.'
        )
    except Exception as e:
        logger.error(f'Error processing query: {e}', exc_info=True)
        await message.answer(
            'Произошла ошибка при обработке запроса.\n'
            'Попробуйте еще раз или переформулируйте вопрос.'
        )


async def on_startup():
    logger.info('Starting bot...')
    settings.validate()
    db.init()
    await cache.connect()
    logger.info('Bot started successfully')


async def on_shutdown():
    logger.info('Shutting down bot...')
    await db.close()
    await cache.close()
    await bot.session.close()
    logger.info('Bot shut down successfully')


async def main():
    try:
        await on_startup()
        await dp.start_polling(bot)
    except KeyboardInterrupt:
        logger.info('Received keyboard interrupt')
    except Exception as e:
        logger.error(f'Fatal error: {e}', exc_info=True)
    finally:
        await on_shutdown()


if __name__ == '__main__':
    asyncio.run(main())
