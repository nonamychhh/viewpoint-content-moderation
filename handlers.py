from aiogram import Bot
import asyncio
from aiogram.dispatcher.router import Router
from aiogram.types import Message, User, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery, Chat
from load_config import load_config, save_config
from aiogram.filters import Command, StateFilter
from aiogram import F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import os
import logging
import json
from typing import Dict, Union, Any, List, Optional

router = Router()

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Создаем форматтер
formatter = logging.Formatter('[%(asctime)s] %(levelname)s: %(message)s')

# Консольный вывод
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)

# Файловый вывод
file_handler = logging.FileHandler("bot.log", encoding="utf-8")
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# Устанавливаем уровень для шумных логгеров
logging.getLogger("aiohttp").setLevel(logging.WARNING)
logging.getLogger("asyncio").setLevel(logging.WARNING)
logging.getLogger("aiogram.event").setLevel(logging.WARNING)
logging.getLogger("aiogram.dispatcher").setLevel(logging.INFO)

class ConfigStates(StatesGroup):
    MAIN_MENU = State()
    GROUP_SELECTION = State()
    TOPIC_SELECTION = State()
    TOPIC_OPTIONS = State()
    CONTENT_CONFIG = State()
    FORWARD_CONFIG = State()
    HASHTAGS_INPUT = State()
    DELETE_CONFIRM = State()
    DOMAINS_INPUT = State()

# Настройки топика
DEFAULT_TOPIC_SETTINGS = {
    "name": "",
    "photo": False,
    "video": False,
    "text": False,
    "audio": False,
    "voice": False,
    "video_voice": False,
    "polls": False,
    "files": False,
    "sticker": False,
    "gif": False,
    "allowed_hashtags": [],
    "forward_to_topics": [],
    "content_tracking": False,
    "is_general": False,
    "forward_mentions": False
}

bot_data = load_config()
group_settings = bot_data.get("group_settings", {})
token = bot_data.get("api_token")
# =============================================
# Функции клавиатур
# =============================================
def main_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Группы", callback_data="main_groups")],
        [InlineKeyboardButton(text="Команды", callback_data="commands")]
    ])

def groups_menu_keyboard(allowed_groups: Optional[Dict] = None) -> InlineKeyboardMarkup:
    buttons = []
    groups = allowed_groups if allowed_groups is not None else group_settings
    
    for gid, info in groups.items():
        group_name = info.get("name", gid)
        buttons.append([InlineKeyboardButton(
            text=group_name, 
            callback_data=f"group_{gid}"
        )])
    
    buttons.append([InlineKeyboardButton(
        text="🔙 Назад", 
        callback_data="main_menu"
    )])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def group_topics_keyboard(group_id: str) -> InlineKeyboardMarkup:
    buttons = []
    topics = group_settings.get(group_id, {}).get("topics", {})
    
    for tid, conf in topics.items():
        buttons.append([InlineKeyboardButton(
            text=conf.get("name", tid), 
            callback_data=f"topic_{tid}"
        )])
    
    if topics:
        buttons.append([InlineKeyboardButton(
            text="Удалить топик", 
            callback_data=f"del_topics_{group_id}"
        )])
    
    buttons.append([InlineKeyboardButton(
        text="🔙 Назад", 
        callback_data="main_groups"
    )])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def topic_options_keyboard(topic_id: str, group_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Настройка контента", callback_data="manual_config")],
        [InlineKeyboardButton(text="Настроить пересылку", callback_data="configure_forward")],
        [InlineKeyboardButton(text="Редактировать хэштеги", callback_data="edit_hashtags")],
        [InlineKeyboardButton(text="Управление ссылками", callback_data="edit_links")],
        [InlineKeyboardButton(text="Дополнительные настройки", callback_data="advanced_settings")],
        [InlineKeyboardButton(text="Удалить топик", callback_data=f"confirm_delete_{topic_id}_{group_id}")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data=f"group_{group_id}")]
    ])

