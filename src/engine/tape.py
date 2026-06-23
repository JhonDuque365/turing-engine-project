class Tape:
    """
    Representa la cinta de una Máquina de Turing.
    Implementada como un diccionario para soporte de cinta infinita.
    El índice 0 corresponde a la celda inicial (leftmost de la entrada).
    """

    def __init__(self, blank: str = '_'):
        self.blank = blank
        self._cells: dict[int, str] = {}
        self._min_visited = 0
        self._max_visited = 0
        self._visited: set[int] = set()

    def write_input(self, input_string: str) -> None:
        """Escribe la cadena de entrada desde la posición 0."""
        self._cells = {}
        for i, symbol in enumerate(input_string):
            self._cells[i] = symbol

    def read(self, position: int) -> str:
        """Lee el símbolo en la posición indicada. Retorna blanco si está fuera del área escrita."""
        self._visited.add(position)
        self._min_visited = min(self._min_visited, position)
        self._max_visited = max(self._max_visited, position)
        return self._cells.get(position, self.blank)

    def write(self, position: int, symbol: str) -> None:
        """Escribe un símbolo en la posición indicada."""
        self._cells[position] = symbol

    def get_content(self, padding: int = 2) -> list[str]:
        """
        Retorna el contenido relevante de la cinta como lista de símbolos.
        Incluye un margen de 'padding' celdas en cada extremo.
        """
        if not self._cells:
            return [self.blank]
        min_pos = min(self._cells.keys()) - padding
        max_pos = max(self._cells.keys()) + padding
        return [self._cells.get(i, self.blank) for i in range(min_pos, max_pos + 1)], min_pos

    def get_display(self, head_pos: int) -> str:
        """Retorna una representación visual de la cinta con indicador del cabezal."""
        if not self._cells and head_pos == 0:
            cells_str = f"[{self.blank}]"
            return f"  Cinta: {cells_str}\n  Cabezal en posición: {head_pos}"

        min_pos = min(min(self._cells.keys()) if self._cells else 0, head_pos) - 1
        max_pos = max(max(self._cells.keys()) if self._cells else 0, head_pos) + 1

        tape_line = ""
        head_line = ""
        for pos in range(min_pos, max_pos + 1):
            symbol = self._cells.get(pos, self.blank)
            if pos == head_pos:
                tape_line += f"[{symbol}]"
                head_line += " ^ "
            else:
                tape_line += f" {symbol} "
                head_line += "   "
        return f"  Cinta: {tape_line}\n         {head_line}"

    def get_final_content(self) -> str:
        """Retorna el contenido no-blanco de la cinta al final de la ejecución."""
        if not self._cells:
            return self.blank
        min_pos = min(self._cells.keys())
        max_pos = max(self._cells.keys())
        content = [self._cells.get(i, self.blank) for i in range(min_pos, max_pos + 1)]
        result = ''.join(content).strip(self.blank)
        return result if result else self.blank

    def count_non_blank(self) -> int:
        """Cuenta celdas con símbolo distinto del blanco."""
        return sum(1 for v in self._cells.values() if v != self.blank)

    def cells_visited(self) -> int:
        """Retorna el número de posiciones distintas visitadas por el cabezal."""
        return len(self._visited)

    def __repr__(self):
        return f"Tape(blank='{self.blank}', cells={self._cells})"
