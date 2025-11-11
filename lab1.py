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
# 31.10.2025
#
import re
import enum
from collections import OrderedDict

class FuzzySet:
    def __init__(self, membership: dict[str, float]):
        self._membership = OrderedDict(sorted(membership.items()))

    @property
    def membership(self) -> OrderedDict[str, float]:
        return self._membership

    @property
    def domain(self) -> tuple[str, ...]:
        return tuple(self._membership.keys())

    def __repr__(self) -> str:
        items = [f'<{key},{value:.2f}>' for key, value in self._membership.items()]
        return f"{{{', '.join(items)}}}"

    def __eq__(self, other) -> bool:
        if not isinstance(other, FuzzySet):
            return NotImplemented
        return self.domain == other.domain and all(
            abs(self.membership[k] - other.membership[k]) < 1e-9 for k in self.domain
        )

class FuzzyMap:
    def __init__(self, domain: tuple[str, ...], codomain: tuple[str, ...], matrix: list[list[float]]):
        self._domain = domain
        self._codomain = codomain
        self.matrix = matrix

    @property
    def domain(self) -> tuple[str, ...]:
        return self._domain

    @property
    def codomain(self) -> tuple[str, ...]:
        return self._codomain
        
    def __repr__(self) -> str:
        header = "     " + "   ".join(self.codomain)
        rows = []
        for i, row in enumerate(self.matrix):
            row_str = f"{self.domain[i]:2} | " + "  ".join(f"{val:4.2f}" for val in row)
            rows.append(row_str)
        return "Матрица отношения:\n" + header + "\n" + "\n".join(rows)
        
class Tnorm:
    def __call__(self, prop1: float, prop2: float) -> float:
        raise NotImplementedError

class Invertor:
    def __call__(self, prop: float) -> float:
        raise NotImplementedError

class Implicator:
    def __call__(self, first: float, second: float) -> float:
        raise NotImplementedError
        
class LogicalProduct(Tnorm):
    def __call__(self, prop1: float, prop2: float) -> float:
        return min(prop1, prop2)

class StandardInvertor(Invertor):
    def __call__(self, prop: float) -> float:
        return 1.0 - prop

class GodelImplicator(Implicator):
    def __call__(self, first: float, second: float) -> float:
        return 1.0 if first <= second else second

class ParseError(Exception):
    def __init__(self, string_index: int, *args: object) -> None:
        super().__init__(*args)
        self.string_index = string_index

class InductedImplicator(Implicator):
    def __init__(
        self,
        tnorm: Tnorm,
        invertor: Invertor,
    ) -> None:
        self.tnorm = tnorm
        self.invertor = invertor
        
    def __call__(self, first: float, second: float) -> float:
        return self.invertor(self.tnorm(first, self.invertor(second)))

class FuzzyLogicAlgebra:
    def __init__(
        self,
        invertor: Invertor = None,
        tnorm: Tnorm = None,
        implicator: Implicator = None,
    ) -> None:
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
        return self.invertor(prop)
        
    def conjunction(self, prop1: float, prop2: float) -> float:
        return self.tnorm(prop1, prop2)
    
    def disjunction(self, prop1: float, prop2: float) -> float:
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
        return self.implicator(prop1, prop2)
    
    def equivalence(self, prop1: float, prop2: float) -> float:
        return self.conjunction(
            self.impication(prop1, prop2),
            self.impication(prop2, prop1)
        )

class FuzzySetAlgebra:
    def __init__(
        self,
        logic_algebra: FuzzyLogicAlgebra,
    ) -> None:
        self.logic_algebra = logic_algebra
        
    def union(self, a: FuzzySet, b: FuzzySet) -> FuzzySet:
        membership = self.logic_algebra.disjunction(a.membership, b.membership)
        return FuzzySet(membership)
    
    def intersection(self, a: FuzzySet, b: FuzzySet) -> FuzzySet:
        if a.domain != b.domain:
            raise ValueError("Domains of fuzzy sets must be the same for intersection")
        
        result_membership = OrderedDict()
        for key in a.domain:
            result_membership[key] = self.logic_algebra.conjunction(a.membership[key], b.membership[key])
        return FuzzySet(result_membership)
        
    def complement(self, a: FuzzySet) -> FuzzySet:
        result_membership = OrderedDict()
        for key, value in a.membership.items():
             result_membership[key] = self.logic_algebra.negatiation(value)
        return FuzzySet(result_membership)

class FuzzyMapAlgebra:
    def __init__(self, set_algebra: FuzzySetAlgebra):
        self.set_algebra = set_algebra
        self.logic_algebra = set_algebra.logic_algebra

    def consequens(self, a: FuzzySet, b: FuzzySet, verbose: bool = False, set_name_a: str = "A", set_name_b: str = "B") -> FuzzyMap:
        if a.domain != b.domain:
            raise ValueError("Domains must be the same to create a relation.")
        
        domain = a.domain
        matrix = []
        
        if verbose:
            print(f"\n--- Построение матрицы отношения {set_name_a} → {set_name_b} ---")
            print("Импликация Гёделя: I(a,b) = 1 если a ≤ b, иначе b")
            print(f"{set_name_a} = {a}")
            print(f"{set_name_b} = {b}")
            print("\nВычисление элементов матрицы:")
        
        for i, x in enumerate(domain):
            row = []
            if verbose:
                print(f"\nДля x = {x} ({set_name_a}({x}) = {a.membership[x]:.2f}):")
            for j, y in enumerate(domain):
                a_val = a.membership[x]
                b_val = b.membership[y]
                val = self.logic_algebra.impication(a_val, b_val)
                row.append(val)
                if verbose:
                    print(f"  R({x},{y}) = I({a_val:.2f}, {b_val:.2f}) = {val:.2f}")
            matrix.append(row)
            
        if verbose:
            print(f"\nИтоговая матрица отношения {set_name_a}→{set_name_b}:")
            relation = FuzzyMap(domain, domain, matrix)
            print(relation)
            
        return FuzzyMap(domain, domain, matrix)

    def composition(self, a: FuzzySet, r: FuzzyMap, verbose: bool = False, set_name_a: str = "A", set_name_b: str = "B") -> FuzzySet:
        if a.domain != r.domain:
            raise ValueError("Domain of the set and the map must match for composition.")

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
                raise ValueError(f"Unknown lex at position")
        return tokens