def delete_topic_menu_keyboard(group_id: str) -> InlineKeyboardMarkup:
    buttons = []
    topics = group_settings.get(group_id, {}).get("topics", {})
    
    for tid, conf in topics.items():
        buttons.append([InlineKeyboardButton(
            text=conf.get("name", tid), 
            callback_data=f"delete_topic_{tid}_{group_id}"
        )])
    
    buttons.append([InlineKeyboardButton(
        text="🔙 Назад", 
        callback_data=f"group_{group_id}"
    )])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def advanced_settings_keyboard(topic: Dict) -> InlineKeyboardMarkup:
    options = [
        ("content_tracking", "Отслеживание контента"),
        ("is_general", "General"),
        ("forward_mentions", "Упоминания")
    ]
    buttons = []
    for key, label in options:
        status = "✅" if topic.get(key, False) else "❌"
        buttons.append([InlineKeyboardButton(
            text=f"{label}: {status}", 
            callback_data=f"toggle_{key}"
        )])
    
    buttons.append([InlineKeyboardButton(
        text="🔙 Назад", 
        callback_data="back_to_topic_options"
    )])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def content_settings_keyboard(topic: Dict) -> InlineKeyboardMarkup:
    options = [
        ("photo", "Фото"),
        ("video", "Видео"),
        ("text", "Текст"),
        ("audio", "Аудио"),
        ("voice", "Голосовые"),
        ("video_voice", "Видео-голосовые"),
        ("polls", "Голосования"),
        ("files", "Файлы"),
        ("sticker", "Стикеры"),
        ("gif", "Gif")
        
    ]
    
    buttons = []
    for key, label in options:
        status = "✅" if topic.get(key, False) else "❌"
        buttons.append([InlineKeyboardButton(
            text=f"{label}: {status}", 
            callback_data=f"toggle_{key}"
        )])
    
    buttons.append([InlineKeyboardButton(
        text="🔙 Назад", 
        callback_data="back_to_topic_options"
    )])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def forward_settings_keyboard(
    group_id: str, 
    current_topic_id: str, 
    current_selection: List[str]
) -> InlineKeyboardMarkup:
    buttons = []
    topics = group_settings.get(group_id, {}).get("topics", {})
    
    for tid, conf in topics.items():
        if tid == current_topic_id:
            continue
            
        sel = "✅" if tid in current_selection else "❌"
        buttons.append([InlineKeyboardButton(
            text=f"{conf.get('name', tid)} {sel}", 
            callback_data=f"forward_toggle_{tid}"
        )])
    
    buttons.append([InlineKeyboardButton(
        text="🔙 Назад", 
        callback_data="back_to_topic_options"
    )])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def hashtags_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="Изменить хэштеги", 
            callback_data="change_hashtags"
        )],
        [InlineKeyboardButton(
            text="🔙 Назад", 
            callback_data="back_to_topic_options"
        )]
    ])

def delete_confirmation_keyboard(topic_id: str, group_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="Да, удалить", 
                callback_data=f"yes_delete_{topic_id}_{group_id}"
            ),
            InlineKeyboardButton(
                text="Отмена", 
                callback_data=f"group_{group_id}"
            )
        ]
    ])

def back_to_main_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад", callback_data="main_menu")]
    ])

def back_to_hashtags_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад", callback_data="edit_hashtags")]
    ])

# =============================================
# Вспомогательные функции
# =============================================
async def check_admin(event: Union[Message, CallbackQuery], bot: Bot) -> bool:
    user: User = event.from_user
    chat: Chat = event.chat if isinstance(event, Message) else event.message.chat
    
    if chat.type == "private":
        return True

    try:
        admins = await bot.get_chat_administrators(chat.id)
        return any(admin.user.id == user.id for admin in admins)
    except Exception as e:
        logging.error(f"Ошибка проверки администратора в чате {chat.id}: {e}")
        return False

def is_content_allowed(message: Message, settings: Dict[str, Any]) -> bool:
    print(settings)
    content_types = {
        'photo': 'photo',
        'video': 'video',
        'audio': 'audio',
        'voice': 'voice',
        'video_note': 'video_voice',
        'poll': 'polls',
        'document': 'files',
        'sticker': 'sticker',
        'animation': 'gif'
    }
    
    for attr, setting_key in content_types.items():
        logging.info(f"Идет проверка {attr}")
        if getattr(message, attr, None):
            logging.info(f"{attr} прошел проверку")
            return settings.get(setting_key, True)
    
    text_content = None
    if message.text:
        logging.info("text")
        text_content = message.text
    elif message.caption:
        text_content = message.caption
    
    if text_content:
        if settings.get("text",True):
            return True
        
        if any(tag in text_content for tag in settings.get("allowed_hashtags", [])):
            logging.info("Найден вл хештег")
            return True
        
        if any(domain in text_content for domain in settings.get("allowed_links", [])):
            logging.info("Найден вл сайт")
            return True
    
    return False

