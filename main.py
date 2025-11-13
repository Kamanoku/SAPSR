######################################################################################################
# Лабораторная работа 1 по дисциплине ЛОИС
# Выполненая студентами группы 321702 БГУИР Бузычковым Никитой Фёдоровичем, Котко Павлом Анатольевичем и Халиловым Русланом Эльвировичем
#
# основной файл программы
#
# Источники:
# 
# - Нечёткая логика: алгебраическая основы и приложения: Монография / С.Л. Блюмин, И.А. Шуйкова,
#   П.В. Сараев, И.В. Черпаков. - Липецк: ЛЭГИ, 2002. - 111с. 
#
# 14.11.2025
#
import re
import enum
from collections import OrderedDict

class FuzzySet:
    """Класс для представления нечёткого множества"""
    
    def __init__(self, membership: dict[str, float]):
        """
        Инициализация нечёткого множества
        
        Аргументы:
            membership: словарь элементов и их степеней принадлежности
        """
        self._membership = OrderedDict(sorted(membership.items()))

    @property
    def membership(self) -> OrderedDict[str, float]:
        """Возвращает словарь принадлежностей элементов"""
        return self._membership

    @property
    def domain(self) -> tuple[str, ...]:
        """Возвращает домен (универсум) множества"""
        return tuple(self._membership.keys())

    def __repr__(self) -> str:
        """Строковое представление нечёткого множества"""
        items = [f'<{key},{value:.2f}>' for key, value in self._membership.items()]
        return f"{{{', '.join(items)}}}"

    def __eq__(self, other) -> bool:
        """Проверка равенства двух нечётких множеств"""
        if not isinstance(other, FuzzySet):
            return NotImplemented
        return self.domain == other.domain and all(
            abs(self.membership[k] - other.membership[k]) < 1e-9 for k in self.domain
        )

class FuzzyMap:
    """Класс для представления нечёткого отношения (отображения)"""
    
    def __init__(self, domain: tuple[str, ...], codomain: tuple[str, ...], matrix: list[list[float]]):
        """
        Инициализация нечёткого отношения
        
        Аргументы:
            domain: домен отношения
            codomain: кодомен отношения  
            matrix: матрица принадлежностей
        """
        self._domain = domain
        self._codomain = codomain
        self.matrix = matrix

    @property
    def domain(self) -> tuple[str, ...]:
        """Возвращает домен отношения"""
        return self._domain

    @property
    def codomain(self) -> tuple[str, ...]:
        """Возвращает кодомен отношения"""
        return self._codomain
        
    def __repr__(self) -> str:
        """Строковое представление матрицы отношения"""
        header = "     " + "   ".join(self.codomain)
        rows = []
        for i, row in enumerate(self.matrix):
            row_str = f"{self.domain[i]:2} | " + "  ".join(f"{val:4.2f}" for val in row)
            rows.append(row_str)
        return "Матрица отношения:\n" + header + "\n" + "\n".join(rows)
        
class Tnorm:
    """Базовый класс для T-норм (операция конъюнкции)"""
    
    def __call__(self, prop1: float, prop2: float) -> float:
        """Вычисление T-нормы для двух значений"""
        raise NotImplementedError

class Invertor:
    """Базовый класс для инверторов (операция отрицания)"""
    
    def __call__(self, prop: float) -> float:
        """Вычисление отрицания значения"""
        raise NotImplementedError

class Implicator:
    """Базовый класс для импликаторов (операция импликации)"""
    
    def __call__(self, first: float, second: float) -> float:
        """Вычисление импликации для двух значений"""
        raise NotImplementedError
        
class LogicalProduct(Tnorm):
    """T-норма: логическое произведение (минимум)"""
    
    def __call__(self, prop1: float, prop2: float) -> float:
        """
        Вычисление логического произведения
        
        Аргументы:
            prop1: первое значение
            prop2: второе значение
            
        Возвращает:
            минимум из двух значений
        """
        return min(prop1, prop2)

class StandardInvertor(Invertor):
    """Стандартный инвертор (дополнение до 1)"""
    
    def __call__(self, prop: float) -> float:
        """
        Вычисление стандартного отрицания
        
        Аргументы:
            prop: исходное значение
            
        Возвращает:
            1 - prop
        """
        return 1.0 - prop

