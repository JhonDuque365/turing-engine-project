# =============================================================================
# simulator.py  -  Motor de simulacion de la Maquina de Turing
# =============================================================================
# Este es el nucleo del sistema. TuringMachineEngine toma una especificacion
# JSON, crea la maquina y la ejecuta paso a paso sobre una cadena de entrada.
#
# Flujo principal:
#   1. from_file(path)  - carga el JSON y crea el motor
#   2. initialize(w)    - escribe 'w' en la cinta y coloca el cabezal en pos. 0
#   3. step()           - ejecuta UNA transicion (para ejecucion paso a paso)
#   4. run()            - llama a step() hasta aceptar, rechazar o agotar pasos
#   5. get_metrics()    - retorna estadisticas de la ejecucion
#
# MODOS ESPECIALES:
#   - 'enumerator': la maquina genera cadenas en lugar de decidir pertenencia.
#     El motor no impone que deba rechazar; trata cada ejecucion como una
#     consulta de si esa cadena pertenece al lenguaje enumerado.
#     Si no hay transicion definida para (estado, simbolo) en modo enumerator,
#     el motor acepta en lugar de rechazar implicitamente.
# =============================================================================

import json
from .tape import Tape
from .machine import TuringMachine, Configuration
from .validator import Validator, ValidationError


