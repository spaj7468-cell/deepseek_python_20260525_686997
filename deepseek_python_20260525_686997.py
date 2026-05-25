import asyncio
import random
import json
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# -------------------- НАСТРОЙКИ --------------------
BOT_TOKEN = "ТВОЙ_ТОКЕН_СЮДА"

# -------------------- ДАННЫЕ --------------------
CARS = {
    "dominator":  {"name": "Доминатор",  "price": 5000,  "emoji": "🚙"},
    "cyclone":    {"name": "Циклон",     "price": 8000,  "emoji": "🌀"},
    "hurricane":  {"name": "Ураган",     "price": 10000, "emoji": "🌊"},
    "titan":      {"name": "Титан",      "price": 12000, "emoji": "🛡️"},
    "vortex":     {"name": "Вихрь",      "price": 15000, "emoji": "💨"},
    "tornado":    {"name": "Смерч",      "price": 20000, "emoji": "🌪️"},
    "typhoon":    {"name": "Тайфун",     "price": 18000, "emoji": "⛈️"},
    "storm":      {"name": "Гроза",      "price": 25000, "emoji": "⚡"},
    "nemesis":    {"name": "Немезида",   "price": 30000, "emoji": "🔥"},
    "armageddon": {"name": "Армагеддон", "price": 50000, "emoji": "💀"},
}

UPGRADE_COSTS = {1: 0, 2: 1.5, 3: 2.5}
REPAIR_COST = 500
BOOST_AMOUNT = 200
BOOST_COOLDOWN = timedelta(minutes=20)
STORM_MIN_WAIT = 60
STORM_MAX_WAIT = 300

TORNADO_TYPES = {
    "EF1": {"chance": 95, "reward": (100, 200)},
    "EF2": {"chance": 80, "reward": (150, 300)},
    "EF3": {"chance": 60, "reward": (250, 450)},
    "EF4": {"chance": 35, "reward": (400, 700)},
    "EF5": {"chance": 15, "reward": (600, 1000)},
}

users = {}

def load_users():
    global users
    try:
        with open("storm_users.json", "r", encoding="utf-8") as f:
            users = {int(k): v for k, v in json.load(f).items()}
    except:
        users = {}

def save_users():
    with open("storm_users.json", "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=2)

def get_user(user: types.User) -> dict:
    uid = user.id
    if uid not in users:
        users[uid] = {
            "name": user.first_name or "Штормер",
            "username": f"@{user.username}" if user.username else "нет",
            "balance": 500,
            "cars": {},
            "boost_until": None,
            "storm_active": False,
        }
    return users[uid]

# -------------------- КЛАВИАТУРЫ --------------------
def profil_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Убрать меню", callback_data="remove_menu"),
         InlineKeyboardButton(text="⚡ Буст", callback_data="boost")]
    ])