async def handle_tag_settings(
    callback: CallbackQuery, 
    state: FSMContext, 
    tag_type: str,  # 'hashtags' или 'domains'
    title: str,     # Заголовок меню
    input_prompt: str,  # Подсказка при вводе
    empty_message: str  # Сообщение при отсутствии тегов
):
    data = await state.get_data()
    group_id = data.get("selected_group")
    topic_id = data.get("selected_topic")
    
    if not group_id or not topic_id:
        await callback.answer("Ошибка: топик не выбран", show_alert=True)
        return
    
    topic = group_settings[group_id]["topics"][topic_id]
    current_tags = topic.get(f"allowed_{tag_type}", [])
    
    text = f"{title}:\n```\n" + " ".join(current_tags) + "\n```" if current_tags else empty_message
    
    # Создаем клавиатуру динамически
    buttons = [
        [InlineKeyboardButton(text="Изменить", callback_data=f"change_{tag_type}")],
        [InlineKeyboardButton(text="Назад", callback_data="back_to_topic_options")]
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    
    await callback.message.edit_text(
        text,
        parse_mode="Markdown",
        reply_markup=keyboard
    )

# =============================================
# Обработчики команд
# =============================================
@router.message(Command("botconfig"))
async def cmd_botconfig(message: Message, bot: Bot, state: FSMContext):
    user = message.from_user
    chat = message.chat
    
    await state.update_data(user_id=user.id, chat_type=chat.type)
    
    if chat.type == "private":
        allowed_groups = {}
        for group_id, group_data in group_settings.items():
            try:
                if "admins" not in group_data:
                    admins = await bot.get_chat_administrators(int(group_id))
                    group_data["admins"] = [admin.user.id for admin in admins]
                    save_config({"api_token":token,"group_settings": group_settings})
                
                if user.id in group_data.get("admins", []):
                    allowed_groups[group_id] = group_data
            except Exception as e:
                logging.error(f"Ошибка группы {group_id}: {e}")
        
        if not allowed_groups:
            await message.answer("⚠️ Вы не администратор ни в одной группе.")
            await state.clear()
            return
        
        await state.update_data(allowed_groups=allowed_groups)
        await message.answer(
            "Выберите группу для настройки:",
            reply_markup=groups_menu_keyboard(allowed_groups)
        )
        await state.set_state(ConfigStates.GROUP_SELECTION)
    else:
        if not await check_admin(message, bot):
            await message.answer("⚠️ Только администраторы могут использовать эту команду.")
            await state.clear()
            return
        
        group_id = str(chat.id)
        
        if group_id not in group_settings:
            group_settings[group_id] = {
                "name": chat.title or group_id,
                "topics": {}
            }
            try:
                admins = await bot.get_chat_administrators(chat.id)
                group_settings[group_id]["admins"] = [admin.user.id for admin in admins]
                save_config({"api_token":token,"group_settings": group_settings})
            except Exception as e:
                logging.error(f"Ошибка получения администраторов: {e}")
        
        await state.update_data(selected_group=group_id)
        
        try:
            await bot.send_message(
                chat_id=user.id,
                text="Выберите раздел:",
                reply_markup=main_menu_keyboard()
            )
            await message.answer("✅ Конфигурация отправлена в ЛС.")
            await state.set_state(ConfigStates.MAIN_MENU)
        except Exception as e:
            logging.error(f"Ошибка отправки ЛС: {e}")
            await message.answer("⚠️ Начните диалог с ботом в ЛС!")
            await state.clear()

@router.message(Command("addtopic"))
async def cmd_addtopic(message: Message, bot: Bot):
    if message.chat.type == "private":
        await message.answer("Эта команда доступна только в группах.")
        return
    
    if not await check_admin(message, bot):
        await message.answer("⚠️ Только администраторы могут использовать эту команду.")
        return
    
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("Используйте: /addtopic <название топика>")
        return
    
    topic_name = parts[1].strip()
    group_id = str(message.chat.id)
    group_title = message.chat.title or group_id
    
    if group_id not in group_settings:
        group_settings[group_id] = {"name": group_title, "topics": {}}
    
    topic_id = str(message.message_thread_id) if message.message_thread_id else "0"
    
    if topic_id in group_settings[group_id].get("topics", {}):
        await message.answer("⚠️ Топик с таким ID уже существует.")
        return
    
    new_topic = dict(DEFAULT_TOPIC_SETTINGS)
    new_topic["name"] = topic_name
    group_settings[group_id].setdefault("topics", {})[topic_id] = new_topic
    save_config({"api_token":token,"group_settings": group_settings})
    
    await message.answer(f"✅ Топик «{topic_name}» добавлен в группу «{group_settings[group_id]['name']}»")
    
    try:
        await bot.send_message(
            chat_id=message.from_user.id,
            text=f"Топик «{topic_name}» добавлен в группу «{group_settings[group_id]['name']}»"
        )
    except Exception:
        pass

@router.message(Command("deltopic"))
async def cmd_deltopic(message: Message, bot: Bot):
    if message.chat.type == "private":
        await message.answer("Эта команда доступна только в группах.")
        return
    
    if not await check_admin(message, bot):
        await message.answer("⚠️ Только администраторы могут использовать эту команду.")
        return
    
    group_id = str(message.chat.id)
    
    if group_id not in group_settings or not group_settings[group_id].get("topics"):
        await message.answer("⚠️ В этой группе нет топиков для удаления.")
        return
    
    try:
        await bot.send_message(
            chat_id=message.from_user.id,
            text="Выберите топик для удаления:",
            reply_markup=delete_topic_menu_keyboard(group_id)
        )
        await message.answer("✅ Меню удаления топика отправлено в ЛС.")
    except Exception:
        await message.answer("⚠️ Начните диалог с ботом в ЛС!")

@router.message(Command("help"))
async def show_commands(message: Message):
    commands_text = (
        "ℹ️ Доступные команды:\n\n"
        "/botconfig - Основное меню настроек\n"
        "/addtopic <название> - Добавить новый топик\n"
        "/deltopic - Удалить топик\n"
        "/help - Показать справку\n\n"
        "🔧 Также доступны команды через кнопки в меню."
    )
    await message.answer(commands_text, reply_markup=back_to_main_keyboard())

# =============================================
# Обработчики callback-запросов
# =============================================
@router.callback_query(F.data.startswith("group_"), ConfigStates.GROUP_SELECTION)
async def group_selected(callback: CallbackQuery, state: FSMContext):
    group_id = callback.data.split("_", 1)[1]
    data = await state.get_data()
    allowed_groups = data.get("allowed_groups", {})
    
    if group_id not in allowed_groups:
        await callback.answer("⚠️ Доступ запрещен", show_alert=True)
        return
    
    await state.update_data(selected_group=group_id)
    
    await callback.message.edit_text(
        f"Группа: {allowed_groups[group_id]['name']}\nСписок топиков:",
        reply_markup=group_topics_keyboard(group_id)
    )
    await state.set_state(ConfigStates.TOPIC_SELECTION)

@router.callback_query(F.data.startswith("topic_"), ConfigStates.TOPIC_SELECTION)
async def topic_selected(callback: CallbackQuery, state: FSMContext):
    topic_id = callback.data.split("_", 1)[1]
    data = await state.get_data()
    group_id = data.get("selected_group")
    
    if not group_id:
        await callback.answer("Ошибка: группа не выбрана", show_alert=True)
        return
    
    await state.update_data(selected_topic=topic_id)
    
    topic = group_settings[group_id]["topics"].get(topic_id, {})
    topic_name = topic.get("name", topic_id)
    
    await callback.message.edit_text(
        f"Настройки топика: {topic_name}",
        reply_markup=topic_options_keyboard(topic_id, group_id)
    )
    await state.set_state(ConfigStates.TOPIC_OPTIONS)

@router.callback_query(F.data == "back_to_topic_options")
async def back_to_topic_options(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    group_id = data.get("selected_group")
    topic_id = data.get("selected_topic")
    
    if not group_id or not topic_id:
        await callback.answer("Ошибка: топик не выбран", show_alert=True)
        return
    
    topic = group_settings[group_id]["topics"].get(topic_id, {})
    topic_name = topic.get("name", topic_id)
    
    await callback.message.edit_text(
        f"Настройки топика: {topic_name}",
        reply_markup=topic_options_keyboard(topic_id, group_id)
    )
    await state.set_state(ConfigStates.TOPIC_OPTIONS)

@router.callback_query(F.data == "manual_config", ConfigStates.TOPIC_OPTIONS)
async def content_settings_menu(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    group_id = data.get("selected_group")
    topic_id = data.get("selected_topic")
    
    if not group_id or not topic_id:
        await callback.answer("Ошибка: топик не выбран", show_alert=True)
        return
    
    topic = group_settings[group_id]["topics"][topic_id]
    
    await callback.message.edit_text(
        "Настройка разрешенного контента:",
        reply_markup=content_settings_keyboard(topic)
    )
    await state.set_state(ConfigStates.CONTENT_CONFIG)

@router.callback_query(F.data == "advanced_settings", ConfigStates.TOPIC_OPTIONS)
async def show_advanced_settings(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    group_id = data.get("selected_group")
    topic_id = data.get("selected_topic")
    
    topic = group_settings[group_id]["topics"][topic_id]
    keyboard = advanced_settings_keyboard(topic)
    
    await callback.message.edit_text(
        "⚙️ Дополнительные настройки топика:",
        reply_markup=keyboard
    )

@router.callback_query(F.data.startswith("toggle_"), ConfigStates.TOPIC_OPTIONS)
async def toggle_content_setting(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    group_id = data.get("selected_group")
    topic_id = data.get("selected_topic")
    setting = "_".join(callback.data.split("_")[1:])
    
    # Переключаем настройку
    current = group_settings[group_id]["topics"][topic_id].get(setting, False)
    group_settings[group_id]["topics"][topic_id][setting] = not current
    save_config({"api_token": token, "group_settings": group_settings})
    
    # Определяем какое меню нужно показать
    if setting in ["content_tracking", "is_general", "forward_mentions"]:
        keyboard = advanced_settings_keyboard(group_settings[group_id]["topics"][topic_id])
        text = "⚙️ Дополнительные настройки топика:"
    else:
        keyboard = content_settings_keyboard(group_settings[group_id]["topics"][topic_id])
        text = "⚙️ Настройки контента:"
    
    await callback.message.edit_text(text, reply_markup=keyboard)

@router.callback_query(F.data == "configure_forward", ConfigStates.TOPIC_OPTIONS)
async def forward_settings_menu(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    group_id = data.get("selected_group")
    topic_id = data.get("selected_topic")
    
    if not group_id or not topic_id:
        await callback.answer("Ошибка: топик не выбран", show_alert=True)
        return
    
    topic = group_settings[group_id]["topics"][topic_id]
    current_selection = topic.get("forward_to_topics", [])
    
    await callback.message.edit_text(
        "Выберите топики для пересылки:",
        reply_markup=forward_settings_keyboard(group_id, topic_id, current_selection)
    )
    await state.set_state(ConfigStates.FORWARD_CONFIG)

@router.callback_query(F.data.startswith("forward_toggle_"), ConfigStates.FORWARD_CONFIG)
async def toggle_forward_topic(callback: CallbackQuery, state: FSMContext):
    target_id = callback.data.split("_", 2)[2]
    data = await state.get_data()
    group_id = data.get("selected_group")
    topic_id = data.get("selected_topic")
    
    if not group_id or not topic_id:
        await callback.answer("Ошибка: топик не выбран", show_alert=True)
        return
    
    topic = group_settings[group_id]["topics"][topic_id]
    current = topic.get("forward_to_topics", [])
    
    if target_id in current:
        current.remove(target_id)
    else:
        current.append(target_id)
    
    topic["forward_to_topics"] = current
    save_config({"api_token":token,"group_settings": group_settings})
    
    await callback.message.edit_reply_markup(
        reply_markup=forward_settings_keyboard(group_id, topic_id, current)
    )

@router.callback_query(F.data == "edit_hashtags", ConfigStates.TOPIC_OPTIONS)
async def hashtags_settings_menu(callback: CallbackQuery, state: FSMContext):
    await handle_tag_settings(
        callback, state,
        tag_type="hashtags",
        title="Текущие хэштеги",
        input_prompt="Введите хэштеги через пробел (например: #обход #голосование):",
        empty_message="Хэштеги не добавлены"
    )

@router.callback_query(F.data == "change_hashtags", ConfigStates.TOPIC_OPTIONS)
async def request_hashtags_input(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "Введите хэштеги через пробел (например: #обход #голосование):",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="Назад", callback_data="edit_hashtags")]]
        )
    )
    await state.set_state(ConfigStates.HASHTAGS_INPUT)

# Обработчики для доменов
@router.callback_query(F.data == "edit_links", ConfigStates.TOPIC_OPTIONS)
async def domains_settings_menu(callback: CallbackQuery, state: FSMContext):
    await handle_tag_settings(
        callback, state,
        tag_type="links",
        title="Текущие разрешенные ссылки",
        input_prompt="Введите ссылки через пробел (например: example.com google.com):",
        empty_message="Ссылки не добавлены"
    )

@router.callback_query(F.data == "change_links", ConfigStates.TOPIC_OPTIONS)
async def request_domains_input(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "Введите домены через пробел (например: example.com google.com):",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="Назад", callback_data="edit_links")]]
        )
    )
    await state.set_state(ConfigStates.DOMAINS_INPUT)

