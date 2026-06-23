#!/usr/bin/env python3
"""
Interfaz de consola para el Motor Genérico de Máquina de Turing.
Permite seleccionar máquinas, ingresar cadenas, ejecutar paso a paso
y consultar métricas.

Uso:
    python src/ui/app.py
"""
import os
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.simulator import TuringMachineEngine
from engine.validator import ValidationError

MACHINES_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    'machines'
)


def listar_maquinas():
    archivos = [f for f in os.listdir(MACHINES_DIR) if f.endswith('.json')]
    return archivos


def seleccionar_maquina():
    maquinas = listar_maquinas()
    if not maquinas:
        print("No se encontraron archivos de máquinas en 'machines/'")
        return None
    print("\n" + "="*50)
    print("  MÁQUINAS DISPONIBLES")
    print("="*50)
    for i, nombre in enumerate(maquinas, 1):
        print(f"  {i}. {nombre}")
    print("  0. Salir")
    try:
        opcion = int(input("\nSelecciona una máquina (número): "))
        if opcion == 0:
            return None
        return os.path.join(MACHINES_DIR, maquinas[opcion - 1])
    except (ValueError, IndexError):
        print("Opción inválida.")
        return None


def menu_ejecucion(engine: TuringMachineEngine, input_str: str):
    print(f"\n  Máquina cargada: {engine.machine.name}")
    print(f"  Modo: {engine.machine.mode}")
    print(f"  Entrada: '{input_str}'")
    print("-"*50)
    print("  1. Ejecutar completo")
    print("  2. Ejecutar paso a paso")
    print("  3. Ver transiciones de la máquina")
    print("  4. Ejecutar suite de pruebas")
    print("  0. Volver")
    return input("\nOpción: ").strip()


def ejecutar_completo(engine, input_str):
    engine.initialize(input_str)
    max_steps = 10000
    try:
        max_steps = int(input("  Límite de pasos [10000]: ") or '10000')
    except ValueError:
        pass
    resultado = engine.run(max_steps=max_steps)
    print(f"\n  ► Resultado: {resultado.upper()}")
    metricas = engine.get_metrics()
    print("\n  MÉTRICAS:")
    for k, v in metricas.items():
        print(f"    {k:<25}: {v}")
    if input("\n  ¿Ver traza completa? (s/n): ").lower() == 's':
        engine.print_trace()


def ejecutar_paso_a_paso(engine, input_str):
    engine.initialize(input_str)
    print("\n  [PASO A PASO] Presiona Enter para avanzar, 'q' para salir.")
    print(engine.trace[0])
    print(engine.trace[0].tape_display)
    status = 'running'
    while status == 'running':
        cmd = input("\n  [Enter=paso / q=salir]: ").strip().lower()
        if cmd == 'q':
            break
        status = engine.step()
        last = engine.trace[-1]
        print(last)
        print(last.tape_display)
    resultado = engine._result or status
    print(f"\n  ► Resultado final: {resultado.upper() if resultado else 'EN EJECUCIÓN'}")


def ver_transiciones(engine):
    print(f"\n  Transiciones de '{engine.machine.name}':")
    print(f"  {'(estado, símbolo)':<25} → {'(nuevo_estado, escribe, mueve)':<35}")
    print("  " + "-"*60)
    for (state, sym), t in sorted(engine.machine.transitions.items()):
        print(f"  ({state:<12}, '{sym}') → ({t.to_state:<12}, '{t.write}', {t.move})")


def ejecutar_suite(engine):
    print(f"\n  Suite de pruebas para '{engine.machine.name}':")
    results = engine.run_test_suite()
    pasados = sum(1 for r in results if r['passed'])
    print(f"  {'Entrada':<15} {'Esperado':<12} {'Obtenido':<35} {'✓/✗'}")
    print("  " + "-"*70)
    for r in results:
        icono = '✓' if r['passed'] else '✗'
        print(f"  {r['input']:<15} {r['expected']:<12} {r['actual']:<35} {icono}")
    print(f"\n  Resultado: {pasados}/{len(results)} pruebas pasadas.")


def main():
    print("\n" + "="*60)
    print("  MOTOR GENÉRICO DE MÁQUINA DE TURING")
    print("  Teoría de la Computación - Univ. de Pamplona 2026-1")
    print("="*60)

    while True:
        ruta = seleccionar_maquina()
        if ruta is None:
            print("\n  Hasta luego.\n")
            break

        try:
            engine = TuringMachineEngine.from_file(ruta)
        except (ValidationError, Exception) as e:
            print(f"  Error al cargar la máquina: {e}")
            continue

        input_str = input("\n  Ingresa la cadena de entrada (vacío = cadena vacía): ")

        while True:
            opcion = menu_ejecucion(engine, input_str)
            if opcion == '0':
                break
            elif opcion == '1':
                try:
                    ejecutar_completo(engine, input_str)
                except ValidationError as e:
                    print(f"  Error de validación: {e}")
            elif opcion == '2':
                try:
                    ejecutar_paso_a_paso(engine, input_str)
                except ValidationError as e:
                    print(f"  Error de validación: {e}")
            elif opcion == '3':
                ver_transiciones(engine)
            elif opcion == '4':
                ejecutar_suite(engine)
            else:
                print("  Opción inválida.")


if __name__ == '__main__':
    main()
