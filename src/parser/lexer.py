######################################################################################################
# Лабораторная работа 1 по дисциплине ЛОИС
# Выполненая студентами группы 221701 БГУИР Глёза Егором Дмитриевичем и Крупским Артёмом Викторович
#
# Класс лексера
#
# 1.11.2024
#
import re

from .token import Token

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
            new_string = self._variable_cutter(tokens, string)
            new_string = self._float_cutter(tokens, new_string)
            for token_type in self.prefix_lex_cutters:
                string_without_lex = self.prefix_lex_cutters[token_type](new_string)
                if string_without_lex != new_string:
                    tokens.append(token_type)
                    new_string = string_without_lex
            if new_string == string:
                raise ValueError(f"Unknown lex at {len(tokens)+1} position")
            string = new_string
        return tokens

    def _variable_cutter(self, tokens: list[Token | str], string: str) -> str:
        if r := var_pattern.match(string):
            tokens.append(f := r.group(0))
            return string[len(f):]
        return string
    
    
    def _float_cutter(self, tokens: list[Token | str], string: str) -> str:
        if r := float_pattern.match(string):
            tokens.append(float(f := r.group(0)))
            return string[len(f):]
        return string
