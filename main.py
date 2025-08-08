
import logging
import asyncio
import json
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from telegram.constants import ParseMode

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Токен бота и админы
BOT_TOKEN = "7711943797:AAEH55uTy0eokX_61OV0MuaMf71YsDENLCw"
ADMIN_IDS = [7058578094]

# Файлы для хранения данных
USERS_FILE = "users.json"
WAITING_FILE = "waiting.json"
CHATS_FILE = "chats.json"

class AnonymousBot:
    def __init__(self):
        self.users = self.load_data(USERS_FILE, {})
        self.waiting_users = self.load_data(WAITING_FILE, [])
        self.active_chats = self.load_data(CHATS_FILE, {})
        self.admin_broadcast_mode = {}  # Для отслеживания режима рассылки
        
    def load_data(self, filename, default):
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return default
    
    def save_data(self, filename, data):
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def get_main_keyboard(self):
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("🔍 Найти собеседника", callback_data="find_chat")],
            [InlineKeyboardButton("❌ Завершить диалог", callback_data="end_chat")]
        ])
    
    def get_chat_keyboard(self):
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("👤 Следующий собеседник", callback_data="next_chat")],
            [InlineKeyboardButton("❌ Завершить диалог", callback_data="end_chat")]
        ])
    
    def get_admin_keyboard(self):
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("📢 Рассылка", callback_data="admin_broadcast")],
            [InlineKeyboardButton("📊 Статистика", callback_data="admin_stats")],
            [InlineKeyboardButton("🔙 Закрыть", callback_data="admin_close")]
        ])
    
    def get_broadcast_keyboard(self):
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("📝 Текст", callback_data="broadcast_text")],
            [InlineKeyboardButton("📷 Фото", callback_data="broadcast_photo")],
            [InlineKeyboardButton("🎥 Видео", callback_data="broadcast_video")],
            [InlineKeyboardButton("🎵 Аудио", callback_data="broadcast_audio")],
            [InlineKeyboardButton("🎤 Голосовое", callback_data="broadcast_voice")],
            [InlineKeyboardButton("⭕ Кружочек", callback_data="broadcast_video_note")],
            [InlineKeyboardButton("🔙 Назад", callback_data="admin_panel")]
        ])
    
    async def setup_commands(self, application):
        """Настройка меню команд"""
        commands = [
            BotCommand("start", "🏠 Главное меню"),
            BotCommand("find", "🔍 Найти собеседника"), 
            BotCommand("next", "👤 Следующий собеседник"),
            BotCommand("end", "❌ Завершить диалог"),
            BotCommand("admin", "⚙️ Админ панель (только для админов)")
        ]
        await application.bot.set_my_commands(commands)
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = str(update.effective_user.id)
        
        # Добавляем пользователя в базу
        if user_id not in self.users:
            self.users[user_id] = {
                'username': update.effective_user.username or "Аноним",
                'first_name': update.effective_user.first_name or "Пользователь"
            }
            self.save_data(USERS_FILE, self.users)
        
        welcome_text = """🎭 <b>Добро пожаловать в анонимный чат!</b>

Здесь вы можете общаться с случайными людьми анонимно.

<b>Возможности:</b>
• Отправка текстовых сообщений
• Отправка фото и видео  
• Отправка аудио и голосовых сообщений
• Отправка видеокружочков
• Отправка стикеров и документов

<b>Команды:</b>
/find - найти собеседника
/next - следующий собеседник
/end - завершить диалог

<b>Правила:</b>
• Будьте вежливы и уважительны
• Запрещены оскорбления и спам
• Соблюдайте законы РФ

Выберите действие:"""

        await update.message.reply_text(
            welcome_text,
            reply_markup=self.get_main_keyboard(),
            parse_mode=ParseMode.HTML
        )
    
    async def find_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /find"""
        user_id = str(update.effective_user.id)
        
        # Имитируем callback query для переиспользования логики
        class FakeQuery:
            def __init__(self, user_id):
                self.from_user = type('obj', (object,), {'id': int(user_id)})
            async def edit_message_text(self, text, reply_markup=None, parse_mode=None):
                await update.message.reply_text(text, reply_markup=reply_markup, parse_mode=parse_mode)
        
        fake_query = FakeQuery(user_id)
        await self.find_chat(user_id, fake_query, context)
    
    async def next_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /next"""
        user_id = str(update.effective_user.id)
        
        class FakeQuery:
            def __init__(self, user_id):
                self.from_user = type('obj', (object,), {'id': int(user_id)})
            async def edit_message_text(self, text, reply_markup=None, parse_mode=None):
                await update.message.reply_text(text, reply_markup=reply_markup, parse_mode=parse_mode)
        
        fake_query = FakeQuery(user_id)
        await self.next_chat(user_id, fake_query, context)
    
    async def end_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /end"""
        user_id = str(update.effective_user.id)
        
        class FakeQuery:
            def __init__(self, user_id):
                self.from_user = type('obj', (object,), {'id': int(user_id)})
            async def edit_message_text(self, text, reply_markup=None, parse_mode=None):
                await update.message.reply_text(text, reply_markup=reply_markup, parse_mode=parse_mode)
        
        fake_query = FakeQuery(user_id)
        await self.end_chat(user_id, fake_query, context)
    
    async def admin_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /admin"""
        user_id = update.effective_user.id
        
        if user_id not in ADMIN_IDS:
            await update.message.reply_text("❌ У вас нет прав администратора.")
            return
        
        admin_text = """⚙️ <b>Админ панель</b>

Добро пожаловать в панель администратора!

Выберите действие:"""
        
        await update.message.reply_text(
            admin_text,
            reply_markup=self.get_admin_keyboard(),
            parse_mode=ParseMode.HTML
        )
    
    async def button_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        
        user_id = str(query.from_user.id)
        
        if query.data == "find_chat":
            await self.find_chat(user_id, query, context)
        elif query.data == "end_chat":
            await self.end_chat(user_id, query, context)
        elif query.data == "next_chat":
            await self.next_chat(user_id, query, context)
        elif query.data == "cancel_search":
            await self.cancel_search(user_id, query)
        elif query.data == "admin_panel":
            await self.admin_panel(query)
        elif query.data == "admin_broadcast":
            await self.admin_broadcast_menu(query)
        elif query.data == "admin_stats":
            await self.admin_stats_callback(query)
        elif query.data == "admin_close":
            await self.admin_close(query)
        elif query.data.startswith("broadcast_"):
            await self.handle_broadcast_type(query, context)
    
    async def find_chat(self, user_id, query, context):
        # Проверяем, не в чате ли уже пользователь
        if user_id in self.active_chats:
            await query.edit_message_text(
                "❌ Вы уже находитесь в диалоге! Завершите текущий диалог или найдите следующего собеседника.",
                reply_markup=self.get_chat_keyboard()
            )
            return
        
        # Проверяем, не в очереди ли уже
        if user_id in self.waiting_users:
            keyboard = [[InlineKeyboardButton("❌ Отменить поиск", callback_data="cancel_search")]]
            await query.edit_message_text(
                "⏳ Вы уже в очереди поиска собеседника...",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return
        
        # Ищем собеседника из очереди
        if self.waiting_users:
            partner_id = self.waiting_users.pop(0)
            
            # Проверяем, что партнер еще доступен
            if partner_id == user_id:
                if self.waiting_users:
                    partner_id = self.waiting_users.pop(0)
                else:
                    self.waiting_users.append(user_id)
                    self.save_data(WAITING_FILE, self.waiting_users)
                    keyboard = [[InlineKeyboardButton("❌ Отменить поиск", callback_data="cancel_search")]]
                    await query.edit_message_text(
                        "⏳ Ищем собеседника...\nОжидайте, пока кто-то подключится к чату.",
                        reply_markup=InlineKeyboardMarkup(keyboard)
                    )
                    return
            
            # Создаем чат
            self.active_chats[user_id] = partner_id
            self.active_chats[partner_id] = user_id
            
            self.save_data(WAITING_FILE, self.waiting_users)
            self.save_data(CHATS_FILE, self.active_chats)
            
            # Уведомляем обоих пользователей
            await query.edit_message_text(
                "✅ <b>Собеседник найден!</b>\n\n💬 Можете начинать общение!\nИспользуйте кнопки ниже для управления диалогом.",
                reply_markup=self.get_chat_keyboard(),
                parse_mode=ParseMode.HTML
            )
            
            try:
                await context.bot.send_message(
                    chat_id=int(partner_id),
                    text="✅ <b>Собеседник найден!</b>\n\n💬 Можете начинать общение!\nИспользуйте кнопки ниже для управления диалогом.",
                    reply_markup=self.get_chat_keyboard(),
                    parse_mode=ParseMode.HTML
                )
            except Exception as e:
                logger.error(f"Ошибка отправки сообщения партнеру {partner_id}: {e}")
        else:
            # Добавляем в очередь
            self.waiting_users.append(user_id)
            self.save_data(WAITING_FILE, self.waiting_users)
            
            keyboard = [[InlineKeyboardButton("❌ Отменить поиск", callback_data="cancel_search")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                "⏳ <b>Ищем собеседника...</b>\n\nОжидайте, пока кто-то подключится к чату.\nВы в очереди!",
                reply_markup=reply_markup,
                parse_mode=ParseMode.HTML
            )
    
    async def next_chat(self, user_id, query, context):
        """Найти следующего собеседника"""
        if user_id not in self.active_chats:
            await query.edit_message_text(
                "❌ Вы не находитесь в диалоге. Сначала найдите собеседника.",
                reply_markup=self.get_main_keyboard()
            )
            return
        
        partner_id = self.active_chats[user_id]
        
        # Завершаем текущий чат
        del self.active_chats[user_id]
        if partner_id in self.active_chats:
            del self.active_chats[partner_id]
        self.save_data(CHATS_FILE, self.active_chats)
        
        # Уведомляем партнера о завершении
        try:
            await context.bot.send_message(
                chat_id=int(partner_id),
                text="💔 <b>Собеседник ушел к следующему</b>\n\nВы можете найти нового собеседника.",
                reply_markup=self.get_main_keyboard(),
                parse_mode=ParseMode.HTML
            )
        except Exception as e:
            logger.error(f"Ошибка отправки сообщения партнеру {partner_id}: {e}")
        
        # Сразу ищем нового собеседника
        await self.find_chat(user_id, query, context)
    
    async def end_chat(self, user_id, query, context):
        if user_id not in self.active_chats:
            await query.edit_message_text(
                "❌ Вы не находитесь в диалоге.",
                reply_markup=self.get_main_keyboard()
            )
            return
        
        partner_id = self.active_chats[user_id]
        
        # Удаляем чат
        del self.active_chats[user_id]
        if partner_id in self.active_chats:
            del self.active_chats[partner_id]
        self.save_data(CHATS_FILE, self.active_chats)
        
        # Уведомляем обоих
        await query.edit_message_text(
            "💔 <b>Диалог завершен</b>\n\nСпасибо за общение!\nВы можете найти нового собеседника.",
            reply_markup=self.get_main_keyboard(),
            parse_mode=ParseMode.HTML
        )
        
        try:
            await context.bot.send_message(
                chat_id=int(partner_id),
                text="💔 <b>Собеседник завершил диалог</b>\n\nСпасибо за общение!\nВы можете найти нового собеседника.",
                reply_markup=self.get_main_keyboard(),
                parse_mode=ParseMode.HTML
            )
        except Exception as e:
            logger.error(f"Ошибка отправки сообщения партнеру {partner_id}: {e}")
    
    async def cancel_search(self, user_id, query):
        if user_id in self.waiting_users:
            self.waiting_users.remove(user_id)
            self.save_data(WAITING_FILE, self.waiting_users)
        
        await query.edit_message_text(
            "❌ <b>Поиск отменен</b>\n\nВы можете начать новый поиск в любое время.",
            reply_markup=self.get_main_keyboard(),
            parse_mode=ParseMode.HTML
        )
    
    async def admin_panel(self, query):
        if query.from_user.id not in ADMIN_IDS:
            await query.edit_message_text("❌ У вас нет прав администратора.")
            return
        
        admin_text = """⚙️ <b>Админ панель</b>

Добро пожаловать в панель администратора!

Выберите действие:"""
        
        await query.edit_message_text(
            admin_text,
            reply_markup=self.get_admin_keyboard(),
            parse_mode=ParseMode.HTML
        )
    
    async def admin_broadcast_menu(self, query):
        if query.from_user.id not in ADMIN_IDS:
            await query.edit_message_text("❌ У вас нет прав администратора.")
            return
        
        broadcast_text = """📢 <b>Рассылка сообщений</b>

Выберите тип контента для рассылки:

<b>Доступные типы:</b>
• Текст - обычное текстовое сообщение
• Фото - изображение с подписью
• Видео - видеофайл с подписью  
• Аудио - аудиофайл с подписью
• Голосовое - голосовое сообщение
• Кружочек - видеокружочек"""
        
        await query.edit_message_text(
            broadcast_text,
            reply_markup=self.get_broadcast_keyboard(),
            parse_mode=ParseMode.HTML
        )
    
    async def handle_broadcast_type(self, query, context):
        if query.from_user.id not in ADMIN_IDS:
            await query.edit_message_text("❌ У вас нет прав администратора.")
            return
        
        user_id = query.from_user.id
        broadcast_type = query.data.replace("broadcast_", "")
        
        self.admin_broadcast_mode[user_id] = broadcast_type
        
        type_names = {
            "text": "текстовое сообщение",
            "photo": "фото",
            "video": "видео", 
            "audio": "аудио",
            "voice": "голосовое сообщение",
            "video_note": "видеокружочек"
        }
        
        await query.edit_message_text(
            f"📤 <b>Отправьте {type_names.get(broadcast_type, 'контент')}</b>\n\n"
            f"Следующее сообщение будет разослано всем пользователям бота.\n\n"
            f"<i>Для отмены используйте команду /admin</i>",
            parse_mode=ParseMode.HTML
        )
    
    async def admin_stats_callback(self, query):
        if query.from_user.id not in ADMIN_IDS:
            await query.edit_message_text("❌ У вас нет прав администратора.")
            return
        
        total_users = len(self.users)
        waiting_count = len(self.waiting_users)
        active_chats_count = len(self.active_chats) // 2
        
        waiting_list = ", ".join(self.waiting_users[:5]) if self.waiting_users else "Нет"
        if len(self.waiting_users) > 5:
            waiting_list += f" и еще {len(self.waiting_users) - 5}..."
        
        stats_text = f"""📊 <b>Админ статистика:</b>

👥 Всего пользователей: <b>{total_users}</b>
⏳ В очереди: <b>{waiting_count}</b>
💬 Активных диалогов: <b>{active_chats_count}</b>

<b>Пользователи в очереди:</b>
<code>{waiting_list}</code>

<b>Активные чаты:</b>
{active_chats_count} пар общается"""
        
        keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="admin_panel")]]
        await query.edit_message_text(
            stats_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.HTML
        )
    
    async def admin_close(self, query):
        await query.edit_message_text(
            "⚙️ <b>Админ панель закрыта</b>",
            parse_mode=ParseMode.HTML
        )
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = str(update.effective_user.id)
        
        # Проверяем режим рассылки для админов
        if int(user_id) in self.admin_broadcast_mode:
            await self.handle_admin_broadcast(update, context)
            return
        
        # Проверяем, находится ли пользователь в активном чате
        if user_id not in self.active_chats:
            await update.message.reply_text(
                "❌ <b>Вы не находитесь в диалоге</b>\n\nНайдите собеседника для общения.",
                reply_markup=self.get_main_keyboard(),
                parse_mode=ParseMode.HTML
            )
            return
        
        partner_id = self.active_chats[user_id]
        
        try:
            # Пересылаем разные типы сообщений
            if update.message.text:
                await context.bot.send_message(
                    chat_id=int(partner_id),
                    text=f"💬 {update.message.text}"
                )
            elif update.message.photo:
                caption = "📷 Фото от собеседника"
                if update.message.caption:
                    caption += f"\n\n💬 {update.message.caption}"
                await context.bot.send_photo(
                    chat_id=int(partner_id),
                    photo=update.message.photo[-1].file_id,
                    caption=caption
                )
            elif update.message.video:
                caption = "🎥 Видео от собеседника"
                if update.message.caption:
                    caption += f"\n\n💬 {update.message.caption}"
                await context.bot.send_video(
                    chat_id=int(partner_id),
                    video=update.message.video.file_id,
                    caption=caption
                )
            elif update.message.audio:
                caption = "🎵 Аудио от собеседника"
                if update.message.caption:
                    caption += f"\n\n💬 {update.message.caption}"
                await context.bot.send_audio(
                    chat_id=int(partner_id),
                    audio=update.message.audio.file_id,
                    caption=caption
                )
            elif update.message.voice:
                await context.bot.send_voice(
                    chat_id=int(partner_id),
                    voice=update.message.voice.file_id,
                    caption="🎤 Голосовое сообщение от собеседника"
                )
            elif update.message.video_note:
                await context.bot.send_video_note(
                    chat_id=int(partner_id),
                    video_note=update.message.video_note.file_id
                )
                await context.bot.send_message(
                    chat_id=int(partner_id),
                    text="⭕ Кружочек от собеседника"
                )
            elif update.message.sticker:
                await context.bot.send_sticker(
                    chat_id=int(partner_id),
                    sticker=update.message.sticker.file_id
                )
                await context.bot.send_message(
                    chat_id=int(partner_id),
                    text="😊 Стикер от собеседника"
                )
            elif update.message.document:
                caption = "📎 Документ от собеседника"
                if update.message.caption:
                    caption += f"\n\n💬 {update.message.caption}"
                await context.bot.send_document(
                    chat_id=int(partner_id),
                    document=update.message.document.file_id,
                    caption=caption
                )
            elif update.message.animation:
                caption = "🎭 GIF от собеседника"
                if update.message.caption:
                    caption += f"\n\n💬 {update.message.caption}"
                await context.bot.send_animation(
                    chat_id=int(partner_id),
                    animation=update.message.animation.file_id,
                    caption=caption
                )
            else:
                await context.bot.send_message(
                    chat_id=int(partner_id),
                    text="📤 Сообщение от собеседника (неподдерживаемый тип)"
                )
                
        except Exception as e:
            logger.error(f"Ошибка при пересылке сообщения от {user_id} к {partner_id}: {e}")
            await update.message.reply_text(
                "❌ <b>Ошибка отправки</b>\n\nНе удалось отправить сообщение собеседнику. Возможно, он покинул чат.",
                parse_mode=ParseMode.HTML
            )
    
    async def handle_admin_broadcast(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка рассылки от админа"""
        user_id = update.effective_user.id
        broadcast_type = self.admin_broadcast_mode.get(user_id)
        
        if not broadcast_type:
            return
        
        success_count = 0
        error_count = 0
        
        status_message = await update.message.reply_text("📤 Начинаю рассылку...")
        
        for target_user_id in self.users:
            try:
                if broadcast_type == "text" and update.message.text:
                    await context.bot.send_message(
                        chat_id=int(target_user_id),
                        text=f"📢 <b>Сообщение от администрации:</b>\n\n{update.message.text}",
                        parse_mode=ParseMode.HTML
                    )
                elif broadcast_type == "photo" and update.message.photo:
                    caption = "📢 Сообщение от администрации"
                    if update.message.caption:
                        caption += f"\n\n{update.message.caption}"
                    await context.bot.send_photo(
                        chat_id=int(target_user_id),
                        photo=update.message.photo[-1].file_id,
                        caption=caption
                    )
                elif broadcast_type == "video" and update.message.video:
                    caption = "📢 Сообщение от администрации"
                    if update.message.caption:
                        caption += f"\n\n{update.message.caption}"
                    await context.bot.send_video(
                        chat_id=int(target_user_id),
                        video=update.message.video.file_id,
                        caption=caption
                    )
                elif broadcast_type == "audio" and update.message.audio:
                    caption = "📢 Сообщение от администрации"
                    if update.message.caption:
                        caption += f"\n\n{update.message.caption}"
                    await context.bot.send_audio(
                        chat_id=int(target_user_id),
                        audio=update.message.audio.file_id,
                        caption=caption
                    )
                elif broadcast_type == "voice" and update.message.voice:
                    await context.bot.send_message(
                        chat_id=int(target_user_id),
                        text="📢 <b>Голосовое сообщение от администрации:</b>",
                        parse_mode=ParseMode.HTML
                    )
                    await context.bot.send_voice(
                        chat_id=int(target_user_id),
                        voice=update.message.voice.file_id
                    )
                elif broadcast_type == "video_note" and update.message.video_note:
                    await context.bot.send_message(
                        chat_id=int(target_user_id),
                        text="📢 <b>Видеокружочек от администрации:</b>",
                        parse_mode=ParseMode.HTML
                    )
                    await context.bot.send_video_note(
                        chat_id=int(target_user_id),
                        video_note=update.message.video_note.file_id
                    )
                
                success_count += 1
                await asyncio.sleep(0.05)  # Защита от лимитов
                
            except Exception as e:
                error_count += 1
                logger.error(f"Ошибка отправки пользователю {target_user_id}: {e}")
        
        await status_message.edit_text(
            f"✅ <b>Рассылка завершена!</b>\n\n"
            f"📤 Успешно: <b>{success_count}</b>\n"
            f"❌ Ошибок: <b>{error_count}</b>",
            parse_mode=ParseMode.HTML
        )
        
        # Очищаем режим рассылки
        del self.admin_broadcast_mode[user_id]

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик ошибок"""
    logger.error(f"Ошибка: {context.error}")
    
    if update and update.effective_chat:
        try:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="❌ Произошла техническая ошибка. Попробуйте позже.",
            )
        except:
            pass

