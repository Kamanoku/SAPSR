######################################################################################################
# Лабораторная работа 1 по дисциплине ЛОИС
# Выполненая студентами группы 221701 БГУИР Глёза Егором Дмитриевичем и Крупским Артёмом Викторович
#
# инициализация пакета logic
#
# 1.11.2024
#
from .fuzzy_logic_algebra import FuzzyLogicAlgebra
from .implicator import Implicator, GodelImplicator
from .inducted_implicator import InductedImplicator
from .invertor import Invertor, StandardInvertor
from .tnorm import Tnorm, LogicalProduct


__all__ = [
    'FuzzyLogicAlgebra',
    'Implicator',
    'GodelImplicator',
    'InductedImplicator',
    'Invertor',
    'StandardInvertor',
    'Tnorm',
    'LogicalProduct',
]