class Parser:
    def __init__(
        self,
        set_algebra: FuzzyMapAlgebra,
        expression_spliter: Token = Token.expression_spliter,
        kb_spliter: list[Token] = None
    ):
        self.algebra = set_algebra
        self._expression_spliter = expression_spliter
        self.kb_spliter = None
    
    def parse(self, tokens: list[Token]) -> tuple[dict[str, FuzzySet], dict[str, tuple[FuzzyMap, str, str]]]:
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
        for i, string in enumerate(strings):
            if Token.consequens in string:
                sets_strings = strings[:i]
                rules_strings = strings[i:]
                return sets_strings, rules_strings
    
        return strings, []
    
    def _build_sets(self, strings: list[list[Token]]) -> dict[str, FuzzySet]:
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
                    raise ParseError(i + 1, f"Invalid set definition syntax at line {i+1}")
        return sets
    
    @staticmethod
    def _build_set(tokens: list[Token]) -> FuzzySet:
        membership = {}
        while tokens:
            if not isinstance(tokens[0], Token) or tokens[0] != Token.left_pair_bracket:
                raise ValueError("Expected '<' to start a pair")
            
            element = tokens[1]
            if not isinstance(element, str):
                raise ValueError(f"Expected a string element name, got {element}")
            
            if tokens[2] != Token.comma:
                raise ValueError("Expected ',' in pair")
            
            element_membership = tokens[3]
            if not isinstance(element_membership, float):
                 raise ValueError(f"Expected float for membership, got {element_membership}")
                 
            if tokens[4] != Token.right_pair_bracket:
                raise ValueError("Expected '>' to end a pair")

            membership[element] = element_membership
            
            tokens = tokens[5:]
            if tokens and tokens[0] == Token.comma:
                tokens = tokens[1:]
                        
        return FuzzySet(membership)
            
    def _build_rules(self, sets: dict[str, FuzzySet], strings: list[list[Token]]) -> dict[str, tuple[FuzzyMap, str, str]]:
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
                        raise ParseError(i + 1, f"There is no set with name {e.args[0]}") from e
                case _:
                    raise ParseError(i + 1, f"Invalid rule syntax at line {i+1}")
        
        return rules

def read_kb(filename: str, set_algebra: FuzzyMapAlgebra) -> tuple[dict[str, FuzzySet], dict[str, tuple[FuzzyMap, str, str]]]:
    with open(filename, 'r', encoding='utf-8') as file:
        content = file.read().replace(' ', '').replace('\r', '')
        tokens = Lexer().analyze(content)
        sets, rules = Parser(set_algebra).parse(tokens)  
        return sets, rules

def main():
    logic_algebra = FuzzyLogicAlgebra(implicator=GodelImplicator())
    set_algebra = FuzzySetAlgebra(logic_algebra)
    map_algebra = FuzzyMapAlgebra(set_algebra)

    try:
        sets, rules = read_kb('1.kb', map_algebra)

    except FileNotFoundError:
        print("Error: Knowledge base file '1.kb' not found.")
        print("Please create it and add data.")
        return
    except ParseError as e:
        print(f"Parse error at line {e.string_index}: {e}")
        return
    except ValueError as e:
        print(f"Value error during parsing: {e}")
        return

    queue = OrderedDict(sets)
    counter = 1
    
    processed_pairs = set()

    while queue:
        set_name, a = queue.popitem(last=False)
        
        for rule_str, (rule, antecedent, consequent) in rules.items():
            if set(rule.domain) != set(a.domain):
                continue
            
            if (set_name, rule_str) in processed_pairs:
                continue
            
            processed_pairs.add((set_name, rule_str))

            print(f"\n{'='*60}")
            print(f"ВЫЧИСЛЕНИЕ: {set_name} ● ({rule_str})")
            print(f"{'='*60}")
            
            if set_name == antecedent:
                result_name = consequent + "'"
            else:
                result_name = set_name + "'"
            
            inferrence = map_algebra.composition(
                a, rule, verbose=True, 
                set_name_a=set_name, 
                set_name_b=result_name
            )
            
            inferrence_name = None
            for n, s in sets.items():
                if inferrence == s:
                    inferrence_name = n
                    break
            
            if inferrence_name is None:
                inferrence_name = f'I{counter}'
                counter += 1
                queue[inferrence_name] = inferrence
                sets[inferrence_name] = inferrence
            
            print(f"\nРЕЗУЛЬТАТ: {set_name} ● ({rule_str}) => {inferrence_name} = {sets[inferrence_name]}")


if __name__ == '__main__':
    main()