async def setup_bot():
    """Асинхронная настройка бота"""
    bot = AnonymousBot()
    
    # Создаем приложение
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Настраиваем команды
    await bot.setup_commands(application)
    
    # Добавляем обработчик ошибок
    application.add_error_handler(error_handler)
    
    # Добавляем обработчики команд
    application.add_handler(CommandHandler("start", bot.start))
    application.add_handler(CommandHandler("find", bot.find_command))
    application.add_handler(CommandHandler("next", bot.next_command))
    application.add_handler(CommandHandler("end", bot.end_command))
    application.add_handler(CommandHandler("admin", bot.admin_command))
    
    # Добавляем обработчики сообщений
    application.add_handler(CallbackQueryHandler(bot.button_handler))
    application.add_handler(MessageHandler(
        filters.ALL & ~filters.COMMAND,
        bot.handle_message
    ))
    
    return application

async def main():
    print("🤖 Запуск бота...")
    
    application = await setup_bot()
    
    # Запускаем бота
    print("✅ Бот успешно запущен!")
    await application.run_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True  # Пропускаем старые обновления
    )

if __name__ == "__main__":
    import nest_asyncio
    nest_asyncio.apply()
    
    try:
        asyncio.run(main())
    except RuntimeError as e:
        if "This event loop is already running" in str(e):
            # Для Replit используем существующий loop
            loop = asyncio.get_event_loop()
            task = loop.create_task(main())
            # Ожидаем завершения задачи
            import threading
            
            def run_task():
                try:
                    loop.run_until_complete(task)
                except:
                    pass
            
            thread = threading.Thread(target=run_task)
            thread.start()
            thread.join()
        else:
            raise
