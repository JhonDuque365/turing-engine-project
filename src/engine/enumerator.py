"""
Módulo enumerador de cadenas binarias.
Implementa el concepto de enumerador de la Teoría de la Computación:
un procedimiento que genera todas las cadenas de un lenguaje en orden.
"""
from itertools import product


class BinaryEnumerator:
    """
    Enumerador de cadenas sobre {0, 1} en orden canónico por longitud.
    Genera: ε, 0, 1, 00, 01, 10, 11, 000, ...
    """

    @staticmethod
    def enumerate(limit: int = 20, alphabet: list = None) -> list[str]:
        """
        Genera las primeras 'limit' cadenas del lenguaje.
        Retorna lista de cadenas en orden ε, 0, 1, 00, 01, ...
        """
        if alphabet is None:
            alphabet = ['0', '1']
        result = ['']
        length = 1
        while len(result) < limit:
            for combo in product(alphabet, repeat=length):
                result.append(''.join(combo))
                if len(result) >= limit:
                    break
            length += 1
        return result[:limit]

    @staticmethod
    def enumerate_palindromes(limit: int = 10, alphabet: list = None) -> list[str]:
        """
        Enumera solo los palíndromos sobre el alfabeto dado.
        Filtra cadenas que cumplen la propiedad decidible w = w^R.
        """
        if alphabet is None:
            alphabet = ['0', '1']
        results = []
        length = 0
        while len(results) < limit:
            for combo in product(alphabet, repeat=length):
                s = ''.join(combo)
                if s == s[::-1]:
                    results.append(s)
                if len(results) >= limit:
                    break
            length += 1
        return results[:limit]


if __name__ == '__main__':
    print("Cadenas binarias (primeras 20):")
    for i, s in enumerate(BinaryEnumerator.enumerate(20)):
        label = 'ε' if s == '' else s
        print(f"  {i}: {label}")

    print("\nPalíndromos binarios (primeros 10):")
    for i, s in enumerate(BinaryEnumerator.enumerate_palindromes(10)):
        label = 'ε' if s == '' else s
        print(f"  {i}: {label}")
