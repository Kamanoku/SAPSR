######################################################################################################
# Лабораторная работа 1 по дисциплине ЛОИС
# Выполненая студентами группы 221701 БГУИР Глёза Егором Дмитриевичем и Крупским Артёмом Викторович
#
# Класс индуцированного импликатора
#
# Источники:
# 
# - Нечёткая логика: алгебраическая основы и приложения: Монография / С.Л. Блюмин, И.А. Шуйкова,
#   П.В. Сараев, И.В. Черпаков. - Липецк: ЛЭГИ, 2002. - 111с. 
#
# 1.11.2024
#
from .tnorm import Tnorm
from .invertor import Invertor
from .implicator import Implicator


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
    
