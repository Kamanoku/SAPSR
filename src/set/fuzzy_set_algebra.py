######################################################################################################
# Лабораторная работа 1 по дисциплине ЛОИС
# Выполненая студентами группы 221701 БГУИР Глёза Егором Дмитриевичем и Крупским Артёмом Викторович
#
# Класс алгебры нечётких множеств
#
# Источники:
# 
# - Нечёткая логика: алгебраическая основы и приложения: Монография / С.Л. Блюмин, И.А. Шуйкова,
#   П.В. Сараев, И.В. Черпаков. - Липецк: ЛЭГИ, 2002. - 111с. 
#
# 1.11.2024
#
from .fuzzy_set import FuzzySet
from ..logic import FuzzyLogicAlgebra


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
        membership = self.logic_algebra.conjunction(a.membership, b.membership)
        return FuzzySet(membership)
        
    def complement(self, a: FuzzySet) -> FuzzySet:
        membership = self.logic_algebra.negatiation(a.membership)
        return FuzzySet(membership)
            
    
