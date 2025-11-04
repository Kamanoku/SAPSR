# save as checker_oop.py
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import docx
import PyPDF2
import os
import re
from datetime import datetime

# -------------------------
# DocumentLoader
# -------------------------
class DocumentLoader:
    """Загружает текст из .docx и .pdf файлов."""
    @staticmethod
    def load_docx(path: str) -> str:
        doc = docx.Document(path)
        paragraphs = [p.text for p in doc.paragraphs]
        return "\n".join(paragraphs)

    @staticmethod
    def load_pdf(path: str) -> str:
        text = []
        with open(path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                page_text = page.extract_text() or ""
                text.append(page_text)
        return "\n".join(text)

    @staticmethod
    def get_text(path: str) -> str:
        lower = path.lower()
        if lower.endswith(".docx"):
            return DocumentLoader.load_docx(path)
        elif lower.endswith(".pdf"):
            return DocumentLoader.load_pdf(path)
        else:
            raise ValueError("Поддерживаются только .docx и .pdf")


# -------------------------
# Template
# -------------------------
class Template:
    """Хранит список разделов (шаблон) и методы загрузки из файла."""
    def __init__(self, sections=None, source_path=None):
        self.sections = sections or []
        self.source_path = source_path

    @staticmethod
    def _heuristic_extract_sections(text: str) -> list:
        """
        Эвристика для извлечения разделов из шаблона:
        - Берём непустые параграфы/строки.
        - Фильтруем по длине (не слишком длинные).
        - Отбрасываем строки, в которых встречается множеством точек (обычные предложения).
        - Отбираем строки, где есть хотя бы одно слово с заглавной первой буквой (часто заголовки).
        - Дополнительно можно адаптировать под твои конкретные примеры шаблонов.
        """
        lines = [ln.strip() for ln in text.splitlines()]
        candidates = []
        for ln in lines:
            if not ln:
                continue
            if len(ln) > 120:
                # слишком длинная — вероятно не заголовок
                continue
            # если в строке есть точка в середине (что похоже на предложение), пропустить
            if ln.count('.') > 1 or ('.' in ln and len(ln) > 60):
                continue
            # если строка выглядит как список (много тире/буллетов), пропустить
            if re.search(r'^[\-\*\•\–\—]\s+', ln):
                continue
            # если строка содержит скорее всего заголовок: первая буква заглавная или все заглавные
            stripped = re.sub(r'[^А-Яа-яA-Za-zЁё0-9\s\-]', '', ln)
            words = stripped.split()
            if not words:
                continue
            # признать заголовком, если:
            # - меньше 6 слов и первая буква первого слова большая
            # - или строка короткая (<40) и содержит ключевые слова (Введение, Заключение и т.д.)
            first_word = words[0]
            if (len(words) <= 6 and first_word[:1].isupper()) or len(ln) < 40:
                candidates.append(ln)
        # Удалим дубликаты, сохраняя порядок
        seen = set()
        out = []
        for c in candidates:
            low = c.lower()
            if low not in seen:
                seen.add(low)
                out.append(c)
        return out

    @classmethod
    def load_from_file(cls, path: str):
        text = DocumentLoader.get_text(path)
        sections = cls._heuristic_extract_sections(text)
        # Если из шаблона не удалось извлечь разделы (пусто), попробуем взять
        # первые несколько значимых строк как запасной вариант
        if not sections:
            fallback = [ln.strip() for ln in text.splitlines() if ln.strip()][:10]
            sections = fallback[:5]
        return cls(sections=sections, source_path=path)

    def get_sections(self):
        return self.sections


# -------------------------
# DocumentChecker
# -------------------------
class DocumentChecker:
    """Сравнивает текст документа с шаблоном, возвращает отчёт."""
    def __init__(self, template: Template):
        self.template = template

    @staticmethod
    def _find_with_context(text: str, query: str, context_chars: int = 100):
        """Ищет query в text (без учёта регистра). Возвращает (found:bool, snippet or None)."""
        lowered = text.lower()
        q = query.lower()
        idx = lowered.find(q)
        if idx == -1:
            return False, None
        start = max(0, idx - context_chars)
        end = min(len(text), idx + len(q) + context_chars)
        snippet = text[start:end].strip()
        # подчёркиваем найденную часть (делаем её в верхнем регистре для простоты визуализации)
        # но не ломаем кириллицу/регистры, вместо этого выделим скобками
        snippet = snippet.replace(text[idx:idx+len(q)], f"«{text[idx:idx+len(q)]}»")
        return True, snippet

    def check_text(self, document_text: str) -> list:
        """Проверяет document_text по всем секциям шаблона.
        Возвращает список словарей: {'section': str, 'found': bool, 'context': str|None}
        """
        results = []
        for sec in self.template.get_sections():
            # Иногда в шаблоне есть нумерация или лишние пробелы — упростим поисковый запрос
            query = sec.strip()
            if not query:
                continue
            found, snippet = self._find_with_context(document_text, query)
            results.append({
                "section": query,
                "found": found,
                "context": snippet
            })
        return results

    def generate_report_text(self, file_name: str, results: list) -> str:
        """Форматированный текст отчёта."""
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        header = f"Отчёт проверки\nФайл: {file_name}\nШаблон: {os.path.basename(self.template.source_path) if self.template.source_path else '(не указан)'}\nДата: {now}\n\n"
        lines = [header]
        for r in results:
            status = "✅ Найдено" if r["found"] else "❌ Отсутствует"
            lines.append(f"{status}: {r['section']}")
            if r["found"] and r.get("context"):
                lines.append(f"  Контекст: {r['context']}")
            lines.append("")  # пустая строка
        return "\n".join(lines)


# -------------------------
# AppGUI (Tkinter)
# -------------------------
class AppGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Проверка структуры документа (OOП)")
        self.root.geometry("700x520")
        self.template = None
        self.document_text = None
        self.document_path = None
        self.checker = None
        self._build_ui()

    def _build_ui(self):
        frame = tk.Frame(self.root, padx=10, pady=10)
        frame.pack(fill="both", expand=True)

        title = tk.Label(frame, text="Проверка структуры документа (шаблон → документ)", font=("Segoe UI", 14, "bold"))
        title.pack(pady=(0,8))

        btn_frame = tk.Frame(frame)
        btn_frame.pack(fill="x", pady=6)

        self.load_template_btn = tk.Button(btn_frame, text="Загрузить шаблон", command=self.load_template, width=18)
        self.load_template_btn.pack(side="left", padx=(0,8))

        self.load_doc_btn = tk.Button(btn_frame, text="Загрузить проверяемый файл", command=self.load_document, width=26, state="disabled")
        self.load_doc_btn.pack(side="left", padx=(0,8))

        self.run_check_btn = tk.Button(btn_frame, text="Проверить", command=self.run_check, width=12, state="disabled")
        self.run_check_btn.pack(side="left")

        self.save_report_btn = tk.Button(btn_frame, text="Сохранить отчёт", command=self.save_report, width=16, state="disabled")
        self.save_report_btn.pack(side="right")

        # Информация о загруженных файлах
        info_frame = tk.Frame(frame)
        info_frame.pack(fill="x", pady=(6, 8))
        self.template_label = tk.Label(info_frame, text="Шаблон: (не загружен)", anchor="w")
        self.template_label.pack(fill="x")
        self.document_label = tk.Label(info_frame, text="Проверяемый файл: (не загружен)", anchor="w")
        self.document_label.pack(fill="x")

        # Результат
        self.result_text = scrolledtext.ScrolledText(frame, wrap=tk.WORD, width=90, height=22, font=("Segoe UI", 10))
        self.result_text.pack(fill="both", expand=True)

        # Приветствие / подсказка
        welcome = (
            "Инструкция:\n"
            "1) Нажмите «Загрузить шаблон» и выберите .docx или .pdf, в котором перечислены разделы (например: Введение, Методы, Заключение).\n"
            "   Программа попытается автоматически выделить заголовки/строки-шаблоны из этого файла.\n"
            "2) Нажмите «Загрузить проверяемый файл» и выберите .docx или .pdf для проверки.\n"
            "3) Нажмите «Проверить» — в окне появится отчёт о соответствии.\n\n"
            "Если извлечённые из шаблона разделы выглядят некорректно, откройте шаблон и поправьте его (или используйте простой шаблон, где каждая строка — раздел)."
        )
        self.result_text.insert(tk.END, welcome)

        # internal storage for latest report
        self._last_report_text = ""

    def load_template(self):
        path = filedialog.askopenfilename(title="Выберите файл-шаблон", filetypes=[("Документы Word", "*.docx"), ("PDF файлы", "*.pdf")])
        if not path:
            return
        try:
            tpl = Template.load_from_file(path)
            self.template = tpl
            self.template_label.config(text=f"Шаблон: {os.path.basename(path)} — {len(tpl.get_sections())} раздел(ов) извлечено")
            # показать извлечённые разделы в окне
            preview = "\n".join(f"• {s}" for s in tpl.get_sections())
            self.result_text.delete(1.0, tk.END)
            self.result_text.insert(tk.END, f"Шаблон загружен: {os.path.basename(path)}\n\nИзвлечённые разделы:\n{preview}\n\nТеперь загрузите проверяемый файл.")
            # включаем кнопку загрузки документа
            self.load_doc_btn.config(state="normal")
            # сбрасываем предыдущие данные
            self.document_text = None
            self.document_path = None
            self.checker = None
            self.run_check_btn.config(state="disabled")
            self.save_report_btn.config(state="disabled")
        except Exception as e:
            messagebox.showerror("Ошибка загрузки шаблона", str(e))

    def load_document(self):
        path = filedialog.askopenfilename(title="Выберите проверяемый файл", filetypes=[("Документы Word", "*.docx"), ("PDF файлы", "*.pdf")])
        if not path:
            return
        try:
            txt = DocumentLoader.get_text(path)
            self.document_text = txt
            self.document_path = path
            self.document_label.config(text=f"Проверяемый файл: {os.path.basename(path)}")
            self.result_text.delete(1.0, tk.END)
            self.result_text.insert(tk.END, f"Файл для проверки загружен: {os.path.basename(path)}\n\nНажмите «Проверить» чтобы сравнить с шаблоном.")
            # готово к проверке
            if self.template:
                self.checker = DocumentChecker(self.template)
                self.run_check_btn.config(state="normal")
        except Exception as e:
            messagebox.showerror("Ошибка загрузки файла", str(e))

    def run_check(self):
        if not self.template:
            messagebox.showwarning("Нет шаблона", "Сначала загрузите шаблон.")
            return
        if not self.document_text:
            messagebox.showwarning("Нет проверяемого файла", "Сначала загрузите проверяемый файл.")
            return
        try:
            results = self.checker.check_text(self.document_text)
            report = self.checker.generate_report_text(os.path.basename(self.document_path), results)
            self._last_report_text = report
            self.result_text.delete(1.0, tk.END)
            self.result_text.insert(tk.END, report)
            self.save_report_btn.config(state="normal")
        except Exception as e:
            messagebox.showerror("Ошибка при проверке", str(e))

    def save_report(self):
        if not self._last_report_text:
            messagebox.showinfo("Нет отчёта", "Сначала выполните проверку, чтобы сохранить отчёт.")
            return
        path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Текстовый файл", "*.txt")], title="Сохранить отчёт как")
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(self._last_report_text)
            messagebox.showinfo("Готово", f"Отчёт сохранён: {os.path.basename(path)}")
        except Exception as e:
            messagebox.showerror("Ошибка сохранения", str(e))


# -------------------------
# main
# -------------------------
def main():
    root = tk.Tk()
    app = AppGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
