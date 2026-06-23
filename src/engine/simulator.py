# =============================================================================
# simulator.py  –  Motor de simulación de la Máquina de Turing
# =============================================================================
# Este es el núcleo del sistema. TuringMachineEngine toma una especificación
# JSON, crea la máquina y la ejecuta paso a paso sobre una cadena de entrada.
#
# Flujo principal:
#   1. from_file(path)  – carga el JSON y crea el motor
#   2. initialize(w)    – escribe 'w' en la cinta y coloca el cabezal en pos. 0
#   3. step()           – ejecuta UNA transición (para ejecución paso a paso)
#   4. run()            – llama a step() hasta aceptar, rechazar o agotar pasos
#   5. get_metrics()    – retorna estadísticas de la ejecución
# =============================================================================

import json
from .tape import Tape
from .machine import TuringMachine, Configuration
from .validator import Validator, ValidationError


class TuringMachineEngine:
    """
    Motor genérico de simulación de Máquinas de Turing.

    Soporta tres modos de resultado:
        'accept'                     – la máquina llegó al estado de aceptación
        'reject'                     – la máquina llegó al estado de rechazo
        'timeout_without_conclusion' – se alcanzó el límite de pasos sin detenerse
                                       (NO equivale a rechazo en reconocedores)
    """

    def __init__(self, spec: dict):
        # Validar la especificación antes de construir la máquina.
        # Si hay errores formales (estado inexistente, transición inválida, etc.)
        # se lanza ValidationError antes de ejecutar nada.
        Validator.validate_spec(spec)
        self.machine = TuringMachine(spec)
        self._initialized = False

        # --- Estado de ejecución (se reinicia en cada initialize()) ---
        self.tape: Tape = None          # La cinta infinita
        self.head: int = 0              # Posición actual del cabezal
        self.state: str = ''            # Estado actual de la máquina
        self.step_count: int = 0        # Número de transiciones ejecutadas
        self.trace: list[Configuration] = []  # Historial completo de configuraciones

        # --- Contadores para métricas ---
        self._left_moves: int = 0       # Movimientos a la izquierda
        self._right_moves: int = 0      # Movimientos a la derecha
        self._result: str = ''          # Resultado final: accept / reject / timeout

    @classmethod
    def from_file(cls, filepath: str) -> 'TuringMachineEngine':
        """
        Crea un motor cargando la especificación desde un archivo JSON.
        Este es el método de entrada principal cuando se usa desde la web.
        """
        with open(filepath, 'r', encoding='utf-8') as f:
            spec = json.load(f)
        return cls(spec)

    def initialize(self, input_string: str) -> None:
        """
        Prepara la máquina para una nueva ejecución:
          1. Valida que la cadena use solo símbolos del alfabeto de entrada.
          2. Crea una cinta nueva y escribe la cadena desde la posición 0.
          3. Coloca el cabezal en la posición 0 (inicio de la cadena).
          4. Reinicia contadores, traza y resultado.
          5. Guarda la configuración inicial (paso 0) en la traza.
        """
        # La cadena vacía es siempre válida (representa epsilon ε)
        Validator.validate_input(input_string, self.machine.input_alphabet)

        # Crear cinta nueva con el símbolo blanco de esta máquina
        self.tape = Tape(blank=self.machine.blank)
        self.tape.write_input(input_string)

        # Posicionar cabezal al inicio
        self.head = 0
        self.state = self.machine.start

        # Reiniciar todos los contadores
        self.step_count = 0
        self.trace = []
        self._left_moves = 0
        self._right_moves = 0
        self._result = ''
        self._initialized = True

        # Guardar configuración inicial (paso 0, antes de ejecutar nada)
        self.trace.append(Configuration(
            step=0,
            state=self.state,
            tape_display=self.tape.get_display(self.head),
            head_pos=self.head,
            transition_applied=None,          # No se aplicó ninguna transición aún
            head_symbol=self.tape.read(self.head)
        ))

    def step(self) -> str:
        """
        Ejecuta UNA sola transición de la máquina.
        Este es el núcleo del motor: implementa la función de transición δ.

        Algoritmo en cada paso:
          1. Si ya está en estado de parada, retorna el resultado directamente.
          2. Lee el símbolo bajo el cabezal.
          3. Busca la transición (estado_actual, simbolo) en δ.
          4. Si no existe transición -> rechazo implícito (MT determinista).
          5. Escribe el nuevo símbolo en la cinta.
          6. Actualiza el estado.
          7. Mueve el cabezal (R = +1, L = -1, S = no mueve).
          8. Incrementa el contador de pasos.
          9. Guarda la nueva configuración en la traza.
         10. Verifica si el nuevo estado es de parada.

        Retorna: 'accept', 'reject' o 'running'
        """
        if not self._initialized:
            raise RuntimeError("Llama a initialize() antes de step()")

        # Si ya está en estado final, no hay nada más que ejecutar
        if self.state == self.machine.accept:
            self._result = 'accept'
            return 'accept'
        if self.state == self.machine.reject:
            self._result = 'reject'
            return 'reject'

        # Paso 2: leer el símbolo bajo el cabezal
        symbol = self.tape.read(self.head)

        # Paso 3: consultar la función de transición δ(estado, simbolo)
        transition = self.machine.get_transition(self.state, symbol)

        # Paso 4: si no hay transición definida, rechazo implícito
        # En una MT determinista, la ausencia de transición equivale a rechazar.
        if transition is None:
            self.state = self.machine.reject
            self._result = 'reject'
            return 'reject'

        # Paso 5: escribir el nuevo símbolo en la cinta
        self.tape.write(self.head, transition.write)

        # Paso 6: actualizar el estado de la máquina
        self.state = transition.to_state

        # Paso 7: mover el cabezal según la dirección de la transición
        if transition.move == 'R':    # Derecha: avanzar una celda
            self.head += 1
            self._right_moves += 1
        elif transition.move == 'L':  # Izquierda: retroceder una celda
            self.head -= 1
            self._left_moves += 1
        # 'S' = Stay: el cabezal no se mueve (no hacer nada)

        # Paso 8: contar la transición aplicada
        self.step_count += 1

        # Paso 9: guardar la configuración resultante en la traza
        # La traza es fundamental: permite explicar CADA decisión de la máquina.
        self.trace.append(Configuration(
            step=self.step_count,
            state=self.state,
            tape_display=self.tape.get_display(self.head),
            head_pos=self.head,
            transition_applied=str(transition),
            head_symbol=self.tape.read(self.head)
        ))

        # Paso 10: verificar si llegamos a un estado de parada
        if self.state == self.machine.accept:
            self._result = 'accept'
            return 'accept'
        if self.state == self.machine.reject:
            self._result = 'reject'
            return 'reject'

        return 'running'  # La máquina sigue ejecutando

    def run(self, max_steps: int = 10000) -> str:
        """
        Ejecuta la máquina llamando a step() repetidamente hasta que:
          a) Alcanza un estado de parada (accept o reject) -> retorna ese resultado
          b) Llega al límite de pasos -> retorna 'timeout_without_conclusion'

        IMPORTANTE: 'timeout_without_conclusion' NO significa rechazo.
        En un reconocedor (no decididor), la máquina puede ejecutar infinitamente
        para entradas que no pertenecen al lenguaje. El timeout solo indica
        que no se alcanzó una conclusión dentro del presupuesto de pasos.
        """
        if not self._initialized:
            raise RuntimeError("Llama a initialize() antes de run()")

        while self.step_count < max_steps:
            status = self.step()
            if status in ('accept', 'reject'):
                return status  # Parada limpia

        # Se agotó el límite de pasos sin llegar a una decisión
        self._result = 'timeout_without_conclusion'
        return 'timeout_without_conclusion'

    def get_metrics(self) -> dict:
        """
        Retorna un diccionario con las métricas de la ejecución actual.
        Se llama después de run() o cuando la ejecución termina.
        """
        return {
            'resultado':             self._result,
            'pasos_ejecutados':      self.step_count,
            'celdas_visitadas':      self.tape.cells_visited() if self.tape else 0,
            'celdas_no_blancas':     self.tape.count_non_blank() if self.tape else 0,
            'movimientos_izquierda': self._left_moves,
            'movimientos_derecha':   self._right_moves,
            'cinta_final':           self.tape.get_final_content() if self.tape else '',
            'longitud_entrada':      len(self.trace[0].head_symbol) if self.trace else 0,
        }

    def print_trace(self, max_steps: int = None) -> None:
        """Imprime la traza completa en consola. Útil para depuración."""
        steps = self.trace if max_steps is None else self.trace[:max_steps + 1]
        print(f"\n{'='*70}")
        print(f"  TRAZA DE EJECUCIÓN - Máquina: {self.machine.name}")
        print(f"{'='*70}")
        for config in steps:
            print(config)
            print(config.tape_display)
            print()
        print(f"  Resultado final: {self._result.upper()}")
        print(f"{'='*70}\n")

    def run_test_suite(self) -> list[dict]:
        """
        Ejecuta todos los casos de prueba definidos en el campo 'tests' del JSON.

        Para cada caso:
          - Inicializa la máquina con el input del test
          - Ejecuta hasta detenerse o agotar pasos
          - Compara el resultado real con el esperado
          - Retorna una lista con el resultado de cada prueba

        El input se devuelve como string limpio (sin repr()) para
        que el frontend pueda mostrarlo directamente.
        """
        results = []
        for test in self.machine.tests:
            input_str = test['input']    # Cadena de entrada (puede ser '' para epsilon)
            expected  = test['expected'] # 'accept' o 'reject'
            try:
                self.initialize(input_str)
                actual = self.run(max_steps=10000)
            except Exception as e:
                actual = f'error: {e}'
            results.append({
                'input':    input_str,           # String limpio, sin repr()
                'expected': expected,
                'actual':   actual,
                'passed':   actual == expected   # True si el motor dio el resultado correcto
            })
        return results