# Общий обработчик для сохранения тегов
@router.message(StateFilter(ConfigStates.HASHTAGS_INPUT, ConfigStates.DOMAINS_INPUT))
async def save_tags(message: Message, state: FSMContext):
    data = await state.get_data()
    group_id = data.get("selected_group")
    topic_id = data.get("selected_topic")
    
    if not group_id or not topic_id:
        await message.answer("Ошибка: топик не выбран")
        await state.clear()
        return
    
    # Определяем тип тегов по текущему состоянию
    tag_type = "hashtags" if await state.get_state() == ConfigStates.HASHTAGS_INPUT else "links"
    back_command = f"edit_{tag_type}"
    
    new_tags = message.text.strip().split()
    group_settings[group_id]["topics"][topic_id][f"allowed_{tag_type}"] = new_tags
    save_config({"api_token": token, "group_settings": group_settings})
    
    text = "Хэштеги" if tag_type == "hashtags" else "Ссылки"
    text += " обновлены:\n```\n" + " ".join(new_tags) + "\n```"
    
    await message.answer(
        text,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="Назад", callback_data=back_command)]]
        )
    )
    await state.set_state(ConfigStates.TOPIC_OPTIONS)

@router.callback_query(F.data.startswith("confirm_delete_"), ConfigStates.TOPIC_OPTIONS)
async def confirm_topic_delete(callback: CallbackQuery):
    parts = callback.data.split("_")
    topic_id = parts[2]
    group_id = parts[3]
    
    if group_id not in group_settings or topic_id not in group_settings[group_id].get("topics", {}):
        await callback.answer("⚠️ Топик не найден", show_alert=True)
        return
    
    topic_name = group_settings[group_id]["topics"][topic_id].get("name", topic_id)
    
    await callback.message.edit_text(
        f"Вы уверены, что хотите удалить топик «{topic_name}»?",
        reply_markup=delete_confirmation_keyboard(topic_id, group_id)
    )

