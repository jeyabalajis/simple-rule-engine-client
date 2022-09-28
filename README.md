# simple-serverless-rule-engine

An extension to [Simple Rule Engine](https://github.com/jeyabalajis/simple-rule-engine) that illustrates how json based rules can be stored, de-serialized into simple-rule-engine constructs and executed with data.

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

