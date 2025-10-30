######################################################################################################
# Лабораторная работа 1 по дисциплине ЛОИС
# Выполненая студентами группы 221701 БГУИР Глёза Егором Дмитриевичем и Крупским Артёмом Викторович
#
# Перечисление токенов для лексера
#
# 1.11.2024
#
import enum


class Token(enum.Enum):
    assignment = 0
    left_set_bracket = 1
    right_set_bracket = 2
    left_pair_bracket = 3
    right_pair_bracket = 4
    consequens = 5
    comma = 6,
    expression_spliter = 7
