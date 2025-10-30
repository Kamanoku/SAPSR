######################################################################################################
# Лабораторная работа 1 по дисциплине ЛОИС
# Выполненая студентами группы 221701 БГУИР Глёза Егором Дмитриевичем и Крупским Артёмом Викторович
#
# Утилиты для работы с базой знаний
#
# 1.11.2024
#
from .lexer import Lexer
from .parser import Parser
from ..set import FuzzySet
from ..map import FuzzyMap, FuzzyMapAlgebra


def read_kb(filename: str, set_algebra: FuzzyMapAlgebra) -> tuple[dict[str, FuzzySet], dict[str, FuzzyMap]]:
    with open(filename) as file:
        tokens = Lexer().analyze(file.read().replace(' ', ''))
        sets, rules = Parser(set_algebra).parse(tokens)
        return sets, rules