@router.callback_query(F.data.startswith("yes_delete_"))
async def delete_topic(callback: CallbackQuery):
    parts = callback.data.split("_")
    topic_id = parts[2]
    group_id = parts[3]
    
    if group_id not in group_settings or topic_id not in group_settings[group_id].get("topics", {}):
        await callback.answer("⚠️ Топик не найден", show_alert=True)
        return
    
    topic_name = group_settings[group_id]["topics"][topic_id].get("name", topic_id)
    group_name = group_settings[group_id].get("name", group_id)
    
    del group_settings[group_id]["topics"][topic_id]
    save_config({"api_token":token,"group_settings": group_settings})
    
    await callback.message.edit_text(
        f"🗑️ Топик «{topic_name}» удалён из группы «{group_name}».",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Назад", callback_data=f"group_{group_id}")]
        ])
    )

@router.callback_query(F.data == "main_menu")
async def back_to_main_menu(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "Главное меню:",
        reply_markup=main_menu_keyboard()
    )
    await state.set_state(ConfigStates.MAIN_MENU)

@router.callback_query(F.data == "main_groups")
async def back_to_groups(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    allowed_groups = data.get("allowed_groups", {})
    
    if not allowed_groups:
        await callback.answer("⚠️ Данные о группах недоступны", show_alert=True)
        return
    
    await callback.message.edit_text(
        "Выберите группу для настройки:",
        reply_markup=groups_menu_keyboard(allowed_groups)
    )
    await state.set_state(ConfigStates.GROUP_SELECTION)

@router.callback_query(F.data == "commands")
async def show_commands_callback(callback: CallbackQuery):
    commands_text = (
        "ℹ️ Доступные команды:\n\n"
        "/botconfig - Основное меню настроек\n"
        "/addtopic <название> - Добавить новый топик\n"
        "/deltopic - Удалить топик\n"
        "/help - Показать справку\n\n"
        "🔧 Также доступны команды через кнопки в меню."
    )
    await callback.message.edit_text(
        commands_text,
        reply_markup=back_to_main_keyboard()
    )

# =============================================
# Обработчики сообщений
# =============================================
@router.message(
    F.chat.type.in_(["group","supergroup"]) 
)
async def check_content(message: Message, bot: Bot):
    if not message:
        return
    
    group_id = str(message.chat.id)
    
    # Определяем, является ли это сообщение ответом в General топике
    is_general_reply = (
        message.is_topic_message is None and
        message.reply_to_message is not None
    )
    # Определяем ID топика с учетом особенностей General
    if is_general_reply:
        topic_id = "default"
    else:
        topic_id = str(message.message_thread_id) if message.message_thread_id is not None else "default"
    
    # Получаем настройки для текущего топика
    settings = group_settings.get(group_id, {}).get("topics", {}).get(topic_id)
    if not settings:
        if is_general_reply:
            settings = group_settings.get(group_id, {}).get("topics", {}).get("default")
            if not settings:
                return
        else:
            return

    # Остальной код остается без изменений...
    logging.info(f"Обработка сообщения в группе {group_id}, топик {topic_id}")
    settings["message_count"] = settings.get("message_count", 0) + 1
    save_config({"api_token": token, "group_settings": group_settings})

    if not settings.get("content_tracking", False):
        return

    if is_content_allowed(message, settings):
        logging.info("Контент разрешен")
        return

    logging.info(f"Обнаружено неразрешенное сообщение в топике {topic_id} группы {group_id}")

    # Основная функция обработки сообщения
    async def process_message():
        try:
            user_id = message.from_user.id
            chat_member = await bot.get_chat_member(int(group_id), user_id)
            author = chat_member.user
        except Exception as e:
            logging.error(f"Ошибка получения информации об авторе: {e}")
            author = None

        mention_text = ""
        if settings.get("forward_mentions", False) and author:
            if author.username:
                mention_text = f"@{author.username}\n"
            else:
                mention_text = f'<a href="tg://user?id={author.id}">{author.first_name}</a>\n'

        for ft in settings.get("forward_to_topics", []):
            try:
                target_thread_id = None if ft == "default" else int(ft)
                
                # 1. Пересылаем исходное сообщение (если есть ответ)
                if message.reply_to_message:
                    await bot.forward_message(
                        chat_id=int(group_id),
                        from_chat_id=int(group_id),
                        message_id=message.reply_to_message.message_id,
                        message_thread_id=target_thread_id
                    )
                
                # 2. Отправляем упоминание (если не пустое)
                if mention_text.strip():
                    await bot.send_message(
                        chat_id=int(group_id),
                        text=mention_text,
                        parse_mode="HTML",
                        message_thread_id=target_thread_id
                    )
                
                # 3. Пересылаем текущее сообщение
                await bot.forward_message(
                    chat_id=int(group_id),
                    from_chat_id=int(group_id),
                    message_id=message.message_id,
                    message_thread_id=target_thread_id
                )
                await bot.get_chat()
                
            except Exception as e:
                logging.error(f"Ошибка обработки для топика {ft}: {e}")

    # Выполняем обработку
    await process_message()
    
    # Удаляем исходное сообщение
    try:
        await message.delete()
        logging.info("Исходное сообщение удалено")
    except Exception as e:
        logging.error(f"Ошибка удаления сообщения: {e}")