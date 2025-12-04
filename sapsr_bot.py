import asyncio
import os
import logging
import re
from datetime import datetime

# Библиотеки для Telegram
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

# Библиотеки для работы с документами
import docx
import PyPDF2

# ============================================================
#  ЧАСТЬ 1: CORE LOGIC (Ваш исходный код без GUI)
# ============================================================

class DocumentLoader:
    @staticmethod
    def _normalize_text(s: str) -> str:
        if s is None: return ""
        s = s.replace("\u00A0", " ").replace("\u200B", "").replace("\uFEFF", "")
        s = re.sub(r"[ \t\v\f\u00A0]+", " ", s)
        return s.strip()

    @staticmethod
    def load_docx_text_and_paragraphs(path: str, dedupe: bool = True, preserve_empty: bool = False):
        doc = docx.Document(path)
        paragraphs = []
        seen = set()
        def add_para(text):
            if text is None: text = ""
            t_norm = DocumentLoader._normalize_text(text) if text else ""
            if t_norm == "" and not preserve_empty: return
            if dedupe:
                if t_norm and t_norm not in seen:
                    paragraphs.append(t_norm); seen.add(t_norm)
                elif t_norm == "" and preserve_empty: paragraphs.append(t_norm)
            else:
                if t_norm == "" and not preserve_empty: return
                paragraphs.append(t_norm)

        for p in doc.paragraphs: add_para("".join(run.text for run in p.runs))
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    for p in cell.paragraphs: add_para("".join(run.text for run in p.runs))
        return "\n".join(paragraphs), paragraphs

    @staticmethod
    def load_pdf_text_and_paragraphs(path: str, dedupe: bool = True, preserve_empty: bool = False):
        text_lines = []
        seen = set()
        with open(path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                page_text = page.extract_text() or ""
                for ln in page_text.splitlines():
                    ln_norm = DocumentLoader._normalize_text(ln)
                    if ln_norm == "" and not preserve_empty: continue
                    if dedupe:
                        if ln_norm and ln_norm not in seen:
                            text_lines.append(ln_norm); seen.add(ln_norm)
                        elif ln_norm == "" and preserve_empty: text_lines.append(ln_norm)
                    else:
                        if ln_norm == "" and not preserve_empty: continue
                        text_lines.append(ln_norm)
        return "\n".join(text_lines), text_lines

    @staticmethod
    def get_paragraphs(path: str):
        lower = path.lower()
        if lower.endswith(".docx"):
            _, paras = DocumentLoader.load_docx_text_and_paragraphs(path, dedupe=False, preserve_empty=True)
            return paras
        elif lower.endswith(".pdf"):
            _, paras = DocumentLoader.load_pdf_text_and_paragraphs(path, dedupe=False, preserve_empty=True)
            return paras
        else:
            raise ValueError("Поддерживаются только .docx и .pdf")

class Template:
    def __init__(self, placeholders=None, source_path=None):
        self.placeholders = placeholders or []
        self.source_path = source_path
    
    def get_placeholders(self): return self.placeholders

    @staticmethod
    def _normalize_type(raw_type: str) -> str:
        t = raw_type.strip().lower()
        if t in ("int", "integer", "num", "number", "float"): return "number"
        if t in ("str", "string", "text"): return "string"
        if t in ("date", "dt"): return "date"
        return t

    @staticmethod
    def extract_placeholders_from_paragraphs(paragraphs: list) -> list:
        placeholders = []
        inline_pattern = re.compile(r"\[\[\s*([^:\]\n]+?)\s*:\s*([^,\]\n]+?)(?:\s*,\s*(optional))?\s*\]\]", flags=re.IGNORECASE)
        skip_patterns = ["утверждаю", "задание", "введение", "заключение", "список использованных источников", "примерный календарный график", "подпись обучающегося"]

        for idx, para in enumerate(paragraphs):
            if not para.strip(): continue
            for m in inline_pattern.finditer(para):
                raw_name = m.group(1).strip()
                raw_type = m.group(2).strip()
                optional_flag = bool(m.group(3))
                left_part = para[: m.start()].strip()
                
                # anchor_before
                if left_part: anchor_before = left_part
                else:
                    anchor_before = ""
                    for j in range(idx - 1, -1, -1):
                        prev_para = paragraphs[j].strip()
                        if prev_para and not inline_pattern.search(prev_para) and not any(sp in prev_para.lower() for sp in skip_patterns):
                            anchor_before = prev_para; break
                
                # anchor_after
                right_part = para[m.end() :].strip()
                if right_part: anchor_after = right_part
                else:
                    anchor_after = ""
                    max_dist = 6
                    forbidden = ["(подпись)", "подпись", "инициалы", "фамилия"]
                    for j in range(idx + 1, min(len(paragraphs), idx + 1 + max_dist)):
                        next_para = paragraphs[j].strip()
                        if not next_para: continue
                        if any(f in next_para.lower() for f in forbidden): continue
                        if not inline_pattern.search(next_para) and not any(sp in next_para.lower() for sp in skip_patterns):
                            anchor_after = next_para; break
                
                placeholders.append({
                    "name": raw_name, "type": Template._normalize_type(raw_type),
                    "optional": optional_flag, "anchor_before": anchor_before,
                    "anchor_after": anchor_after, "para_index": idx
                })

        # dedupe
        seen = set()
        unique = []
        for p in placeholders:
            key = (p["name"].lower(), p["anchor_before"], p["anchor_after"])
            if key not in seen:
                seen.add(key); unique.append(p)
        
        # next_is_placeholder logic
        for i in range(len(unique) - 1):
            if unique[i + 1]["para_index"] - unique[i]["para_index"] <= 1:
                unique[i]["next_is_placeholder"] = True
            else:
                unique[i]["next_is_placeholder"] = False
        return unique

    @classmethod
    def load_from_file(cls, path: str):
        lower = path.lower()
        if lower.endswith(".docx"):
            _, paragraphs = DocumentLoader.load_docx_text_and_paragraphs(path, dedupe=True, preserve_empty=False)
        elif lower.endswith(".pdf"):
            _, paragraphs = DocumentLoader.load_pdf_text_and_paragraphs(path, dedupe=True, preserve_empty=False)
        else:
            raise ValueError("Поддерживаются только .docx и .pdf")
        
        placeholders = cls.extract_placeholders_from_paragraphs(paragraphs)
        if not placeholders:
            raise ValueError("В шаблоне не найдено ни одного заполнителя [[...]]")
        return cls(placeholders=placeholders, source_path=path)

class DocumentChecker:
    def __init__(self, template: Template):
        self.template = template

    @staticmethod
    def _validate_type(value: str, expected_type: str) -> bool:
        if not value: return False
        v = value.strip()
        if expected_type == "string": return bool(re.search(r"[A-Za-zА-Яа-яЁё]", v))
        if expected_type == "number": return bool(re.fullmatch(r"[+-]?\d+([.,]\d+)?", v))
        if expected_type == "date": return bool(re.fullmatch(r"\d{1,2}\.\d{1,2}\.\d{4}", v) or re.search(r"\d{1,2}\s+[А-Яа-яёЁ]+\.?\s+\d{4}", v))
        return True

    @staticmethod
    def _is_anchor_like(value: str, anchors: list) -> bool:
        if not value: return False
        v = re.sub(r"\s+", " ", value).strip().lower()
        for a in anchors:
            if not a: continue
            if v == re.sub(r"\s+", " ", a).strip().lower(): return True
        return False

    def _find_value_using_anchors(self, anchor_before, anchor_after, doc_paragraphs, start_index=0, expected_type=None, next_is_placeholder=False):
        stop_words = ["введение", "заключение", "список использованных источников", "приложение", "задание"]
        
        def find_positions(anchor):
            if not anchor: return []
            a_norm = re.sub(r"\s+", " ", anchor.strip()).lower()
            pos = []
            for i in range(start_index, len(doc_paragraphs)):
                p = doc_paragraphs[i]
                if p and re.search(r"(?<!\w)" + re.escape(a_norm) + r"(?!\w)", re.sub(r"\s+", " ", p.strip()).lower(), flags=re.IGNORECASE):
                    pos.append(i)
            return pos

        pos_before = find_positions(anchor_before)
        pos_after = find_positions(anchor_after)

        def candidate_ok(val, anchors):
            if not val or not val.strip(): return False
            v = val.strip()
            if self._is_anchor_like(v, anchors): return False
            if re.match(r"^\d+\.", v): return False # Нумерация списков
            if any(sw in v.lower() for sw in stop_words): return False
            if re.search(r"подпись|иниц|инициалы|фамил", v.lower()): return False
            if expected_type: return self._validate_type(v, expected_type)
            return True

        # Стратегия 1: Есть оба якоря
        if pos_before and pos_after:
            best_pair = None
            min_dist = 999
            for b in pos_before:
                for a in pos_after:
                    if b > a: continue
                    dist = a - b
                    if dist < min_dist:
                        min_dist = dist
                        best_pair = (b, a)
            
            if best_pair:
                b, a = best_pair
                if (a - b) <= 8 and not ((a - b) <= 1 or next_is_placeholder):
                     for k in range(b + 1, a):
                        mid = doc_paragraphs[k].strip()
                        if candidate_ok(mid, [anchor_before, anchor_after]):
                            return True, mid, k

        # Стратегия 2: Только якорь до
        if pos_before:
            for b in pos_before:
                para_b = doc_paragraphs[b] or ""
                # Проверка в той же строке
                ab = anchor_before.strip().lower()
                idx_b = para_b.lower().find(ab)
                if idx_b != -1:
                    after_b = para_b[idx_b + len(ab):].strip()
                    if candidate_ok(after_b, [anchor_before, anchor_after]): return True, after_b, b
                
                # Проверка следующих строк
                for k in range(b + 1, min(len(doc_paragraphs), b + 8)):
                    cand = doc_paragraphs[k] or ""
                    if not anchor_after and not cand.strip(): continue # пропускаем пустые если нет closing anchor
                    if anchor_after and not cand.strip(): break # пустая строка прерывает поиск если closing anchor важен
                    
                    if any(sw in cand.lower() for sw in stop_words): break
                    if re.search(r"^\(?\s*(подпись|иниц)", cand.lower()): break
                    
                    if candidate_ok(cand, [anchor_before, anchor_after]): return True, cand, k

        # Стратегия 3: Только якорь после (для дат в конце и т.д.)
        if pos_after:
            for a in pos_after:
                k = a - 1
                if k >= 0:
                    cand = doc_paragraphs[k] or ""
                    if candidate_ok(cand, [anchor_before, anchor_after]): return True, cand, k
                    
        return False, None, -1

    def check_document(self, doc_paragraphs: list) -> list:
        results = []
        cursor = 0
        for ph in self.template.get_placeholders():
            found, value, idx = self._find_value_using_anchors(
                ph.get("anchor_before"), ph.get("anchor_after"), doc_paragraphs, cursor, ph["type"], ph.get("next_is_placeholder")
            )
            
            res = {
                "field": ph["name"], "expected_type": ph["type"],
                "optional": ph["optional"], "value": value
            }
            if not found:
                res["status"] = "missing_optional" if ph["optional"] else "missing"
            else:
                is_valid = self._validate_type(value, ph["type"])
                res["status"] = "ok" if is_valid else "invalid"
                cursor = max(cursor, idx + 1)
            results.append(res)
        return results

# ============================================================
#  ЧАСТЬ 2: AGENT LAYER (Агент-Инспектор)
# ============================================================

class InspectorAgent:
    """Агент, который выполняет грязную работу по проверке"""
    
    def generate_report(self, template_path: str, document_path: str) -> str:
        try:
            # 1. Загрузка шаблона
            tpl = Template.load_from_file(template_path)
            
            # 2. Загрузка документа
            doc_paras = DocumentLoader.get_paragraphs(document_path)
            
            # 3. Проверка
            checker = DocumentChecker(tpl)
            results = checker.check_document(doc_paras)
            
            # 4. Генерация текста отчета
            lines = [f"📄 <b>Отчет проверки</b>", f"Файл: {os.path.basename(document_path)}", ""]
            
            errors_count = 0
            for r in results:
                icon = "✅"
                text = f"<b>{r['field']}</b>: {r.get('value', '')}"
                
                if r['status'] == 'invalid':
                    icon = "⚠️"
                    text += f" (ожидался тип {r['expected_type']})"
                    errors_count += 1
                elif r['status'] == 'missing':
                    icon = "❌"
                    text = f"<b>{r['field']}</b>: Не найдено!"
                    errors_count += 1
                elif r['status'] == 'missing_optional':
                    icon = "ℹ️"
                    text += " (не найдено, но не обязательно)"
                
                lines.append(f"{icon} {text}")
            
            status_summary = "\n\n🟢 <b>Документ прошел проверку</b>" if errors_count == 0 else f"\n\n🔴 <b>Найдено ошибок: {errors_count}</b>"
            lines.append(status_summary)
            
            return "\n".join(lines)
            
        except Exception as e:
            logging.error(e, exc_info=True)
            return f"🔥 <b>Критическая ошибка при проверке:</b>\n{str(e)}"

# ============================================================
#  ЧАСТЬ 3: ORCHESTRATOR (Telegram Bot)
# ============================================================

BOT_TOKEN = "8124707173:AAEUWIG6cU8ErdX_ItQZdbWNGD3JRLwjjNo"  # <--- ВСТАВИТЬ ТОКЕН

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Инициализация
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())
inspector = InspectorAgent()

