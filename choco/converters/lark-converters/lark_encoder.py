from lark import Transformer, Tree


class BaseEncoder(object):
    def __init__(self, transformer: Transformer):
        """Build parser using specified parsing engine and grammar.

        Parameters
        ----------
        transformer: Transformer
            Lark's transformer used to turn parsed tree into a new encoding
        """
        self.transformer = transformer

    def encode(self, tree: Tree) -> Tree:
        """Parse chord into tree

        Parameters
        ----------
        tree : Tree
            Input tree

        Returns
        -------
        Tree
            Tree built by using the specified grammar
        """
        return self.transformer.transform(tree)
