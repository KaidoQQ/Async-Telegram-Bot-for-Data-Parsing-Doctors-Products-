import asyncio
import sys
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from dotenv import load_dotenv
import os

from parsers.doctor_parser import DoctorSearchFunc
from parsers.product_parser import ProductParser

from tech.to_exel import excel_file_doctor 
from tech.to_exel import excel_file_product

from tech.database import DataBase

from aiogram.types import FSInputFile

from deep_translator import GoogleTranslator


load_dotenv("tokens.env")

BOT_TOKEN = os.getenv("BOT_TOKEN") #---- Your token here

logging.basicConfig(level=logging.INFO)

db = DataBase('bot_database.db')


doctor_service = DoctorSearchFunc()
product_parser = ProductParser()

bot = Bot(
  token=BOT_TOKEN, 
  default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN)
)
dp = Dispatcher()

class DoctorSearch(StatesGroup):
  waiting_for_name_spec = State()
  waiting_for_city_spec  = State()
  waiting_for_date_spec  = State()

  waiting_for_name = State()
  waiting_for_city  = State()
  waiting_for_date  = State()

class ProductSearch(StatesGroup):
  waiting_for_category = State()
  waiting_for_budget = State()

def translate_to_polish(text):
  try:
    translated = GoogleTranslator(source='auto', target='pl').translate(text)
    return translated
  except Exception as e:
    logging.error(f"❌ [ERROR]: {e}")
    return text


@dp.message(CommandStart())
async def cmd_start(message: types.Message):
  db.add_user(message.from_user.id, message.from_user.username)
  print(f"👤 User {message.from_user.first_name} saved to DB")

  kb = [
    [KeyboardButton(text = "👨‍⚕️ Doc Search (Spec)"),
     KeyboardButton(text = "👨‍⚕️ Doc Search (Name)"),
    KeyboardButton(text = "🛍 Product Search")
    ],
    [
      KeyboardButton(text = "ℹ️ Help")
    ]
  ]

  keyboard = ReplyKeyboardMarkup(
    keyboard=kb,
    resize_keyboard=True,
    input_field_placeholder="Select an option"
  )

  await message.answer(
    f"Hello, {message.from_user.first_name}! I am your Parser Bot. Choose an option:",
    reply_markup=keyboard
  )

@dp.message(F.text =="ℹ️ Help")
async def cmd_help(message: types.Message):
  await message.answer("I can help you find open slots for doctors or track product prices.")


@dp.message(F.text == "👨‍⚕️ Doc Search (Spec)")
async def doctor_name_search_spec(message: types.Message, state: FSMContext):
  await message.answer("Please enter the *Specialty* (e.g., Dentist):")
  await state.set_state(DoctorSearch.waiting_for_name_spec)

@dp.message(DoctorSearch.waiting_for_name_spec)
async def doctor_name_chosen_spec(message: types.Message, state: FSMContext):
  await state.update_data(doctor_name_spec = message.text)
  await message.answer("Got it. Now please enter the *City* (e.g., Krakow):")
  await state.set_state(DoctorSearch.waiting_for_date_spec)


@dp.message(DoctorSearch.waiting_for_date_spec)
async def doctor_date_chosen_spec(message: types.Message, state: FSMContext):
  user_data = await state.get_data()
  name = user_data['doctor_name_spec'].lower().strip()
  city = message.text.lower().strip()

  n_name_spec = await asyncio.to_thread(translate_to_polish, name)

  search_query = f"Doctor: {name}, City: {city}"
  cached_path = db.get_cached_file(search_query)

  if cached_path and os.path.exists(cached_path):
    print(f"📦 Found in cache: {cached_path}")
    await message.answer("📦 Found cached result! Sending file...")

    document = FSInputFile(cached_path, filename=f"{name}_doctor_list.xlsx")
    await message.answer_document(document, caption=f"✅ Done! (Loaded from cache)")
    await state.clear()
    return 

  await message.answer(f"🔎 Searching for *{name}* in *{city}*... Please wait.")

  search_params = {
    "doctor_name": name if 'doctor_name' in user_data else None,
    "doctor_name_spec": n_name_spec,
    "city": city,
  }

  result_data = await doctor_service.search(**search_params)

  # Генерируем уникальное имя для файла на диске
  # Используем replace, чтобы убрать пробелы, которые могут мешать системе
  safe_name = name.replace(" ", "_")
  new_filename = f"cache/{safe_name}_{city}.xlsx"

  file_path = await excel_file_doctor(result_data, filename=new_filename)

  if file_path:
    db.add_search_log(message.from_user.id, "doctor_search", search_query, file_path)

    document = FSInputFile(file_path,filename=f"{name}_doctor_list.xlsx")
    await message.answer_document(document, caption=f"✅ Done! Here is the list for you")
  else:
    await message.answer("❌ [ERROR] Nothing was found or error creating file.")
  await state.clear()