class TuringMachineEngine:
    """
    Motor generico de simulacion de Maquinas de Turing.

    Soporta cuatro modos de maquina:
        'decider'    - siempre termina en accept o reject
        'recognizer' - acepta entradas del lenguaje, puede no terminar en otras
        'enumerator' - genera/lista cadenas de un lenguaje
        'function'   - computa una salida en la cinta

    Tres posibles resultados de ejecucion:
        'accept'                     - llego al estado de aceptacion
        'reject'                     - llego al estado de rechazo
        'timeout_without_conclusion' - se alcanzo el limite de pasos sin detenerse
                                       (NO equivale a rechazo en reconocedores/enumeradores)
    """

    def __init__(self, spec: dict):
        Validator.validate_spec(spec)
        self.machine = TuringMachine(spec)
        self._initialized = False

        # Estado de ejecucion (se reinicia en cada initialize())
        self.tape: Tape = None
        self.head: int = 0
        self.state: str = ''
        self.step_count: int = 0
        self.trace: list = []

        # Contadores para metricas
        self._left_moves: int = 0
        self._right_moves: int = 0
        self._result: str = ''

    @classmethod
    def from_file(cls, filepath: str) -> 'TuringMachineEngine':
        """
        Crea un motor cargando la especificacion desde un archivo JSON.
        Ignora comentarios de linea (//) antes de parsear.
        """
        with open(filepath, 'r', encoding='utf-8') as f:
            raw = f.read()
        # Eliminar comentarios de linea estilo // para permitir JSON anotado
        import re
        clean = re.sub(r'//[^\n]*', '', raw)
        spec = json.loads(clean)
        return cls(spec)

    def initialize(self, input_string: str) -> None:
        """
        Prepara la maquina para una nueva ejecucion:
          1. Valida que la cadena use solo simbolos del alfabeto de entrada.
          2. Crea una cinta nueva y escribe la cadena desde la posicion 0.
          3. Coloca el cabezal en la posicion 0.
          4. Reinicia contadores, traza y resultado.
          5. Guarda la configuracion inicial (paso 0) en la traza.
        """
        Validator.validate_input(input_string, self.machine.input_alphabet)

        self.tape = Tape(blank=self.machine.blank)
        self.tape.write_input(input_string)

        self.head = 0
        self.state = self.machine.start

        self.step_count = 0
        self.trace = []
        self._left_moves = 0
        self._right_moves = 0
        self._result = ''
        self._initialized = True

        self.trace.append(Configuration(
            step=0,
            state=self.state,
            tape_display=self.tape.get_display(self.head),
            head_pos=self.head,
            transition_applied=None,
            head_symbol=self.tape.read(self.head)
        ))

    def _is_enumerator(self) -> bool:
        """Retorna True si la maquina esta en modo enumerador."""
        return self.machine.mode == 'enumerator'

    def step(self) -> str:
        """
        Ejecuta UNA sola transicion de la maquina.

        Algoritmo:
          1. Si ya esta en estado de parada, retorna el resultado.
          2. Lee el simbolo bajo el cabezal.
          3. Busca la transicion (estado_actual, simbolo) en delta.
          4. Si no existe transicion:
             - Modo 'enumerator': acepta implicitamente (la cadena es enumerada).
             - Otros modos: rechazo implicito (MT determinista).
          5. Escribe el nuevo simbolo en la cinta.
          6. Actualiza el estado.
          7. Mueve el cabezal (R=+1, L=-1, S=no mueve).
          8. Incrementa el contador de pasos.
          9. Guarda la nueva configuracion en la traza.
         10. Verifica si el nuevo estado es de parada.
        """
        if not self._initialized:
            raise RuntimeError("Llama a initialize() antes de step()")

        # Si ya esta en estado final, no hay mas que ejecutar
        if self.state == self.machine.accept:
            self._result = 'accept'
            return 'accept'
        if self.state == self.machine.reject:
            self._result = 'reject'
            return 'reject'

        # Leer el simbolo bajo el cabezal
        symbol = self.tape.read(self.head)

        # Consultar la funcion de transicion delta(estado, simbolo)
        transition = self.machine.get_transition(self.state, symbol)

        # Si no hay transicion definida:
        if transition is None:
            if self._is_enumerator():
                # En modo enumerator: aceptacion implicita.
                # El enumerador genera todas las cadenas del lenguaje;
                # si no hay regla especifica, la cadena pertenece al lenguaje enumerado.
                self.state = self.machine.accept
                self._result = 'accept'
                self.step_count += 1
                self.trace.append(Configuration(
                    step=self.step_count,
                    state=self.state,
                    tape_display=self.tape.get_display(self.head),
                    head_pos=self.head,
                    transition_applied='(aceptacion implicita - modo enumerator)',
                    head_symbol=self.tape.read(self.head)
                ))
                return 'accept'
            else:
                # Modos decider/recognizer/function: rechazo implicito
                self.state = self.machine.reject
                self._result = 'reject'
                return 'reject'

        # Escribir el nuevo simbolo en la cinta
        self.tape.write(self.head, transition.write)

        # Actualizar el estado
        self.state = transition.to_state

        # Mover el cabezal
        if transition.move == 'R':
            self.head += 1
            self._right_moves += 1
        elif transition.move == 'L':
            self.head -= 1
            self._left_moves += 1
        # 'S' = Stay: el cabezal no se mueve

        # Contar la transicion aplicada
        self.step_count += 1

        # Guardar la configuracion resultante en la traza
        self.trace.append(Configuration(
            step=self.step_count,
            state=self.state,
            tape_display=self.tape.get_display(self.head),
            head_pos=self.head,
            transition_applied=str(transition),
            head_symbol=self.tape.read(self.head)
        ))

        # Verificar si llegamos a un estado de parada
        if self.state == self.machine.accept:
            self._result = 'accept'
            return 'accept'
        if self.state == self.machine.reject:
            self._result = 'reject'
            return 'reject'

        return 'running'

    def run(self, max_steps: int = 10000) -> str:
        """
        Ejecuta la maquina llamando a step() repetidamente hasta que:
          a) Alcanza un estado de parada (accept o reject) -> retorna ese resultado.
          b) Llega al limite de pasos -> retorna 'timeout_without_conclusion'.

        IMPORTANTE: 'timeout_without_conclusion' NO significa rechazo.
        En reconocedores y enumeradores, la maquina puede correr indefinidamente
        para ciertas entradas. El timeout solo indica ausencia de conclusion
        dentro del presupuesto de pasos asignado.
        """
        if not self._initialized:
            raise RuntimeError("Llama a initialize() antes de run()")

        while self.step_count < max_steps:
            status = self.step()
            if status in ('accept', 'reject'):
                return status

        self._result = 'timeout_without_conclusion'
        return 'timeout_without_conclusion'

    def get_metrics(self) -> dict:
        """
        Retorna un diccionario con las metricas de la ejecucion actual.
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
        """Imprime la traza completa en consola. Util para depuracion."""
        steps = self.trace if max_steps is None else self.trace[:max_steps + 1]
        print(f"\n{'='*70}")
        print(f"  TRAZA DE EJECUCION - Maquina: {self.machine.name}")
        print(f"{'='*70}")
        for config in steps:
            print(config)
            print(config.tape_display)
            print()
        print(f"  Resultado final: {self._result.upper()}")
        print(f"{'='*70}\n")

    def run_test_suite(self) -> list:
        """
        Ejecuta todos los casos de prueba definidos en el campo 'tests' del JSON.

        Para cada caso:
          - Inicializa la maquina con el input del test.
          - Ejecuta hasta detenerse o agotar pasos.
          - Compara el resultado real con el esperado.
          - Retorna una lista con el resultado de cada prueba.
        """
        results = []
        for test in self.machine.tests:
            input_str = test['input']
            expected  = test['expected']
            try:
                self.initialize(input_str)
                actual = self.run(max_steps=10000)
            except Exception as e:
                actual = f'error: {e}'
            results.append({
                'input':    input_str,
                'expected': expected,
                'actual':   actual,
                'passed':   actual == expected
            })
        return results