class GodelImplicator(Implicator):
    """Импликатор Гёделя"""
    
    def __call__(self, first: float, second: float) -> float:
        """
        Вычисление импликации по Гёделю
        
        Аргументы:
            first: первое значение
            second: второе значение
            
        Возвращает:
            1 если first ≤ second, иначе second
        """
        return 1.0 if first <= second else second

class ParseError(Exception):
    """Класс ошибок парсинга"""
    
    def __init__(self, string_index: int, *args: object) -> None:
        """
        Инициализация ошибки парсинга
        
        Аргументы:
            string_index: индекс строки с ошибкой
            *args: дополнительные аргументы
        """
        super().__init__(*args)
        self.string_index = string_index

class InductedImplicator(Implicator):
    """Индуцированный импликатор через T-норму и инвертор"""
    
    def __init__(
        self,
        tnorm: Tnorm,
        invertor: Invertor,
    ) -> None:
        """
        Инициализация индуцированного импликатора
        
        Аргументы:
            tnorm: T-норма для использования
            invertor: инвертор для использования
        """
        self.tnorm = tnorm
        self.invertor = invertor
        
    def __call__(self, first: float, second: float) -> float:
        """
        Вычисление индуцированной импликации
        
        Аргументы:
            first: первое значение
            second: второе значение
            
        Возвращает:
            инвертор(T-норма(first, инвертор(second)))
        """
        return self.invertor(self.tnorm(first, self.invertor(second)))

class FuzzyLogicAlgebra:
    """Алгебра нечёткой логики с операциями над значениями принадлежности"""
    
    def __init__(
        self,
        invertor: Invertor = None,
        tnorm: Tnorm = None,
        implicator: Implicator = None,
    ) -> None:
        """
        Инициализация алгебры нечёткой логики
        
        Аргументы:
            invertor: инвертор (по умолчанию стандартный)
            tnorm: T-норма (по умолчанию логическое произведение)
            implicator: импликатор (по умолчанию индуцированный)
        """
        if invertor is None:
            invertor = StandardInvertor()
            
        if tnorm is None:
            tnorm = LogicalProduct()
        
        if implicator is None:
            implicator = InductedImplicator(tnorm, invertor)
            
        self.tnorm = tnorm
        self.invertor = invertor
        self.implicator = implicator
     
    def negatiation(self, prop: float) -> float:
        """
        Операция отрицания
        
        Аргументы:
            prop: исходное значение
            
        Возвращает:
            отрицание значения
        """
        return self.invertor(prop)
        
    def conjunction(self, prop1: float, prop2: float) -> float:
        """
        Операция конъюнкции
        
        Аргументы:
            prop1: первое значение
            prop2: второе значение
            
        Возвращает:
            конъюнкция значений
        """
        return self.tnorm(prop1, prop2)
    
    def disjunction(self, prop1: float, prop2: float) -> float:
        """
        Операция дизъюнкции
        
        Аргументы:
            prop1: первое значение или словарь принадлежностей
            prop2: второе значение или словарь принадлежностей
            
        Возвращает:
            дизъюнкция значений
        """
        prop1_vals = list(prop1.values()) if isinstance(prop1, OrderedDict) else [prop1]
        prop2_vals = list(prop2.values()) if isinstance(prop2, OrderedDict) else [prop2]
        
        inverted1 = [self.invertor(p) for p in prop1_vals]
        inverted2 = [self.invertor(p) for p in prop2_vals]

        keys = list(prop1.keys()) if isinstance(prop1, OrderedDict) else range(len(inverted1))

        result_membership = OrderedDict()
        for i, key in enumerate(keys):
            tnorm_result = self.tnorm(inverted1[i], inverted2[i])
            result_membership[key] = self.invertor(tnorm_result)
            
        return result_membership
    
    def impication(self, prop1: float, prop2: float) -> float:
        """
        Операция импликации
        
        Аргументы:
            prop1: первое значение
            prop2: второе значение
            
        Возвращает:
            импликация значений
        """
        return self.implicator(prop1, prop2)
    
    def equivalence(self, prop1: float, prop2: float) -> float:
        """
        Операция эквивалентности
        
        Аргументы:
            prop1: первое значение
            prop2: второе значение
            
        Возвращает:
            эквивалентность значений
        """
        return self.conjunction(
            self.impication(prop1, prop2),
            self.impication(prop2, prop1)
        )

