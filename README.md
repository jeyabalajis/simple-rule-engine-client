# simple-serverless-rule-engine

An extension to [Simple Rule Engine](https://github.com/jeyabalajis/simple-rule-engine) that illustrates how can be declaratively specified (json etc.), stored, and later de-serialized into simple-rule-engine constructs and executed with data.

# Examples

## A simple decision tree involving facts

### Decision matrix

| Bureau Score | Marital Status | Business Ownership | Decision
| :----------: | :----------------: | :----------------: | --------:|
| between 650 and 800        | in [Married, Unspecified]                | in [Owned by Self, Owned by Family] | GO       |

### JSON Rule specification

```json
{
    "RuleDecision": {
        "RuleRows": [
            {
                "WhenAll": [
                    {
                        "NumericToken": "cibil_score",
                        "Between": {
                            "floor": 650,
                            "ceiling": 800
                        }
                    },
                    {
                        "StringToken": "business_ownership",
                        "In": [
                            "Owned by Self",
                            "Owned by Family"
                        ]
                    }
                ],
                "Consequent": "GO"
            }
        ]
    }
}
```

### Test Harness

```python
from unittest import TestCase

from services.adapter.simple_rule_engine_adapter import SimpleRuleEngineAdapter
from services.util.json_file_util import JsonFileUtil


class TestSimpleRuleEngineAdapter(TestCase):
    def test_rule_simple_decision(self):
        json_file_util = JsonFileUtil(file_name_with_path="./examples/simple_decision.json")
        decision_dict = json_file_util.read_file()

        rule_engine_adapter = SimpleRuleEngineAdapter(rule_dict=decision_dict)
        decision_rule = rule_engine_adapter.get_rule()

        assert type(decision_rule).__name__ == "RuleDecision"

        fact = dict(cibil_score=700, business_ownership="Owned by Self")
        assert decision_rule.execute(token_dict=fact) == "GO"
```
