import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import docx
import PyPDF2

# === Укажите ваш токен от BotFather ===
TOKEN = "8330847005:AAEmWHaLmGnq3dLBpcBU5P7fDBuc4jgDecA"

# --- Проверка DOCX ---
def check_docx(file_path):
    doc = docx.Document(file_path)
    text = "\n".join([p.text for p in doc.paragraphs])
    result = []
    for section in ["Введение", "Заключение", "Список литературы"]:
        if section.lower() in text.lower():
            result.append(f"✅ {section} — найдено")
        else:
            result.append(f"❌ {section} — отсутствует")
    return "\n".join(result)

# --- Проверка PDF ---
def check_pdf(file_path):
    with open(file_path, "rb") as f:
        reader = PyPDF2.PdfReader(f)
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""
    result = []
    for section in ["Введение", "Заключение", "Список литературы"]:
        if section.lower() in text.lower():
            result.append(f"✅ {section} — найдено")
        else:
            result.append(f"❌ {section} — отсутствует")
    return "\n".join(result)

# --- Стартовая команда ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Отправь мне файл (.docx или .pdf), и я проверю его структуру 📑")

# --- Обработка документов ---
async def handle_docs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file = await update.message.document.get_file()
    file_path = update.message.document.file_name
    await file.download_to_drive(file_path)

    if file_path.endswith(".docx"):
        report = check_docx(file_path)
    elif file_path.endswith(".pdf"):
        report = check_pdf(file_path)
    else:
        report = "❌ Поддерживаются только .docx и .pdf"

    os.remove(file_path)
    await update.message.reply_text(report)

# --- Запуск бота ---
def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_docs))

    app.run_polling()

if __name__ == "__main__":
    main()