class FuzzySetAlgebra:
    """Алгебра операций над нечёткими множествами"""
    
    def __init__(
        self,
        logic_algebra: FuzzyLogicAlgebra,
    ) -> None:
        """
        Инициализация алгебры нечётких множеств
        
        Аргументы:
            logic_algebra: алгебра логики для базовых операций
        """
        self.logic_algebra = logic_algebra
        
    def _align_domains(self, a: FuzzySet, b: FuzzySet) -> tuple[list[str], dict[str, float], dict[str, float]]:
        """
        Выравнивание доменов двух нечётких множеств
        
        Аргументы:
            a: первое нечёткое множество
            b: второе нечёткое множество
            
        Возвращает:
            кортеж (объединённые ключи, принадлежности первого множества, принадлежности второго множества)
        """
        all_keys = sorted(set(a.domain) | set(b.domain))
        a_membership = {k: a.membership.get(k, 0.0) for k in all_keys}
        b_membership = {k: b.membership.get(k, 0.0) for k in all_keys}
        return all_keys, a_membership, b_membership

    def union(self, a: FuzzySet, b: FuzzySet) -> FuzzySet:
        """
        Объединение нечётких множеств
        
        Аргументы:
            a: первое нечёткое множество
            b: второе нечёткое множество
            
        Возвращает:
            новое нечёткое множество - объединение a и b
        """
        all_keys, a_m, b_m = self._align_domains(a, b)
        membership = OrderedDict()
        for k in all_keys:
            membership[k] = max(a_m[k], b_m[k])
        return FuzzySet(membership)

    def intersection(self, a: FuzzySet, b: FuzzySet) -> FuzzySet:
        """
        Пересечение нечётких множеств
        
        Аргументы:
            a: первое нечёткое множество
            b: второе нечёткое множество
            
        Возвращает:
            новое нечёткое множество - пересечение a и b
        """
        all_keys, a_m, b_m = self._align_domains(a, b)
        membership = OrderedDict()
        for k in all_keys:
            membership[k] = min(a_m[k], b_m[k])
        return FuzzySet(membership)
        
    def complement(self, a: FuzzySet) -> FuzzySet:
        """
        Дополнение нечёткого множества
        
        Аргументы:
            a: исходное множество
            
        Возвращает:
            дополнение множества
        """
        result_membership = OrderedDict()
        for key, value in a.membership.items():
             result_membership[key] = self.logic_algebra.negatiation(value)
        return FuzzySet(result_membership)

class FuzzyMapAlgebra:
    """Алгебра операций над нечёткими отношениями"""
    
    def __init__(self, set_algebra: FuzzySetAlgebra):
        """
        Инициализация алгебры нечётких отношений
        
        Аргументы:
            set_algebra: алгебра множеств для базовых операций
        """
        self.set_algebra = set_algebra
        self.logic_algebra = set_algebra.logic_algebra

    def consequens(self, a: FuzzySet, b: FuzzySet, verbose=False, set_name_a="A", set_name_b="B") -> FuzzyMap:
        """
        Создание нечёткого отношения следования
        
        Аргументы:
            a: первое нечёткое множество (антецедент)
            b: второе нечёткое множество (консеквент)
            verbose: флаг подробного вывода
            set_name_a: имя первого множества для вывода
            set_name_b: имя второго множества для вывода
            
        Возвращает:
            нечёткое отношение следования между множествами
        """
        all_keys = sorted(set(a.domain) | set(b.domain))
        a_m = {k: a.membership.get(k, 0.0) for k in all_keys}
        b_m = {k: b.membership.get(k, 0.0) for k in all_keys}

        matrix = []
        if verbose:
            print(f"\n--- Построение матрицы отношения {set_name_a} → {set_name_b} ---")
            print("Импликация Гёделя: I(a,b) = 1 если a ≤ b, иначе b")
            print(f"{set_name_a} = {a}")
            print(f"{set_name_b} = {b}")
            print("\nВычисление элементов матрицы:")

        for x in all_keys:
            row = []
            for y in all_keys:
                val = self.logic_algebra.impication(a_m[x], b_m[y])
                row.append(val)
                if verbose:
                    print(f"  R({x},{y}) = I({a_m[x]:.2f}, {b_m[y]:.2f}) = {val:.2f}")
            matrix.append(row)

        relation = FuzzyMap(tuple(all_keys), tuple(all_keys), matrix)
        if verbose:
            print(f"\nРезультат:\n{relation}")
        return relation

    def composition(self, a: FuzzySet, r: FuzzyMap, verbose: bool = False, set_name_a: str = "A", set_name_b: str = "B") -> FuzzySet:
        """
        Композиция нечёткого множества с отношением
        
        Аргументы:
            a: нечёткое множество
            r: нечёткое отношение
            verbose: флаг подробного вывода
            set_name_a: имя множества для вывода
            set_name_b: имя результата для вывода
            
        Возвращает:
            результат композиции
            
        Вызывает:
            ValueError: если домен множества и отношения не совпадают
        """
        if a.domain != r.domain:
            raise ValueError("Домен множества и отношения должны совпадать для композиции.")

        result_membership = OrderedDict()
        codomain_len = len(r.codomain)
        
        if verbose:
            print(f"\n--- Композиция {set_name_a} ∘ R ---")
            print(f"Формула: {set_name_b}(y) = maxₓ [min({set_name_a}(x), R(x,y))]")
            print(f"{set_name_a} = {a}")
            print(f"R = {r}")
            print("\nВычисления:")
        
        for j in range(codomain_len):
            y = r.codomain[j]
            max_val = 0.0
            calculations = []
            
            for i in range(len(r.domain)):
                x = r.domain[i]
                a_val = a.membership[x]
                r_val = r.matrix[i][j]
                val = self.logic_algebra.tnorm(a_val, r_val)
                calculations.append(f"min({a_val:.2f}, {r_val:.2f}) = {val:.2f}")
                if val > max_val:
                    max_val = val
                    
            result_membership[y] = max_val
            
            if verbose:
                calc_str = ", ".join(calculations)
                print(f"  {set_name_b}({y}) = max({calc_str}) = {max_val:.2f}")
            
        if verbose:
            print(f"\nРезультат композиции: {FuzzySet(result_membership)}")
            
        return FuzzySet(result_membership)
        
