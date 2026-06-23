# =============================================================================
# tape.py  –  Módulo de la CINTA de la Máquina de Turing
# =============================================================================
# La cinta es la estructura de memoria de la MT. Es infinita en ambas
# direcciones. Usamos un diccionario Python {posicion: simbolo} en lugar de
# una lista, porque los índices negativos son válidos y la cinta crece sin
# límite en ambos extremos sin desperdiciar memoria.
# =============================================================================

class Tape:
    """
    Representa la cinta infinita de una Máquina de Turing.

    Internamente es un diccionario {int -> str} donde la clave es la
    posición absoluta en la cinta. Las celdas no escritas devuelven
    automáticamente el símbolo blanco, simulando la infinitud de la cinta.
    """

    def __init__(self, blank: str = '_'):
        # Símbolo blanco: representa una celda vacía (no escrita).
        # Por convención se usa '_', pero puede cambiarse en el JSON.
        self.blank = blank

        # Diccionario principal: posición -> símbolo escrito.
        # Solo se almacenan celdas que tienen algún contenido.
        self._cells: dict[int, str] = {}

        # Rango mínimo y máximo de posiciones visitadas por el cabezal.
        # Se usan para calcular métricas de ejecución.
        self._min_visited = 0
        self._max_visited = 0

        # Conjunto de posiciones distintas que el cabezal ha recorrido.
        self._visited: set[int] = set()

    def write_input(self, input_string: str) -> None:
        """
        Escribe la cadena de entrada en la cinta empezando en la posición 0.
        Se llama al inicio de cada simulación para preparar la cinta.

        Ejemplo: write_input('aabb') coloca
          pos 0 -> 'a', pos 1 -> 'a', pos 2 -> 'b', pos 3 -> 'b'
        """
        self._cells = {}  # Limpiar contenido anterior
        for i, symbol in enumerate(input_string):
            self._cells[i] = symbol

    def read(self, position: int) -> str:
        """
        Lee el símbolo en la posición dada.
        Si la posición no fue escrita, retorna el símbolo blanco.
        Esto simula la cinta infinita: cualquier celda fuera del área
        escrita contiene blanco por defecto.

        Además actualiza las métricas de celdas visitadas.
        """
        # Registrar que el cabezal visitó esta posición
        self._visited.add(position)
        self._min_visited = min(self._min_visited, position)
        self._max_visited = max(self._max_visited, position)

        # dict.get(key, default) retorna blank si la clave no existe
        return self._cells.get(position, self.blank)

    def write(self, position: int, symbol: str) -> None:
        """
        Escribe un símbolo en la posición dada.
        Sobrescribe cualquier valor anterior en esa celda.
        """
        self._cells[position] = symbol

    def get_content(self, padding: int = 2) -> list[str]:
        """
        Retorna el contenido de la cinta como lista de símbolos,
        incluyendo un margen extra de 'padding' celdas en cada extremo
        para visualización.
        """
        if not self._cells:
            return [self.blank]
        min_pos = min(self._cells.keys()) - padding
        max_pos = max(self._cells.keys()) + padding
        return [self._cells.get(i, self.blank) for i in range(min_pos, max_pos + 1)], min_pos

    def get_display(self, head_pos: int) -> str:
        """
        Genera una representación visual de la cinta para la traza.
        El símbolo bajo el cabezal aparece entre corchetes [x].
        Las demás celdas aparecen con espacios.

        Ejemplo de salida:
          Cinta:  a  a [b] b
                        ^
        """
        if not self._cells and head_pos == 0:
            return f"  Cinta: [{self.blank}]\n  Cabezal en posición: {head_pos}"

        min_pos = min(min(self._cells.keys()) if self._cells else 0, head_pos) - 1
        max_pos = max(max(self._cells.keys()) if self._cells else 0, head_pos) + 1

        tape_line = ""
        head_line = ""
        for pos in range(min_pos, max_pos + 1):
            symbol = self._cells.get(pos, self.blank)
            if pos == head_pos:
                tape_line += f"[{symbol}]"   # Cabezal: entre corchetes
                head_line += " ^ "
            else:
                tape_line += f" {symbol} "
                head_line += "   "
        return f"  Cinta: {tape_line}\n         {head_line}"

    def get_final_content(self) -> str:
        """
        Retorna el contenido final de la cinta como cadena,
        eliminando blancos en los extremos.
        Se usa para máquinas tipo 'function' que producen salida en cinta.
        """
        if not self._cells:
            return self.blank
        min_pos = min(self._cells.keys())
        max_pos = max(self._cells.keys())
        content = [self._cells.get(i, self.blank) for i in range(min_pos, max_pos + 1)]
        result = ''.join(content).strip(self.blank)
        return result if result else self.blank

    def count_non_blank(self) -> int:
        """Cuenta cuántas celdas tienen un símbolo distinto del blanco al final."""
        return sum(1 for v in self._cells.values() if v != self.blank)

    def cells_visited(self) -> int:
        """Retorna cuántas posiciones distintas visitó el cabezal durante la ejecución."""
        return len(self._visited)

    def __repr__(self):
        return f"Tape(blank='{self.blank}', cells={self._cells})"