def shop_keyboard(page=0):
    car_ids = list(CARS.keys())
    per_page = 6
    total_pages = (len(car_ids) + per_page - 1) // per_page
    page = max(0, min(page, total_pages - 1))
    start = page * per_page
    page_cars = car_ids[start:start + per_page]
    buttons = []
    row = []
    for i, cid in enumerate(page_cars):
        c = CARS[cid]
        row.append(InlineKeyboardButton(text=f"{c['emoji']} {c['name']} ({c['price']} МШ)", callback_data=f"car_{cid}"))
        if i % 2 == 1:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton(text="⬅️ Назад", callback_data=f"shop_page_{page-1}"))
    if page < total_pages - 1:
        nav.append(InlineKeyboardButton(text="Вперёд ➡️", callback_data=f"shop_page_{page+1}"))
    if nav:
        buttons.append(nav)
    buttons.append([InlineKeyboardButton(text="❌ Закрыть", callback_data="remove_menu")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def storm_car_keyboard(user_data):
    buttons = []
    for cid, cd in user_data["cars"].items():
        c = CARS[cid]
        em = "🔧" if cd["broken"] else c["emoji"]
        st = "сломан" if cd["broken"] else f"ур.{cd['level']}"
        buttons.append([InlineKeyboardButton(text=f"{em} {c['name']} ({st})", callback_data=f"stormcar_{cid}")])
    buttons.append([InlineKeyboardButton(text="❌ Выйти", callback_data="remove_menu")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# -------------------- БОТ --------------------
bot = Bot(token=8922851436:AAFM-L00bk1NP772dWVGuDA3sZyVDEJLn3U)
dp = Dispatcher()

@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer("🌪️ Шторм бот запущен!\n/profil — профиль\n/shop — магазин\n/storm — охота\n/name Имя — сменить имя")

@dp.message(Command("name"))
async def name_cmd(message: types.Message):
    u = get_user(message.from_user)
    parts = message.text.split(maxsplit=1)
    if len(parts) > 1:
        u["name"] = parts[1][:30]
        save_users()
        await message.answer(f"✅ Имя: {u['name']}")

@dp.message(Command("profil"))
async def profil(message: types.Message):
    u = get_user(message.from_user)
    cars_text = "🚫 Нет машин"
    if u["cars"]:
        cars_text = "\n  ".join([f"{CARS[c]['emoji']} {CARS[c]['name']} (ур.{d['level']}) {'🔧' if d['broken'] else '✅'}" for c, d in u["cars"].items()])
    text = f"🌪️ Шторм-профиль\n👤 {u['name']}\n📛 {u['username']}\n💰 {u['balance']} МШ\n🚗 Машины:\n  {cars_text}"
    await message.answer(text, parse_mode="HTML", reply_markup=profil_keyboard() if message.chat.type != "private" else None)

@dp.message(Command("shop"))
async def shop(message: types.Message):
    await message.answer("🏎️ Магазин перехватчиков:", reply_markup=shop_keyboard())

@dp.message(Command("storm"))
async def storm(message: types.Message):
    u = get_user(message.from_user)
    if u.get("storm_active"):
        await message.answer("⏳ Вы уже в погоне!")
        return
    if not u["cars"]:
        await message.answer("🚫 Нет машин. Купите в /shop")
        return
    await message.answer("🌪️ Выберите перехватчика:", reply_markup=storm_car_keyboard(u))

@dp.message(F.chat.type.in_(["group", "supergroup"]))
async def group_msg(message: types.Message):
    if message.text and message.text.startswith("/"):
        return
    u = get_user(message.from_user)
    now = datetime.now()
    last = u.get("last_active")
    if last and now - datetime.fromisoformat(last) < timedelta(minutes=3):
        return
    u["last_active"] = now.isoformat()
    reward = random.randint(10, 100)
    u["balance"] += reward
    save_users()
    await asyncio.sleep(random.uniform(2, 5))
    await message.reply(f"🌪️ Шторм заметил активность!\n{message.from_user.full_name} получает {reward} МШ!\nБаланс: {u['balance']} МШ")

@dp.callback_query(F.data == "remove_menu")
async def remove_menu(cb: types.CallbackQuery):
    try:
        await cb.message.delete()
    except:
        pass
    await cb.answer()

@dp.callback_query(F.data == "boost")
async def boost(cb: types.CallbackQuery):
    u = get_user(cb.from_user)
    now = datetime.now()
    if u.get("boost_until") and now < datetime.fromisoformat(u["boost_until"]):
        await cb.answer("Буст ещё недоступен", show_alert=True)
        return
    u["boost_until"] = (now + BOOST_COOLDOWN).isoformat()
    u["balance"] += BOOST_AMOUNT
    save_users()
    try:
        await bot.send_message(cb.from_user.id, f"⚡ Буст! +{BOOST_AMOUNT} МШ\nБаланс: {u['balance']} МШ")
    except:
        pass
    await cb.answer("Буст в личке!", show_alert=True)

@dp.callback_query(F.data.startswith("shop_page_"))
async def shop_page(cb: types.CallbackQuery):
    await cb.message.edit_reply_markup(reply_markup=shop_keyboard(int(cb.data.split("_")[-1])))
    await cb.answer()

@dp.callback_query(F.data.startswith("car_"))
async def car_action(cb: types.CallbackQuery):
    cid = cb.data[4:]
    u = get_user(cb.from_user)
    c = CARS[cid]
    uc = u["cars"].get(cid)
    if uc is None:
        if u["balance"] < c["price"]:
            await cb.answer(f"Недостаточно МШ! Нужно: {c['price']}", show_alert=True)
            return
        u["balance"] -= c["price"]
        u["cars"][cid] = {"level": 1, "broken": False}
        save_users()
        await cb.answer(f"✅ Куплен {c['name']}!", show_alert=True)
    elif uc["broken"]:
        if u["balance"] < REPAIR_COST:
            await cb.answer(f"Недостаточно МШ! Нужно: {REPAIR_COST}", show_alert=True)
            return
        u["balance"] -= REPAIR_COST
        uc["broken"] = False
        save_users()
        await cb.answer(f"🔧 {c['name']} отремонтирован!", show_alert=True)
    elif uc["level"] >= 3:
        await cb.answer("Максимальный уровень!", show_alert=True)
    else:
        cost = int(c["price"] * UPGRADE_COSTS[uc["level"] + 1])
        if u["balance"] < cost:
            await cb.answer(f"Недостаточно МШ! Нужно: {cost}", show_alert=True)
            return
        u["balance"] -= cost
        uc["level"] += 1
        save_users()
        await cb.answer(f"⬆️ {c['name']} → ур.{uc['level']}!", show_alert=True)
    await cb.message.edit_reply_markup(reply_markup=shop_keyboard())

@dp.callback_query(F.data.startswith("stormcar_"))
async def storm_start(cb: types.CallbackQuery):
    cid = cb.data[9:]
    u = get_user(cb.from_user)
    if u.get("storm_active"):
        await cb.answer("Уже в погоне!", show_alert=True)
        return
    cd = u["cars"].get(cid)
    if not cd or cd["broken"]:
        await cb.answer("Машина недоступна!", show_alert=True)
        return
    u["storm_active"] = True
    save_users()
    wait = random.randint(STORM_MIN_WAIT, STORM_MAX_WAIT)
    await cb.message.edit_text(f"🌪️ Погоня на {CARS[cid]['emoji']} {CARS[cid]['name']}!\n⏳ Ждите {wait//60} мин {wait%60} сек...")
    await cb.answer()
    asyncio.create_task(storm_finish(cb.from_user.id, cid, wait, cb.message.chat.id, cb.message.message_id))

async def storm_finish(uid, cid, wait, chat_id, msg_id):
    await asyncio.sleep(wait)
    if uid not in users:
        return
    u = users[uid]
    u["storm_active"] = False
    cd = u["cars"].get(cid)
    if not cd:
        return
    c = CARS[cid]
    ef = random.choices(["EF1","EF2","EF3","EF4","EF5"], weights=[35,30,20,10,5])[0]
    t = TORNADO_TYPES[ef]
    bonus = (cd["level"]-1)*10
    ok = random.randint(1,100) <= min(95, t["chance"]+bonus)
    if ok:
        reward = random.randint(*t["reward"])
        u["balance"] += reward
        text = f"🌪️ Погоня завершена!\n🚗 {c['emoji']} {c['name']} (ур.{cd['level']})\n✅ Торнадо {ef} перехвачен!\n💰 +{reward} МШ"
    else:
        cd["broken"] = True
        text = f"🌪️ Погоня завершена!\n🚗 {c['emoji']} {c['name']} (ур.{cd['level']})\n❌ {ef} повредил машину!\n🔧 Ремонт: {REPAIR_COST} МШ"
    save_users()
    try:
        await bot.edit_message_text(text, chat_id=chat_id, message_id=msg_id)
    except:
        pass

async def main():
    load_users()
    print("🌪️ Бот Шторм запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())