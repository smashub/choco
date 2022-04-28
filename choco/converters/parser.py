from lark import Lark, Transformer, Tree


class BaseParser(object):
    def __init__(self, grammar: str, parser: str = "earley", encoder: Transformer = None):
        """Build parser using specified parsing engine and grammar.

        Parameters
        ----------
        grammar : str
            Grammar used by the parser
        parser : str, optional
            Parsing engine used by the parser, by default "earley" (safest one)
        encoder: Transformer, optional
            Encoder used to directly transform the parsed tree into a string, without
            spending time in building the tree representation
        """
        self.parser = Lark(grammar, parser=parser, transformer=encoder)

    def parse(self, chord: str) -> Tree:
        """Parse chord into tree

        Parameters
        ----------
        chord : str
            Input chord

        Returns
        -------
        Tree
            Tree built by using the specified grammar
        """
        return self.parser.parse(chord)
