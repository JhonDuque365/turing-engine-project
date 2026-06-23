"""
Pruebas unitarias para el decididor ANBN.
Verifica que L = { a^n b^n | n >= 0 } se decide correctamente.
"""
import sys
import os
import json
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from engine.simulator import TuringMachineEngine


class TestANBN(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        path = os.path.join(os.path.dirname(__file__), '..', 'machines', 'anbn_decider.json')
        cls.engine = TuringMachineEngine.from_file(path)

    def _run(self, s):
        self.engine.initialize(s)
        return self.engine.run(max_steps=5000)

    # Casos positivos
    def test_empty_string(self):
        self.assertEqual(self._run(''), 'accept')

    def test_ab(self):
        self.assertEqual(self._run('ab'), 'accept')

    def test_aabb(self):
        self.assertEqual(self._run('aabb'), 'accept')

    def test_aaabbb(self):
        self.assertEqual(self._run('aaabbb'), 'accept')

    def test_aaaabbbb(self):
        self.assertEqual(self._run('aaaabbbb'), 'accept')

    # Casos negativos
    def test_a_solo(self):
        self.assertEqual(self._run('a'), 'reject')

    def test_b_solo(self):
        self.assertEqual(self._run('b'), 'reject')

    def test_aab(self):
        self.assertEqual(self._run('aab'), 'reject')

    def test_abb(self):
        self.assertEqual(self._run('abb'), 'reject')

    def test_abab(self):
        self.assertEqual(self._run('abab'), 'reject')

    def test_ba(self):
        self.assertEqual(self._run('ba'), 'reject')

    def test_bba(self):
        self.assertEqual(self._run('bba'), 'reject')

    # Prueba de traza
    def test_trace_aabb(self):
        self.engine.initialize('aabb')
        self.engine.run(max_steps=5000)
        self.assertGreater(len(self.engine.trace), 1)
        self.assertEqual(self.engine._result, 'accept')

    # Prueba suite integrada
    def test_suite_completa(self):
        results = self.engine.run_test_suite()
        failed = [r for r in results if not r['passed']]
        self.assertEqual(len(failed), 0, f"Pruebas fallidas: {failed}")


if __name__ == '__main__':
    unittest.main(verbosity=2)