@dp.message(F.text == "👨‍⚕️ Doc Search (Name)")
async def doctor_name_search(message: types.Message, state: FSMContext):
  await message.answer("Please enter the doctors *Name and Surname* (e.g.,Alla Krykhta)")
  await state.set_state(DoctorSearch.waiting_for_name)

@dp.message(DoctorSearch.waiting_for_name)
async def doctor_name_chosen(message: types.Message, state: FSMContext):
  await state.update_data(doctor_name = message.text)
  await message.answer("Got it. Now please enter the *City* (e.g., Krakow):")
  await state.set_state(DoctorSearch.waiting_for_date)


@dp.message(DoctorSearch.waiting_for_date)
async def doctor_date_chosen(message: types.Message, state: FSMContext):
  user_data = await state.get_data()
  name = user_data['doctor_name'].lower().strip()
  city = message.text.lower().strip()

  search_query = f"Doctor: {name}, City: {city}"
  cached_path = db.get_cached_file(search_query)

  if cached_path and os.path.exists(cached_path):
    print(f"📦 Found in cache: {cached_path}")
    await message.answer("📦 Found cached result! Sending file...")

    document = FSInputFile(cached_path, filename=f"{name}_doctor_list.xlsx")
    await message.answer_document(document, caption=f"✅ Done! (Loaded from cache)")
    await state.clear()
    return 

  await message.answer(f"🔎 Searching for *{name}* in *{city}*... Please wait.")

  search_params = {
    "doctor_name": name if 'doctor_name' in user_data else None,
    "doctor_name_spec": user_data.get('doctor_name_spec'),
    "city": city,
  }

  result_data = await doctor_service.search(**search_params)

  # Генерируем уникальное имя для файла на диске
  # Используем replace, чтобы убрать пробелы, которые могут мешать системе
  safe_name = name.replace(" ", "_")
  new_filename = f"cache/{safe_name}_{city}.xlsx"

  file_path = await excel_file_doctor(result_data, filename=new_filename)

  if file_path:
    db.add_search_log(message.from_user.id, "doctor_search", search_query, file_path)

    document = FSInputFile(file_path,filename=f"{name}_doctor_list.xlsx")
    await message.answer_document(document, caption=f"✅ Done! Here is the list for you")
  else:
    await message.answer("❌ [ERROR] Nothing was found or error creating file.")
  await state.clear()



@dp.message(F.text == "🛍 Product Search")
async def product_category_search(message: types.Message, state:FSMContext):
  await message.answer("Please enter the *Product Category* or *Name* (e.g., iPhone 15, Sneakers):")
  await state.set_state(ProductSearch.waiting_for_category)

@dp.message(ProductSearch.waiting_for_category)
async def product_category_chosen(message: types.Message, state:FSMContext):
  await state.update_data(category = message.text)
  await message.answer("Okay. What is your *Budget*? (e.g., 1000 ZŁ):")
  await state.set_state(ProductSearch.waiting_for_budget)

@dp.message(ProductSearch.waiting_for_budget)
async def product_budget_chosen(message: types.Message, state: FSMContext):
  user_data = await state.get_data()
  category = user_data['category']
  budget = message.text

  search_query = f"Category: {category}, Budget: {budget}"
  cached_path = db.get_cached_file(search_query)

  if cached_path and os.path.exists(cached_path):
    print(f"📦 Found in cache: {cached_path}")
    await message.answer("📦 Found cached result! Sending file...")

    document = FSInputFile(cached_path, filename=f"{category}_list.xlsx")
    await message.answer_document(document, caption=f"✅ Done! (Loaded from cache)")
    await state.clear()
    return 
  
  await message.answer(f"🔎 Searching for *{category}* with budget *{budget}*... Please wait.")

  result_data = await asyncio.to_thread(
    product_parser.parser, 
    category=category, 
    budget=budget
  )

  safe_name = category.replace(" ", "_")
  new_filename = f"cache/{safe_name}_{budget}.xlsx"

  file_path = await excel_file_product(result_data,filename=new_filename)
  
  if file_path:
    db.add_search_log(message.from_user.id, "product_search", search_query, file_path)

    document = FSInputFile(file_path)
    await message.answer_document(document, caption=f"✅ Done! Here is the list for you")
  else:
    await message.answer("❌ [ERROR] Nothing was found or error creating file.")
  await state.clear()


async def main():
  print("🧿 Bot Started!")
  await dp.start_polling(bot)

if __name__ == "__main__":
  if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

  try:
    asyncio.run(main())
  except KeyboardInterrupt:
    print("☠️ Bot collapse!")