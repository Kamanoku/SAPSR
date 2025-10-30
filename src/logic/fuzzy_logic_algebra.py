######################################################################################################
# Лабораторная работа 1 по дисциплине ЛОИС
# Выполненая студентами группы 221701 БГУИР Глёза Егором Дмитриевичем и Крупским Артёмом Викторович
#
# Класс алгебры нечёткой логики
#
# Источники:
# 
# - Нечёткая логика: алгебраическая основы и приложения: Монография / С.Л. Блюмин, И.А. Шуйкова,
#   П.В. Сараев, И.В. Черпаков. - Липецк: ЛЭГИ, 2002. - 111с. 
#
# 1.11.2024
#
from .tnorm import Tnorm, LogicalProduct
from .invertor import Invertor, StandardInvertor
from .implicator import Implicator
from .inducted_implicator import InductedImplicator 


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
        return self.invertor(
                self.tnorm(
                    self.invertor(prop1),
                    self.invertor(prop2)
                )
            )
    
    def impication(self, prop1: float, prop2: float) -> float:
        return self.implicator(prop1, prop2)
    
    def equivalence(self, prop1: float, prop2: float) -> float:
        return self.conjunction(
            self.impication(prop1, prop2),
            self.impication(prop2, prop1)
        )
        
