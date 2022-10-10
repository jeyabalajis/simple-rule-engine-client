# simple-serverless-rule-engine

An extension to [Simple Rule Engine](https://github.com/jeyabalajis/simple-rule-engine) that illustrates how rules can be declaratively specified (json, yaml, custom grammar etc.), stored, and later de-serialized into simple-rule-engine constructs and executed with data.

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

## A simple scoring rule

### Scoring Rule

- If age >= 35 and pet in dog, score is 10, with a weight of 0.5
- If domicile is in KA, score is 5, with a weight of 0.5

### JSON Rule specification

```json
{
  "RuleScore": {
    "RuleSets": [
      {
        "RuleRows": [
          {
            "WhenAll": [
              {
                "NumericToken": "age",
                "Gte": 35
              },
              {
                "StringToken": "pet",
                "In": [
                  "dog"
                ]
              }
            ],
            "Consequent": 10
          }
        ],
        "Weight": 0.5
      },
      {
        "RuleRows": [
          {
            "WhenAll": [
              {
                "StringToken": "domicile",
                "In": [
                  "KA"
                ]
              }
            ],
            "Consequent": 5
          }
        ],
        "Weight": 0.5
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
    def test_rule_simple_score(self):
        json_file_util = JsonFileUtil(file_name_with_path="./examples/simple_score.json")
        score_rule_dict = json_file_util.read_file()

        rule_engine_adapter = SimpleRuleEngineAdapter(rule_dict=score_rule_dict)
        score_rule = rule_engine_adapter.get_rule()

        assert type(score_rule).__name__ == "RuleScore"

        fact = dict(age=40, pet="dog", domicile="TN")
        assert score_rule.execute(token_dict=fact) == 5.0

        fact = dict(age=40, pet="dog", domicile="KA")
        assert score_rule.execute(token_dict=fact) == 7.5
```

## Custom SQL Like Rule Grammar

This is currently work in progress.

Here's an illustration of a rule that's based on a [custom grammar](decision_rule.lark) written in [Lark](https://github.com/lark-parser/lark).

### Sample Rule
```lark
my_rule {
    when {
        cibil_score >= 650 and 
        age > 35 and 
        house_ownership in (owned, rented) and
        (
            total_overdue_amount == 0 or 
            number_of_overdue_loans < 2 or
            (
                number_of_overdue_loans >= 2 and
                big_shot == yes
            )
        ) and
        pet == dog
    }
    then true
    when {
        cibil_score < 650 or
        $RULE_overdue_rule < 0
    }
    then false
}
overdue_rule {
    when {
        overdue_in_months > 3
    }
    then -10
}
```

### Parse Tree (AST)

```
 start
   decisionrule
     my_rule
     rulerow
       expression
         cibil_score        
         >=
         650
       conditional       and
       expression
         age
         >
         35
       conditional       and
       expression
         house_ownership    
         in
         word_list
           owned
           rented
       conditional       and
       expression
         expression
           total_overdue_amount
           ==
           0
         conditional     or
         expression
           number_of_overdue_loans
           <
           2
         conditional     or
         expression
           expression
             number_of_overdue_loans
             >=
             2
           conditional   and
           expression
             big_shot
             ==
             yes
       conditional       and
       expression
         pet
         ==
         dog
       decision  true
     rulerow
       expression
         cibil_score
         <
         650
       conditional       or
       expression
         $RULE_overdue_rule
         <
         0
       decision  false
   decisionrule
     overdue_rule
     rulerow
       expression
         overdue_in_months
         >
         3
       decision  -10
```
