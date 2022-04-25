from lark import Lark
import os

dirname = os.path.dirname(__file__)
grammar_path = os.path.join(dirname, "grammar", "leadsheet.lark")
with open(grammar_path) as f:
  grammar = f.read()

parser = Lark(grammar, start='chord')
parse = parser.parse