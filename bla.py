import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import docx
import PyPDF2
import os


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


def check_pdf(file_path):
    text = ""
    with open(file_path, "rb") as f:
        reader = PyPDF2.PdfReader(f)
        for page in reader.pages:
            text += page.extract_text() or ""
    result = []
    for section in ["Введение", "Заключение", "Список литературы"]:
        if section.lower() in text.lower():
            result.append(f"✅ {section} — найдено")
        else:
            result.append(f"❌ {section} — отсутствует")
    return "\n".join(result)


def choose_file():
    file_path = filedialog.askopenfilename(
        title="Выберите документ",
        filetypes=[("Документы Word", "*.docx"), ("PDF файлы", "*.pdf")]
    )

    if not file_path:
        return

    result_text.delete(1.0, tk.END)

    try:
        if file_path.endswith(".docx"):
            result = check_docx(file_path)
        elif file_path.endswith(".pdf"):
            result = check_pdf(file_path)
        else:
            messagebox.showerror("Ошибка", "Поддерживаются только .docx и .pdf файлы.")
            return

        # Показ результатов
        result_text.insert(tk.END, f"📄 Файл: {os.path.basename(file_path)}\n\n")
        result_text.insert(tk.END, result)

    except Exception as e:
        messagebox.showerror("Ошибка при проверке", str(e))


# === Интерфейс ===
root = tk.Tk()
root.title("Проверка структуры документа")
root.geometry("500x400")
root.resizable(True, True)

frame = tk.Frame(root, padx=10, pady=10)
frame.pack(fill="both", expand=True)

label = tk.Label(frame, text="Проверка структуры документа", font=("Segoe UI", 14, "bold"))
label.pack(pady=10)

button = tk.Button(frame, text="Выбрать файл", command=choose_file, font=("Segoe UI", 12))
button.pack(pady=5)

result_text = scrolledtext.ScrolledText(frame, wrap=tk.WORD, width=60, height=15, font=("Segoe UI", 10))
result_text.pack(pady=10)

# === Приветственное сообщение ===
welcome_message = (
    "💬 Добро пожаловать!\n\n"
    "Выберите файл (.docx или .pdf) для проверки структуры.\n"
    "Программа определит наличие разделов:\n"
    "• Введение\n"
    "• Заключение\n"
    "• Список литературы\n\n"
    "Нажмите кнопку «Выбрать файл» 👇"
)
result_text.insert(tk.END, welcome_message)

root.mainloop()