# FSM Состояния
class Workflow(StatesGroup):
    waiting_for_template = State()
    waiting_for_document = State()

# Папка для временных файлов
TEMP_DIR = "temp_files"
os.makedirs(TEMP_DIR, exist_ok=True)

# --- Хендлеры ---

@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await message.answer(
        "👋 Привет! Я бот-контролер.\n\n"
        "Я работаю в режиме диалога:\n"
        "1. Сначала пришлите мне <b>ШАБЛОН</b> (.docx/.pdf) с тегами `[[field:type]]`\n"
        "2. Затем пришлите заполненный <b>ДОКУМЕНТ</b> для проверки.",
        parse_mode="HTML"
    )
    await state.set_state(Workflow.waiting_for_template)

@dp.message(Workflow.waiting_for_template, F.document)
async def process_template(message: types.Message, state: FSMContext):
    file_id = message.document.file_id
    file_name = message.document.file_name
    
    if not (file_name.endswith('.docx') or file_name.endswith('.pdf')):
        await message.answer("❌ Поддерживаются только .docx и .pdf файлы.")
        return

    # Скачиваем шаблон
    file = await bot.get_file(file_id)
    local_path = os.path.join(TEMP_DIR, f"tpl_{message.from_user.id}_{file_name}")
    await bot.download_file(file.file_path, local_path)
    
    # Сохраняем путь в контексте
    await state.update_data(template_path=local_path)
    
    await message.answer(f"✅ Шаблон <b>{file_name}</b> принят.\nТеперь пришлите документ для проверки.", parse_mode="HTML")
    await state.set_state(Workflow.waiting_for_document)

@dp.message(Workflow.waiting_for_document, F.document)
async def process_document(message: types.Message, state: FSMContext):
    data = await state.get_data()
    template_path = data.get("template_path")
    
    file_name = message.document.file_name
    
    msg = await message.answer("⏳ Агент-инспектор изучает документ...")
    
    # Скачиваем документ
    file = await bot.get_file(message.document.file_id)
    doc_path = os.path.join(TEMP_DIR, f"doc_{message.from_user.id}_{file_name}")
    await bot.download_file(file.file_path, doc_path)
    
    # ЗАПУСК АГЕНТА (в отдельном потоке, чтобы не блочить бота)
    report = await asyncio.to_thread(inspector.generate_report, template_path, doc_path)
    
    await msg.edit_text(report, parse_mode="HTML")
    
    # Очистка и сброс
    # (Опционально можно удалять файлы тут)
    await message.answer("Можете прислать следующий документ для проверки по этому же шаблону или нажмите /start для нового шаблона.")

@dp.message(Command("cancel"))
async def cmd_cancel(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Действие отменено. Жмите /start")

# --- Запуск ---

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
