#!/usr/bin/env python3
"""
Servidor Flask – Interfaz web para el Motor Genérico de Máquina de Turing.
Expone una API REST que conecta el frontend con el motor existente.

Uso:
    python src/web/server.py
    Abrir: http://localhost:5000
"""
import os
import sys
import json
from flask import Flask, render_template, request, jsonify, session

# Asegurar imports del motor
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC  = os.path.join(ROOT, 'src')
sys.path.insert(0, SRC)

from engine.simulator import TuringMachineEngine
from engine.validator import ValidationError

app = Flask(__name__, template_folder='templates', static_folder='static')
app.secret_key = 'turing-motor-2026-unipamplona'

MACHINES_DIR = os.path.join(ROOT, 'machines')

# Estado global de sesión por instancia de motor (simple: una sesión activa)
_engine: TuringMachineEngine = None
_machine_name: str = ''


# ── Utilidades ────────────────────────────────────────────────────────────────

def list_machines():
    """Retorna lista de archivos JSON disponibles en machines/."""
    return sorted([
        f for f in os.listdir(MACHINES_DIR)
        if f.endswith('.json')
    ])


def tape_to_list(engine: TuringMachineEngine):
    """Convierte la cinta a lista de objetos {pos, symbol, is_head} para el frontend."""
    tape = engine.tape
    head = engine.head
    if not tape._cells:
        return [{'pos': 0, 'symbol': tape.blank, 'is_head': True}]

    min_pos = min(min(tape._cells.keys()), head) - 2
    max_pos = max(max(tape._cells.keys()), head) + 2

    result = []
    for pos in range(min_pos, max_pos + 1):
        result.append({
            'pos': pos,
            'symbol': tape._cells.get(pos, tape.blank),
            'is_head': (pos == head)
        })
    return result


def config_to_dict(config, tape_cells=None):
    """Serializa una Configuration a dict JSON."""
    return {
        'step': config.step,
        'state': config.state,
        'head_pos': config.head_pos,
        'head_symbol': config.head_symbol,
        'transition': config.transition_applied or '(inicio)',
        'tape': tape_cells or []
    }


# ── Rutas principales ─────────────────────────────────────────────────────────

@app.route('/')
def index():
    machines = list_machines()
    return render_template('index.html', machines=machines)


@app.route('/api/machines', methods=['GET'])
def api_machines():
    machines = list_machines()
    result = []
    for fname in machines:
        path = os.path.join(MACHINES_DIR, fname)
        try:
            with open(path, encoding='utf-8') as f:
                spec = json.load(f)
            result.append({
                'file': fname,
                'name': spec.get('name', fname),
                'mode': spec.get('mode', '?'),
                'description': spec.get('description', ''),
                'states_count': len(spec.get('states', [])),
                'transitions_count': len(spec.get('transitions', [])),
                'tests_count': len(spec.get('tests', [])),
            })
        except Exception as e:
            result.append({'file': fname, 'name': fname, 'error': str(e)})
    return jsonify(result)


@app.route('/api/load', methods=['POST'])
def api_load():
    """Carga una máquina e inicializa el motor con la cadena de entrada."""
    global _engine, _machine_name
    data = request.get_json()
    filename = data.get('file', '')
    input_str = data.get('input', '')

    path = os.path.join(MACHINES_DIR, filename)
    if not os.path.exists(path):
        return jsonify({'error': f'Archivo no encontrado: {filename}'}), 404

    try:
        _engine = TuringMachineEngine.from_file(path)
        _machine_name = _engine.machine.name
        _engine.initialize(input_str)
    except ValidationError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

    cfg = _engine.trace[0]
    return jsonify({
        'ok': True,
        'machine': _machine_name,
        'mode': _engine.machine.mode,
        'states': sorted(_engine.machine.states),
        'accept_state': _engine.machine.accept,
        'reject_state': _engine.machine.reject,
        'transitions': [
            {'from': t.from_state, 'read': t.read,
             'to': t.to_state, 'write': t.write, 'move': t.move}
            for t in _engine.machine.transitions.values()
        ],
        'current': config_to_dict(cfg, tape_to_list(_engine)),
        'result': None,
        'step_count': 0,
    })


@app.route('/api/step', methods=['POST'])
def api_step():
    """Avanza un paso en la ejecución."""
    global _engine
    if _engine is None:
        return jsonify({'error': 'Motor no inicializado. Carga una máquina primero.'}), 400
    if _engine._result in ('accept', 'reject'):
        return jsonify({
            'ok': True,
            'status': _engine._result,
            'current': config_to_dict(_engine.trace[-1], tape_to_list(_engine)),
            'step_count': _engine.step_count,
            'metrics': _engine.get_metrics(),
            'done': True
        })
    try:
        status = _engine.step()
        cfg = _engine.trace[-1]
        done = status in ('accept', 'reject')
        return jsonify({
            'ok': True,
            'status': status,
            'current': config_to_dict(cfg, tape_to_list(_engine)),
            'step_count': _engine.step_count,
            'metrics': _engine.get_metrics() if done else None,
            'done': done
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/run', methods=['POST'])
def api_run():
    """Ejecuta la máquina hasta detenerse o alcanzar el límite."""
    global _engine
    if _engine is None:
        return jsonify({'error': 'Motor no inicializado.'}), 400
    data = request.get_json() or {}
    max_steps = int(data.get('max_steps', 10000))
    try:
        result = _engine.run(max_steps=max_steps)
        metrics = _engine.get_metrics()
        trace_summary = [
            config_to_dict(c) for c in _engine.trace
        ]
        return jsonify({
            'ok': True,
            'result': result,
            'metrics': metrics,
            'tape': tape_to_list(_engine),
            'current': config_to_dict(_engine.trace[-1], tape_to_list(_engine)),
            'step_count': _engine.step_count,
            'trace': trace_summary
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/reset', methods=['POST'])
def api_reset():
    """Reinicia la ejecución con la misma máquina y una cadena nueva."""
    global _engine
    if _engine is None:
        return jsonify({'error': 'Motor no inicializado.'}), 400
    data = request.get_json() or {}
    input_str = data.get('input', '')
    try:
        _engine.initialize(input_str)
        cfg = _engine.trace[0]
        return jsonify({
            'ok': True,
            'current': config_to_dict(cfg, tape_to_list(_engine)),
            'step_count': 0,
            'result': None
        })
    except ValidationError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/tests', methods=['POST'])
def api_tests():
    """Ejecuta la suite de pruebas de la máquina cargada."""
    global _engine
    if _engine is None:
        return jsonify({'error': 'Motor no inicializado.'}), 400
    try:
        results = _engine.run_test_suite()
        passed = sum(1 for r in results if r['passed'])
        return jsonify({'ok': True, 'results': results, 'passed': passed, 'total': len(results)})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    print('\n' + '='*55)
    print('  MOTOR GENÉRICO DE MÁQUINA DE TURING – Interfaz Web')
    print('  Universidad de Pamplona – 2026-1')
    print('  http://localhost:5000')
    print('='*55 + '\n')
    app.run(debug=True, port=5000)