class Token(enum.Enum):
    """Перечисление токенов для лексического анализа"""
    assignment = 0
    left_set_bracket = 1
    right_set_bracket = 2
    left_pair_bracket = 3
    right_pair_bracket = 4
    consequens = 5
    comma = 6
    expression_spliter = 7

var_pattern = re.compile(r"^[a-zA-Z]\w*")
float_pattern = re.compile(r"^(0(\.\d*)?|1(\.0*)?)")

class Lexer:
    """Лексический анализатор для разбора входного текста"""
    
    prefix_lex_cutters = {
        Token.assignment: lambda x: x.removeprefix('='),
        Token.left_set_bracket: lambda x: x.removeprefix('{'),
        Token.right_set_bracket: lambda x: x.removeprefix('}'),
        Token.left_pair_bracket: lambda x: x.removeprefix('<'),
        Token.right_pair_bracket: lambda x: x.removeprefix('>'),
        Token.consequens: lambda x: x.removeprefix('~>'),
        Token.comma: lambda x: x.removeprefix(','),
        Token.expression_spliter: lambda x: x.removeprefix('\n'),
    }

    def analyze(self, string: str) -> list[Token | str | float]:
        """
        Лексический анализ входной строки
        
        Аргументы:
            string: входная строка для анализа
            
        Возвращает:
            список токенов
            
        Вызывает:
            ValueError: при обнаружении неизвестной лексемы
        """
        tokens = []
        while string:
            original_string_len = len(string)
            
            if r := var_pattern.match(string):
                var_name = r.group(0)
                tokens.append(var_name)
                string = string[len(var_name):]
            elif r := float_pattern.match(string):
                float_val = float(r.group(0))
                tokens.append(float_val)
                string = string[len(r.group(0)):]
            
            else:
                found_token = False
                for token_type, cutter in self.prefix_lex_cutters.items():
                    string_without_lex = cutter(string)
                    if len(string_without_lex) < len(string):
                        tokens.append(token_type)
                        string = string_without_lex
                        found_token = True
                        break
            
            if len(string) == original_string_len:
                raise ValueError(f"Неизвестная лексема на позиции")
        return tokens

