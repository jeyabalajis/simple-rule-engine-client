from unittest import TestCase

from simpleruleengine.operator.not_equal import NotEq


class TestSimpleRuleLibrary(TestCase):
    def test_operator_with_not_eq(self):
        assert NotEq(2).evaluate(3) is True
        assert NotEq(2.25).evaluate(2.26) is True

