######################################################################################################
# Лабораторная работа 1 по дисциплине ЛОИС
# Выполненая студентами группы 321702 БГУИР Бузычковым Никитой Фёдоровичем, Котко Павлом Анатольевичем и Халиловым Русланом Эльвировичем
#
# основной файл программы
#
# 31.10.2025
#
import numpy as np
from collections import OrderedDict

from src.parser import read_kb
from src.logic import FuzzyLogicAlgebra, GodelImplicator
from src.set import FuzzySetAlgebra
from src.map import FuzzyMapAlgebra
from src.exception import ParseError


def main():
    logic_algebra = FuzzyLogicAlgebra(implicator=GodelImplicator())
    set_algebra = FuzzySetAlgebra(logic_algebra)
    
    
    map_algebra = FuzzyMapAlgebra(set_algebra)

    try:
        sets, rules = read_kb('1.kb', map_algebra)
    except ParseError as e:
        print(f"Parse error at line {e.string_index}")
        return
    except ValueError as e:
        print(e)
        return

    queue = OrderedDict(sets)
    counter = 1
    while queue:
        set_name, a = queue.popitem(last=False)
        for rule_str, rule in rules.items():
            if set(rule.domain) != set(a.domain):
                continue
            
            inferrence = map_algebra.composition(a, rule)
            
            for n, s in sets.items():
                if inferrence == s:
                    inferrence_name = n
                    break
            else:
                inferrence_name = f'I{counter}'
                counter += 1
                queue[inferrence_name] = inferrence
                sets[inferrence_name] = inferrence
            
            print(f'{set_name}/~\\({rule_str}) = {inferrence_name} = {sets[inferrence_name]}')


if __name__ == '__main__':
    main()
