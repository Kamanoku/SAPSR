######################################################################################################
# Лабораторная работа 1 по дисциплине ЛОИС
# Выполненая студентами группы 221701 БГУИР Глёза Егором Дмитриевичем и Крупским Артёмом Викторович
#
# Класс парсера
#
# 1.11.2024
#
from ..set import FuzzySet
from ..map import FuzzyMap, FuzzyMapAlgebra  
from ..exception import ParseError

from .token import Token

    
class Parser:
    def __init__(
        self,
        set_algebra: FuzzyMapAlgebra,
        expression_spliter: Token = Token.expression_spliter,
        kb_spliter: list[Token] = None
    ):
        self.algebra = set_algebra
        self._expression_spliter = expression_spliter
        if kb_spliter is None:
            self.kb_spliter = []
    
    def parse(self, tokens: list[Token]) -> tuple[dict[str, FuzzySet], dict[str, FuzzyMap]]:
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
                strings.append(string)
                string = []
            else:
                string.append(token)
        return strings
    
    def _split_kb(self, strings: list[list[Token]]) -> tuple[list[list[Token]], list[list[Token]]]:
        try:
            kb_spliter_index = strings.index(self.kb_spliter)
        except ValueError:
            raise ValueError("No empty string in kb file")
        sets_strings = strings[:kb_spliter_index]
        rules_strings = strings[kb_spliter_index + 1:]
        return sets_strings, rules_strings
    
    def _build_sets(self, strings: list[Token]) -> dict[str, FuzzySet]:
        sets = {}
        counter = 0
        for string in strings:
            counter += 1
            match string:
                case (str() as var,
                    Token.assignment,
                    Token.left_set_bracket,
                    *subformula,
                    Token.right_set_bracket):
                    sets[var] = self._build_set(subformula)
                case _:
                    raise ParseError(strings.index(string))
        return sets
    
    @staticmethod
    def _build_set(tokens: list[Token]) -> FuzzySet:
        membership = {}
        while tokens:
            match tokens:
                case (Token.left_pair_bracket,
                    str() as element,
                    Token.comma,
                    float() as element_membership,
                    Token.right_pair_bracket,
                    Token.comma,
                    *subformula)|\
                        (Token.left_pair_bracket,
                    str() as element,
                    Token.comma,
                    float() as element_membership,
                    Token.right_pair_bracket,
                    *subformula):
                        membership[element] = element_membership
                        tokens = subformula
                        
        return FuzzySet(membership)
            
    def _build_rules(self, sets: dict[str, FuzzyMap], strings: list[Token]) -> dict[str, FuzzyMap]:
        rules = {}
        for string in strings:
            match string:
                case (str() as antecedent,
                    Token.consequens,
                    str() as consequent):
                    try:
                        rules[f'{antecedent}~>{consequent}'] = self.algebra.consequens(sets[antecedent], sets[consequent])
                    except KeyError as e:
                        raise ParseError(strings.index(string), f"There is no set with name {e.args[0]}") from e
                case _:
                    raise ParseError(strings.index(string))
        
        return rules
    
