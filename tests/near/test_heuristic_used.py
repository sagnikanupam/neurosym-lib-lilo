"""
Check that the heuristic is actually being used in neural model search, and that
it works as expected.
"""

import re
import unittest

import neurosym as ns
from neurosym.examples import near


class TestNeuralModels(unittest.TestCase):

    def test_doesnt_work_no_heuristic_combinator(self):
        self.assertNearReturns(
            6, near.debug_nested_dsl.get_combinator_dsl, {}, "StopIteration"
        )

    def test_no_heuristic_combinator_works_more_time(self):
        self.assertNearReturns(
            6,
            near.debug_nested_dsl.get_combinator_dsl,
            {},
            re.compile(r"\(.*\)"),
            max_iterations=10_000,
        )

    def test_doesnt_work_no_heuristic_variables(self):
        self.assertNearReturns(
            6, near.debug_nested_dsl.get_variable_dsl, {}, "StopIteration"
        )

    def test_no_heuristic_variables_works_more_time(self):
        self.assertNearReturns(
            6,
            near.debug_nested_dsl.get_variable_dsl,
            {},
            re.compile(r"\(.*\)"),
            max_iterations=10_000,
        )

    def test_combinator_dsl_works_with_mlps(self):
        self.assertNearReturns(
            10,
            near.debug_nested_dsl.get_combinator_dsl,
            self.mlp_modules,
            self.compute_combinator_soln,
        )

    def test_combinator_dsl_works_with_transformer(self):
        self.assertNearReturns(
            5,
            near.debug_nested_dsl.get_combinator_dsl,
            self.transformer_modules,
            self.compute_combinator_soln,
        )

    def test_variable_dsl_works_with_transformer(self):
        self.assertNearReturns(
            10,
            near.debug_nested_dsl.get_variable_dsl,
            self.transformer_modules,
            self.compute_variable_soln,
        )

    def compute_combinator_soln(self, nesting):
        expected = ns.SExpression("terminal", ())
        for i in range(2, nesting + 1):
            expected = ns.SExpression(f"correct_{i}", (expected,))
        return ns.render_s_expression(expected)

    def compute_variable_soln(self, nesting):
        expected = ns.SExpression("terminal", (ns.SExpression("$0_0", ()),))
        for i in range(2, nesting + 1):
            expected = ns.SExpression(f"correct_{i}", (expected,))
        expected = ns.SExpression("lam", (expected,))
        return ns.render_s_expression(expected)

    def mlp_modules(self, nesting):
        return near.create_modules(
            "mlp",
            [ns.parse_type("{f, 1} -> {f, %s}" % i) for i in range(1, 2 + nesting)],
            near.mlp_factory(hidden_size=10),
        )

    def transformer_modules(self, nesting):
        return near.create_modules(
            "transformer",
            [ns.parse_type("{f, %s}" % i) for i in range(1, 2 + nesting)]
            + [ns.parse_type("{f, 1} -> {f, %s}" % i) for i in range(2, 2 + nesting)],
            near.transformer_factory(
                max_tensor_size=10,
                hidden_size=16,
                num_decoder_layers=1,
                num_encoder_layers=1,
                num_head=4,
            ),
        )

    def assertNearReturns(self, nesting, dsl_fn, neural_modules, expected, **kwargs):
        if not isinstance(neural_modules, dict):
            neural_modules = neural_modules(nesting)
        try:
            results = near.debug_nested_dsl.run_near_on_dsl(
                nesting,
                dsl_fn(nesting),
                neural_modules=neural_modules,
                **kwargs,
            )
            if not results:
                actual = "No results"
            else:
                [actual] = results
                actual = ns.render_s_expression(actual.program)
        except StopIteration:
            actual = "StopIteration"
        if callable(expected):
            expected = expected(nesting)
        if isinstance(expected, str):
            self.assertEqual(actual, expected)
        else:
            assert isinstance(expected, re.Pattern)
            self.assertRegex(actual, expected)
