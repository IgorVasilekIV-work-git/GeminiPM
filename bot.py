import os
import json
import logging
from pyrogram import Client, filters
from pyrogram.types import Message
import google.generativeai as genai

# Настройка логов
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Конфигурационный файл
CONFIG_FILE = "config.json"

class GeminiUserbot:
    def __init__(self):
        self.user_states = {}
        self.config = self.load_config()
        
        # Инициализация Pyrogram клиента для юзербота
        self.app = Client(
            "gemini_userbot",
            api_id=self.config.get("api_id"),
            api_hash=self.config.get("api_hash"),
            phone_number=self.config.get("phone_number")  # Ваш номер телефона
        )
        
        # Регистрация обработчиков
        self.register_handlers()
        
        # Настройка Gemini
        if self.config.get("gemini_api_key"):
            genai.configure(api_key=self.config["gemini_api_key"])

    def load_config(self):
        """Загрузка конфигурации из файла"""
        config = {
            "api_id": "",
            "api_hash": "",
            "phone_number": "",  # Например: "+79991234567"
            "gemini_api_key": "",
            "user_states": {}
        }
        
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, "r") as f:
                    loaded = json.load(f)
                    config.update(loaded)
                    # Загрузка состояний пользователей
                    self.user_states = loaded.get("user_states", {})
        except Exception as e:
            logger.error(f"Ошибка загрузки конфига: {e}")
            
        return config

    def save_config(self):
        """Сохранение конфигурации в файл"""
        try:
            self.config["user_states"] = self.user_states
            with open(CONFIG_FILE, "w") as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            logger.error(f"Ошибка сохранения конфига: {e}")

    def register_handlers(self):
        """Регистрация обработчиков команд"""
        
        @self.app.on_message(filters.command("gpt") & filters.private)
        async def gpt_command(client: Client, message: Message):
            user_id = message.from_user.id
            args = message.command
            
            if len(args) < 2:
                await message.reply("ℹ️ Используйте: `/gpt on` или `/gpt off`")
                return
                
            state = args[1].lower()
            if state == "on":
                if self.user_states.get(user_id):
                    await message.reply("✅ **Gemini уже включен!**")
                else:
                    self.user_states[user_id] = True
                    self.save_config()
                    await message.reply("🟢 **Gemini включен! Теперь я буду отвечать на ваши сообщения.**")
                    
            elif state == "off":
                if not self.user_states.get(user_id):
                    await message.reply("❌ **Gemini уже выключен!**")
                else:
                    self.user_states[user_id] = False
                    self.save_config()
                    await message.reply("🔴 **Gemini выключен! Ответы на сообщения прекращены.**")
                    
            else:
                await message.reply("❌ Неизвестная команда. Используйте: `/gpt on` или `/gpt off`")
        
        @self.app.on_message(filters.command("setkey") & filters.private)
        async def set_key(client: Client, message: Message):
            args = message.command
            if len(args) < 2:
                await message.reply("ℹ️ Укажите API ключ: `/setkey ваш_ключ`")
                return
                
            new_key = args[1]
            self.config["gemini_api_key"] = new_key
            self.save_config()
            genai.configure(api_key=new_key)
            await message.reply("🔑 **API ключ успешно обновлен!**")
        
        @self.app.on_message(filters.private & filters.incoming & filters.text & ~filters.command)
        async def handle_message(client: Client, message: Message):
            user_id = message.from_user.id
            
            # Если Gemini выключен для пользователя
            if not self.user_states.get(user_id):
                return
                
            # Если API ключ не установлен
            if not self.config.get("gemini_api_key"):
                await message.reply("❌ **API ключ не настроен! Используйте /setkey для установки ключа**")
                return
                
            try:
                # Показываем статус "печатает"
                await client.send_chat_action(message.chat.id, "typing")
                
                # Генерация ответа через Gemini
                model = genai.GenerativeModel('gemini-pro')
                response = model.generate_content(message.text)
                
                await message.reply(response.text)
            except Exception as e:
                logger.error(f"Gemini error: {e}")
                await message.reply(f"⚠️ **Ошибка генерации ответа:**\n{str(e)}")

    def run(self):
        """Запуск юзербота"""
        logger.info("Запуск юзербота Gemini AI...")
        self.app.run()

if __name__ == "__main__":
    userbot = GeminiUserbot()
    userbot.run()
