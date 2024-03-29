# simple-rule-engine-client

An extension to [Simple Rule Engine](https://github.com/jeyabalajis/simple-rule-engine) that illustrates how rules can be declaratively specified (json, yaml, custom grammar etc.), stored, and later de-serialized into simple-rule-engine constructs and executed with data.

[![CircleCI](https://dl.circleci.com/status-badge/img/gh/jeyabalajis/simple-rule-engine-client/tree/main.svg?style=shield)](https://dl.circleci.com/status-badge/redirect/gh/jeyabalajis/simple-rule-engine-client/tree/main)

# Table of Contents

- [A Simple Decision Tree](#a-simple-decision-tree-involving-facts)
- [A Simple Scoring Rule](#a-simple-scoring-rule)
- [Custom SQL Like Rule Grammar](#custom-sql-like-rule-grammar)

# Examples

## A simple decision tree involving facts

### Decision matrix

| Bureau Score | Business Ownership | Decision
| :----------: | :----------------: | --------:|
| between 650 and 800        | in [Owned by Self, Owned by Family] | GO       |

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

from services.adapter.simple_rule_engine_dict_adapter import SimpleRuleEngineDictAdapter
from services.util.json_file_util import JsonFileUtil


class TestSimpleRuleEngineAdapter(TestCase):
    def test_rule_simple_decision(self):
        json_file_util = JsonFileUtil(file_name_with_path="./examples/simple_decision.json")
        decision_rule_dict = json_file_util.read_file()

        rule_engine_adapter = SimpleRuleEngineDictAdapter(rule_dict=decision_rule_dict)
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

from services.adapter.simple_rule_engine_dict_adapter import SimpleRuleEngineDictAdapter
from services.util.json_file_util import JsonFileUtil


class TestSimpleRuleEngineAdapter(TestCase):
    def test_rule_simple_score(self):
        json_file_util = JsonFileUtil(file_name_with_path="./examples/simple_score.json")
        score_rule_dict = json_file_util.read_file()

        rule_engine_adapter = SimpleRuleEngineDictAdapter(rule_dict=score_rule_dict)
        score_rule = rule_engine_adapter.get_rule()

        assert type(score_rule).__name__ == "RuleScore"

        fact = dict(age=40, pet="dog", domicile="TN")
        assert score_rule.execute(token_dict=fact) == 5.0

        fact = dict(age=40, pet="dog", domicile="KA")
        assert score_rule.execute(token_dict=fact) == 7.5
```

## Custom SQL Like Rule Grammar

Here's an illustration of a rule that's based on a [custom grammar](decision_rule.lark) written in [EBNF](https://en.wikipedia.org/wiki/Extended_Backus%E2%80%93Naur_form) and parsed by [Lark](https://github.com/lark-parser/lark).

### Sample Rule
```lark
my_rule {
    when {
        cibil_score between 650 and 750 and 
        age > 35 and 
        house_ownership in (owned, rented) and
        (
            total_overdue_amount == 0 or 
            number_of_overdue_loans < 2 or
            (
                number_of_overdue_loans >= 2 and
                big_shot == true
            )
        ) and
        pet == dog
    }
    then true
    when {
        cibil_score < 650
    }
    then false
}
```

### Parse Tree

```
start
  decisionrule
    my_rule
    rulerow
      when
      condition
        expression
          token	cibil_score
          between
          number	650
          number	750
        conditional	and
        expression
          token	age
          gt
          number	35
        conditional	and
        expression
          token	house_ownership
          in
          word_list
            owned
            rented
        conditional	and
        expression
          expression
            token	total_overdue_amount
            eq
            number	0
          conditional	or
          expression
            token	number_of_overdue_loans
            lt
            number	2
          conditional	or
          expression
            expression
              token	number_of_overdue_loans
              gte
              number	2
            conditional	and
            expression
              token	big_shot
              eq
              boolean	true
        conditional	and
        expression
          token	pet
          eq
          string	dog
      then
      decision
        boolean	true
    rulerow
      when
      condition
        expression
          token	cibil_score
          lt
          number	650
      then
      decision
        boolean	false
```

### Test Harness

```python
import pytest
from lark import Lark

from services.adapter.simple_rule_engine_lark_tree_adapter import SimpleRuleEngineLarkTreeAdapter


@pytest.fixture
def decision_rule_grammar():
    with open("./decision_rule.lark") as rule_grammar_file:
        rule_grammar = rule_grammar_file.read()

    return rule_grammar

def test_rule_complex_decision(decision_rule_grammar):
    parser = Lark(decision_rule_grammar)

    custom_rule = """
        my_rule {
            when {
                cibil_score between 650 and 750 and 
                age > 35 and 
                house_ownership in (owned, rented) and
                (
                    total_overdue_amount == 0 or 
                    number_of_overdue_loans < 2 or
                    (
                        number_of_overdue_loans >= 2 and
                        big_shot == true
                    )
                ) and
                pet == dog
            }
            then true
            when {
                cibil_score < 650
            }
            then false
        }
        """

    tree = parser.parse(custom_rule)
    print(tree.pretty())

    decision_rule = SimpleRuleEngineLarkTreeAdapter(tree).get_rule()

    # Evaluate the Decision Rule by passing data
    facts = dict(
        cibil_score=700,
        age=40,
        house_ownership="owned",
        total_overdue_amount=0,
        pet="dog"
    )
    assert decision_rule.execute(token_dict=facts) is True

    facts = dict(
        cibil_score=700,
        age=40,
        house_ownership="owned",
        total_overdue_amount=100,
        number_of_overdue_loans=1,
        pet="dog"
    )
    assert decision_rule.execute(token_dict=facts) is True

    facts = dict(
        cibil_score=700,
        age=40,
        house_ownership="owned",
        total_overdue_amount=100,
        number_of_overdue_loans=2,
        big_shot="true",
        pet="dog"
    )
    assert decision_rule.execute(token_dict=facts) is True

    facts = dict(
        cibil_score=600,
        age=40,
        house_ownership="owned",
        total_overdue_amount=100,
        number_of_overdue_loans=2,
        big_shot="false",
        pet="dog"
    )
    assert decision_rule.execute(token_dict=facts) is False
```