class Parser:
    """Синтаксический анализатор для построения AST"""
    
    def __init__(
        self,
        set_algebra: FuzzyMapAlgebra,
        expression_spliter: Token = Token.expression_spliter,
        kb_spliter: list[Token] = None
    ):
        """
        Инициализация парсера
        
        Аргументы:
            set_algebra: алгебра для операций с множествами
            expression_spliter: токен-разделитель выражений
            kb_spliter: список токенов-разделителей базы знаний
        """
        self.algebra = set_algebra
        self._expression_spliter = expression_spliter
        self.kb_spliter = None
    
    def parse(self, tokens: list[Token]) -> tuple[dict[str, FuzzySet], dict[str, tuple[FuzzyMap, str, str]]]:
        """
        Парсинг списка токенов
        
        Аргументы:
            tokens: список токенов для разбора
            
        Возвращает:
            кортеж (словарь множеств, словарь правил)
        """
        strings = self._split_expressions(tokens)
        set_strings, rule_strings = self._split_kb(strings)
        sets = self._build_sets(set_strings)
        try:
            rules = self._build_rules(sets, rule_strings)
        except ParseError as e:
            e.string_index += len(set_strings) + 1
            raise e
        return sets, rules

    def _split_expressions(self, tokens: list[Token]) -> list[list[Token]]:
        """
        Разделение токенов на выражения
        
        Аргументы:
            tokens: список всех токенов
            
        Возвращает:
            список выражений (каждое выражение - список токенов)
        """
        strings = []
        string = []
        for token in tokens:
            if token == self._expression_spliter:
                if string:
                    strings.append(string)
                string = []
            else:
                string.append(token)
        if string:
            strings.append(string)
        return strings
    
    def _split_kb(self, strings: list[list[Token]]) -> tuple[list[list[Token]], list[list[Token]]]:
        """
        Разделение выражений на множества и правила
        
        Аргументы:
            strings: список выражений
            
        Возвращает:
            кортеж (выражения множеств, выражения правил)
        """
        for i, string in enumerate(strings):
            if Token.consequens in string:
                sets_strings = strings[:i]
                rules_strings = strings[i:]
                return sets_strings, rules_strings
    
        return strings, []
    
    def _build_sets(self, strings: list[list[Token]]) -> dict[str, FuzzySet]:
        """
        Построение словаря нечётких множеств из выражений
        
        Аргументы:
            strings: выражения для построения множеств
            
        Возвращает:
            словарь имён и нечётких множеств
            
        Вызывает:
            ParseError: при синтаксической ошибке в определении множества
        """
        sets = {}
        for i, string in enumerate(strings):
            match string:
                case [str() as var,
                    Token.assignment,
                    Token.left_set_bracket,
                    *subformula,
                    Token.right_set_bracket]:
                    sets[var] = self._build_set(subformula)
                case _:
                    raise ParseError(i + 1, f"Недопустимый синтаксис определения множества в строке {i+1}")
        return sets
    
    @staticmethod
    def _build_set(tokens: list[Token]) -> FuzzySet:
        """
        Построение нечёткого множества из токенов
        
        Аргументы:
            tokens: токены определения множества
            
        Возвращает:
            нечёткое множество
            
        Вызывает:
            ValueError: при синтаксической ошибке в определении пары
        """
        membership = {}
        while tokens:
            if not isinstance(tokens[0], Token) or tokens[0] != Token.left_pair_bracket:
                raise ValueError("Ожидался символ '<' для начала пары")
            
            element = tokens[1]
            if not isinstance(element, str):
                raise ValueError(f"Ожидалось строковое имя элемента, получено {element}")
            
            if tokens[2] != Token.comma:
                raise ValueError("Ожидался символ ',' в паре")
            
            element_membership = tokens[3]
            if not isinstance(element_membership, float):
                 raise ValueError(f"Ожидалось число с плавающей точкой для степени принадлежности, получено {element_membership}")
                 
            if tokens[4] != Token.right_pair_bracket:
                raise ValueError("Ожидался символ '>' для конца пары")

            membership[element] = element_membership
            
            tokens = tokens[5:]
            if tokens and tokens[0] == Token.comma:
                tokens = tokens[1:]
                        
        return FuzzySet(membership)
            
    def _build_rules(self, sets: dict[str, FuzzySet], strings: list[list[Token]]) -> dict[str, tuple[FuzzyMap, str, str]]:
        """
        Построение словаря правил из выражений
        
        Аргументы:
            sets: словарь множеств для ссылок в правилах
            strings: выражения правил
            
        Возвращает:
            словарь правил (имя правила -> (отношение, антецедент, консеквент))
            
        Вызывает:
            ParseError: при синтаксической ошибке или отсутствующем множестве
        """
        rules = {}
        for i, string in enumerate(strings):
            match string:
                case [str() as antecedent,
                    Token.consequens,
                    str() as consequent]:
                    try:
                        rule_name = f'{antecedent}~>{consequent}'
                        relation = self.algebra.consequens(
                            sets[antecedent], 
                            sets[consequent], 
                            verbose=True, 
                            set_name_a=antecedent, 
                            set_name_b=consequent
                        )
                        rules[rule_name] = (relation, antecedent, consequent)
                    except KeyError as e:
                        raise ParseError(i + 1, f"Не существует множества с именем {e.args[0]}") from e
                case _:
                    raise ParseError(i + 1, f"Недопустимый синтаксис правила в строке {i+1}")
        
        return rules

