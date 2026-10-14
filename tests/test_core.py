"""Run: python3 -m unittest discover tests"""
import json, os, sys, tempfile, unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ["ERROR_OF_HOME"] = tempfile.mkdtemp()
from error_of import core


class Core(unittest.TestCase):
    def test_bash_running_python_is_syntax_and_context(self):
        err = ("f.py: line 1: import: command not found\n"
               "f.py: line 6: syntax error near unexpected token `('")
        self.assertEqual({h["class"] for h in core.classify(err)}, {"Syntax", "Context"})

    def test_self_report_is_parsed_and_ranked_first(self):
        err = 'ERROR-OF {"class": "Representation", "boundary": "b"}\nValueError: x'
        cap = dict(command=["x"], stdout="", stderr=err, exit_code=0, runtime_s=0,
                   environment={}, time="t")
        case = core.build_case(cap)
        self.assertEqual(case["status"], "continued")
        self.assertEqual(case["observations"][0]["class"], "Representation")

    def test_signature_ignores_paths_and_numbers(self):
        a = core.signature("File /a/b.py, line 12\nKeyError: 3")
        b = core.signature("File /c/d.py, line 99\nKeyError: 7")
        self.assertEqual(a, b)

    def test_unknown_is_explicit(self):
        cap = dict(command=["x"], stdout="", stderr="zzz", exit_code=1, runtime_s=0,
                   environment={}, time="t")
        self.assertEqual(core.build_case(cap)["inferences"][0]["class"], "Unknown")

    def test_store_is_append_only(self):
        core.store({"id": "a", "signature": None})
        core.store({"id": "b", "signature": None})
        self.assertEqual([c["id"] for c in core.load_cases()][-2:], ["a", "b"])


if __name__ == "__main__":
    unittest.main()
