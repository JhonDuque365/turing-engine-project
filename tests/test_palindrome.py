"""
Pruebas unitarias para el decididor de palíndromos.
Verifica que PAL = { w | w = w^R } sobre {0,1} se decide correctamente.
"""
import sys
import os
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from engine.simulator import TuringMachineEngine


class TestPalindrome(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        path = os.path.join(os.path.dirname(__file__), '..', 'machines', 'palindrome_decider.json')
        cls.engine = TuringMachineEngine.from_file(path)

    def _run(self, s):
        self.engine.initialize(s)
        return self.engine.run(max_steps=5000)

    # Palíndromos (accept)
    def test_empty(self):
        self.assertEqual(self._run(''), 'accept')

    def test_single_0(self):
        self.assertEqual(self._run('0'), 'accept')

    def test_single_1(self):
        self.assertEqual(self._run('1'), 'accept')

    def test_00(self):
        self.assertEqual(self._run('00'), 'accept')

    def test_11(self):
        self.assertEqual(self._run('11'), 'accept')

    def test_010(self):
        self.assertEqual(self._run('010'), 'accept')

    def test_0110(self):
        self.assertEqual(self._run('0110'), 'accept')

    def test_001100(self):
        # No es palíndromo
        self.assertEqual(self._run('001100'), 'reject')

    # No palíndromos (reject)
    def test_01(self):
        self.assertEqual(self._run('01'), 'reject')

    def test_001(self):
        self.assertEqual(self._run('001'), 'reject')

    def test_0100(self):
        self.assertEqual(self._run('0100'), 'reject')

    # Suite integrada
    def test_suite_completa(self):
        results = self.engine.run_test_suite()
        failed = [r for r in results if not r['passed']]
        self.assertEqual(len(failed), 0, f"Pruebas fallidas: {failed}")


if __name__ == '__main__':
    unittest.main(verbosity=2)