def read_kb(filename: str, set_algebra: FuzzyMapAlgebra) -> tuple[dict[str, FuzzySet], dict[str, tuple[FuzzyMap, str, str]]]:
    """
    Чтение базы знаний из файла
    
    Аргументы:
        filename: имя файла базы знаний
        set_algebra: алгебра для операций с множествами
        
    Возвращает:
        кортеж (словарь множеств, словарь правил)
    """
    with open(filename, 'r', encoding='utf-8') as file:
        content = file.read().replace(' ', '').replace('\r', '')
        tokens = Lexer().analyze(content)
        sets, rules = Parser(set_algebra).parse(tokens)  
        return sets, rules

def main():
    """
    Основная функция программы - выполнение нечёткого логического вывода
    с возможностью интерактивного выбора множеств для импликации и композиции.
    """
    logic_algebra = FuzzyLogicAlgebra(implicator=GodelImplicator())
    set_algebra = FuzzySetAlgebra(logic_algebra)
    map_algebra = FuzzyMapAlgebra(set_algebra)

    try:
        sets, rules = read_kb('1.kb', map_algebra)

    except FileNotFoundError:
        print("Ошибка: Файл базы знаний '1.kb' не найден.")
        print("Пожалуйста, создайте его и добавьте данные.")
        return
    except ParseError as e:
        print(f"Ошибка разбора в строке {e.string_index}: {e}")
        return
    except ValueError as e:
        print(f"Ошибка значения во время разбора: {e}")
        return

    print("\nЗагруженные нечёткие множества:")
    for name, fset in sets.items():
        print(f"  {name} = {fset}")

    print("\nДоступные операции: построить импликацию и композицию между выбранными множествами.")
    print("Введите 'exit' в любое время, чтобы выйти.")

    while True:
        print("\n-----------------------------------------")
        antecedent_name = input("Введите имя первого множества (антецедент, 'если ...'): ").strip()
        if antecedent_name.lower() == "exit":
            break
        consequent_name = input("Введите имя второго множества (консеквент, 'то ...'): ").strip()
        if consequent_name.lower() == "exit":
            break

        if antecedent_name not in sets or consequent_name not in sets:
            print("Ошибка: одно из указанных множеств не найдено. Попробуйте снова.")
            continue

        a = sets[antecedent_name]
        b = sets[consequent_name]

        print(f"\n{'='*60}")
        print(f"ПОСТРОЕНИЕ ИМПЛИКАЦИИ: {antecedent_name} ~> {consequent_name}")
        print(f"{'='*60}")

        relation = map_algebra.consequens(
            a, b, verbose=True, set_name_a=antecedent_name, set_name_b=consequent_name
        )

        print(f"\n{'='*60}")
        print(f"КОМПОЗИЦИЯ: {antecedent_name} ∘ R({antecedent_name}→{consequent_name})")
        print(f"{'='*60}")

        all_keys = sorted(set(a.domain) | set(relation.domain))
        a_membership = OrderedDict((k, a.membership.get(k, 0.0)) for k in all_keys)
        aligned_a = FuzzySet(a_membership)

        aligned_rule_matrix = []
        for x in all_keys:
            row = []
            if x in relation.domain:
                i = relation.domain.index(x)
            else:
                i = None
            for y in all_keys:
                if i is not None and y in relation.codomain:
                    j = relation.codomain.index(y)
                    val = relation.matrix[i][j]
                else:
                    val = 0.0
                row.append(val)
            aligned_rule_matrix.append(row)

        aligned_relation = FuzzyMap(tuple(all_keys), tuple(all_keys), aligned_rule_matrix)

        result_set = map_algebra.composition(
            aligned_a, aligned_relation, verbose=True,
            set_name_a=antecedent_name,
            set_name_b=consequent_name + "'"
        )

        print(f"\n РЕЗУЛЬТАТ: {antecedent_name} ∘ ({antecedent_name}~>{consequent_name}) = {consequent_name}' = {result_set}")

    print("\nРабота программы завершена.")

if __name__ == '__main__':
    main()
