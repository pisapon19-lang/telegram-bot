"""
Telegram бот для Render.com
АВТОМАТИЧЕСКИ получает QR-код с JavaScript сайта
"""

import logging
import asyncio
from io import BytesIO
from telegram import Update, InputFile
from telegram.ext import Application, CommandHandler, ContextTypes
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os
import time

# ============ НАСТРОЙКИ ============
TOKEN = "8294429332:AAHDw84FkyZ-EOHIXynS0YdgYRkLcjI8eK4"
URL_SAYTA = "https://web.max.ru"
# ===================================

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Глобальный драйвер
driver = None

def create_driver():
    """Создание драйвера для Render.com"""
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920x1080')
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    
    driver = webdriver.Chrome(options=chrome_options)
    return driver

async def get_qr_auto():
    """Автоматическое получение QR-кода"""
    global driver
    
    try:
        if not driver:
            driver = create_driver()
            logger.info("Драйвер создан")
        
        # Загружаем страницу
        logger.info(f"Загружаю страницу: {URL_SAYTA}")
        driver.get(URL_SAYTA)
        
        # Ждем загрузки JavaScript
        logger.info("Жду загрузки JavaScript...")
        time.sleep(15)
        
        # Пробуем найти SVG (QR-код)
        logger.info("Ищу SVG элементы...")
        svg_elements = driver.find_elements(By.TAG_NAME, "svg")
        logger.info(f"Найдено SVG: {len(svg_elements)}")
        
        if svg_elements:
            # Проверяем размеры
            for svg in svg_elements:
                width = svg.get_attribute("width")
                height = svg.get_attribute("height")
                logger.info(f"SVG размер: {width}x{height}")
                
                if width and height:
                    png = svg.screenshot_as_png
                    if png:
                        img_io = BytesIO(png)
                        img_io.name = "qrcode.png"
                        logger.info("QR-код найден!")
                        return img_io
        
        # Ищем canvas
        logger.info("Ищу canvas элементы...")
        canvas_elements = driver.find_elements(By.TAG_NAME, "canvas")
        logger.info(f"Найдено canvas: {len(canvas_elements)}")
        
        if canvas_elements:
            for canvas in canvas_elements:
                png = canvas.screenshot_as_png
                if png:
                    img_io = BytesIO(png)
                    img_io.name = "qrcode.png"
                    logger.info("QR-код найден в canvas!")
                    return img_io
        
        # Если ничего не нашли, делаем скриншот всей страницы
        logger.info("Делаю полный скриншот страницы")
        screenshot = driver.get_screenshot_as_png()
        img_io = BytesIO(screenshot)
        img_io.name = "page.png"
        return img_io
        
    except Exception as e:
        logger.error(f"Ошибка в get_qr_auto: {e}")
        return None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start"""
    await update.message.reply_text(
        "👋 **Бот работает на сервере Render!**\n\n"
        "🤖 Автоматически получаю QR-код с сайта max.ru\n"
        "🔹 Напиши /qr\n"
        "🔹 Подожди 20-30 секунд\n"
        "🔹 Получи QR-код\n\n"
        "⚡️ Сервер выполняет JavaScript за тебя!",
        parse_mode='Markdown'
    )

async def qr_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /qr"""
    msg = await update.message.reply_text("🔄 **Загружаю сайт и ищу QR-код...**\n⏳ Это займет 20-30 секунд", parse_mode='Markdown')
    
    try:
        img_io = await get_qr_auto()
        
        if img_io:
            await msg.delete()
            await update.message.reply_photo(
                photo=InputFile(img_io, filename="qrcode.png"),
                caption="✅ **QR-код успешно получен!**\n\n🔹 Отправлен автоматически с сервера",
                parse_mode='Markdown'
            )
        else:
            await msg.edit_text(
                "❌ **Не удалось получить QR-код**\n\n"
                "Попробуйте еще раз через минуту.\n"
                "Если ошибка повторится - сайт временно недоступен.",
                parse_mode='Markdown'
            )
            
    except Exception as e:
        logger.error(f"Ошибка: {e}")
        await msg.edit_text(f"❌ Ошибка: {str(e)[:100]}")

async def main():
    """Главная функция"""
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("qr", qr_command))
    
    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    
    logger.info("✅ Серверный бот запущен на Render.com!")
    logger.info(f"✅ Сайт: {URL_SAYTA}")
    
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        logger.info("Останавливаю бота...")
        if driver:
            driver.quit()
        await app.stop()

if __name__ == "__main__":
    asyncio.run(main())