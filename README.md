# simple-serverless-rule-engine
A _lightweight_ yet _powerful_ rule engine that allows declarative specification of business rules and **saves tons of repeated development work**.

This framework already powered more than 100K scores & decisions at [FUNDSCORNER](https://www.fundscorner.com) and can be deployed as a serverless function (FaaS) or as a container.

## Key Features
1. Ability to __declaratively__ author both Scoring and Decision Rules.
2. Ability to __version control__ rule declarations thus enabling auditing of rule changes over a period of time.
3. Ability to author **_chained rules_**. Evaluation of one rule can refer to the result of another rule, thus enabling 
modular, hierarchical rules. 
4. The rule engine is __server less__! - perfect for hosting it as an independent micro-service.
5. The consumer of the rules services __will not__ know about the rule details. The consumer just invokes the service and get the rule results. This enables a clean segregation between rule owners & rule consumers.
6. Written in Python 3.6 with minimal requirements

## Demo

1. Clone or download the project into your local repository.
2. Import the postman collection stored under examples folder into Postman
3. Try out the service!  

## Installation Instructions

### Pre-requisites

#### Database
1. The rule templates must be stored in a MongoDB schema. You can specify the schema name under config.ini against the key rule_db
2. You can refer to the examples folder for some common examples of rule templates for both Score and Decision rules

#### AWS
1. Create a secret name prod/DBAuthentication with the following key value pairs to point to the rules database

|Key Name|Value|
|:------:|:---:|
|db_url|URI of the MongoDB Database|
|user_name|User name to login to the database|
|password|Password to login to the database|

1. Clone or download the project into your local repository.
2. Create a virtual environment with Python 3.6 or above and activate the same.
3. To deploy this as a FaaS through [AWS Lambda](https://aws.amazon.com/lambda/), use [Zappa](https://www.zappa.io/), a framework for Serverless Python Web Services - Powered by AWS Lambda and API Gateway
4. To deploy this as a container in a Kubernetes cluster, use [Fission](https://fission.io/), a framework for serverless functions on Kubernetes.

# Table of Contents
- [Why Rule Engine](#Why-Rule-Engine)
- [Concepts](#Concepts)
- [Examples](#Examples)
- [API Specification](#API-Specification)

# Why Rule Engine?
Decision making has always been at the heart of any business. In certain industries (such as Lending), some of the decisions made are so dynamic & at a flux that programming these decisions by hand is counter-productive.

Take the example of the decision of giving someone a loan. It primarily involves ascertaining two fundamental factors:
- Ability to repay the loan.
- Intent to repay the loan.

When you start assessing a borrower based on above, you typically get all facts required to make a decision (such as Bureau score, bank statements etc.) and you will pass these facts through a decision matrix to arrive at 
- A composite score on a scale that gives an indication of _whether the borrower will repay the loan_ (**intent**)
- A recommendation of _how much loan_ should be given to the borrower. (**ability**)

The aforementioned decisions involve evaluation of multiple parameters. You simply cannot write a program to solve such complex scoring or decision problems:
 - The evaluations and/or scores will _always_ change over a period of time to adjust to business needs 
- The _rules_ will also change based on the nature of the business product.

> The simple-serverless-rule-engine solves such dynamic decision making problems by abstracting the scoring or decision making into a _framework_ and providing a standard rule template (JSON) to author the rules. 

>  As a result, we can conveniently treat the rule engine as a service and just by passing all the facts (a.k.a inputs), we get the the corresponding decisions or scores (output)!

### Benefits
- Declarative authoring of rules. This can be done by a business analyst, rather than a developer. The developer just focuses on extracting the facts that are required to be passed into the engine.
- Versioning of rules to enable the auditing of the rule changes over a period of time.

# Concepts

The simple-serverless-rule-engine is composed of two parts:

- A Rule template which enables one to declaratively specify a rule, which can either be a Decision (or) a Score. The rule template is uniquely identified by a name.
- A parser engine which when passed with a rule name & facts, parses the rule template against the facts given and provides an output. The output can either be a score (numeric) or a decision (anything).

The simple-serverless-rule-engine allows the rules to be _“chained”_. I.e. you can build a small portion of the score as an independent rule and _“use”_ this rule in another rule. 

> At the heart of simple-serverless-rule-engine is the rule declaration language. 

> A rule can either be a Decision or a Score.

## Score rule:
- A Score rule is composed of one or many rule sets. 
- Each rule-set computes a sub-score and is applied a weight. 
- The total score then would be the sum of all the individual scores of all the rule sets belonging to a rule.
- A rule set is composed of one or many rule rows. 
- You can ‘roughly’ think of each Rule Row as a Conditional evaluation of the facts (a.k.a antecedent) & a score based on these conditions (a.k.a consequent).
 
![Score Rule Concept](/images/score_rule.png)


## Decision rule:
- A Decision rule is always composed of only one rule set.
- A rule set is composed of one or many rule rows. 
- You can ‘roughly’ think of each Rule Row as a Conditional evaluation of the facts (a.k.a antecedent) & a score based on these conditions (a.k.a consequent).
- A decision rule always arrives at a single decision at the end of parsing.
- The decision can be anything (a numeric, a string such as YES/NO or even a JSON)

![Decision Rule Concept](/images/decision_rule.png)


## Antecedent and Consequent

- An antecedent at the core is an evaluator. It evaluates one or many facts through an operator.
- For evaluating numeric facts, a numeric operator is used. It can be one of (<=, <, >, >=, ==, <>, between, is_none)
- For evaluating string facts, a string operator is used. It can be one of (in_list, contains, is_none, equals)
- You can mix evaluation of more than one fact & combine the result with an “and” or “or” condition.
- You can perform complex evaluations involving multiple facts combining AND and OR conditions recursively in the antecedent. See [Examples](#Examples).
- The system allows a total recursion depth of 5 to allow complex evaluations.
- You can use the result of a rule as a token! This way you can build simple modular rules & combine them to get to a bigger rule.

# Examples

## A simple decision tree involving facts

### Decision matrix

| Bureau Score | Marital Status | Business Ownership | Decision
| :----------: | :----------------: | :----------------: | --------:|
| between 650 and 800        | in [Married, Unspecified]                | in [Owned by Self, Owned by Family] | GO       |

### Rule specification
```json
{ 
    "rule_name" : "eligibility_criteria", 
    "rule_description" : "Eligibility Criteria", 
    "rule_type" : "decision", 
    "rule_set" : {
        "set_name" : "eligibility_criteria", 
        "rule_set_type" : "evaluate", 
        "rule_rows" : [
            {
                "antecedent" : {
                    "@when_all" : [
                        {
                            "token_category" : "organic", 
                            "token_name" : "cibil_score", 
                            "operator" : "between", 
                            "eval_value" : {
                                "low" : 650, 
                                "high" : 800
                            }, 
                            "token_type" : "numeric"
                        }, 
                        {
                            "token_category" : "organic", 
                            "token_name" : "marital_status", 
                            "operator" : "in_list", 
                            "eval_value" : [
                                "Married", 
                                "Unspecified"
                            ], 
                            "token_type" : "string"
                        }, 
                        {
                            "token_category" : "organic", 
                            "token_name" : "business_ownership", 
                            "operator" : "in_list", 
                            "eval_value" : [
                                "Owned by Self", 
                                "Owned by Family"
                            ], 
                            "token_type" : "string"
                        }
                    ]
                }, 
                "consequent" : {
                    "decision" : "GO"
                }
            }
        ]
    }, 
    "version" : 1
}
```

## A complex decision tree involving multiple AND  and OR conditions

### Decision matrix

| Applicant Age | Applicant Ownership| Business Ownership | Decision
| :----------: | :----------------: | :----------------: | --------:|
| >=35        | in [Owned by Self, Owned by Family]                | in [Owned by Self, Owned by Family] | GO       |
| >=35        | in [Owned by Self, Owned by Family]                | in [Rented] | GO       |
| >=35        | in [Rented]                | in [Owned by Self, Owned by Family] | GO       |
| >=35        | in [Rented]                | in [Rented] | NO GO       |
| <35        | in [Rented]                | in [Rented] | NO GO       |
| <35        | in [Owned by Self, Owned by Family]                | in [Rented] | NO GO       |
| <35        | in [Rented]                | in  [Owned by Self, Owned by Family] | NO GO       |
| <35        | in [Owned by Self, Owned by Family]                | in [Owned by Self, Owned by Family] | GO       |

- when the applicant age is >=35, either of applicant ownership or business ownership must be Owned.
- When the applicant age is <35, both the applicant ownership and business ownership must be Owned.


### Rule specification
```json
{
  "rule_name": "eligibility_criteria",
  "rule_description": "Eligibility Criteria",
  "rule_type": "decision",
  "rule_set": {
    "set_name": "eligibility_criteria",
    "rule_set_type": "evaluate",
    "rule_rows": [
      {
        "antecedent": {
          "@when_all": [
            {
              "token_category": "organic",
              "token_name": "applicant_age",
              "operator": ">=",
              "eval_value": 35,
              "token_type": "numeric"
            },
            {
              "@when_any": [
                {
                  "token_category": "organic",
                  "token_name": "applicant_ownership",
                  "operator": "in_list",
                  "eval_value": [
                    "Owned by Self",
                    "Owned by Family"
                  ],
                  "token_type": "string"
                },
                {
                  "token_category": "organic",
                  "token_name": "business_ownership",
                  "operator": "in_list",
                  "eval_value": [
                    "Owned by Self",
                    "Owned by Family"
                  ],
                  "token_type": "string"
                }
              ]
            }
          ]
        },
        "consequent": {
          "decision": "GO"
        }
      },
      {
        "antecedent": {
          "@when_all": [
            {
              "token_category": "organic",
              "token_name": "applicant_age",
              "operator": "<=",
              "eval_value": 35,
              "token_type": "numeric"
            },
            {
              "token_category": "organic",
              "token_name": "applicant_ownership",
              "operator": "in_list",
              "eval_value": [
                "Owned by Self",
                "Owned by Family"
              ],
              "token_type": "string"
            },
            {
              "token_category": "organic",
              "token_name": "business_ownership",
              "operator": "in_list",
              "eval_value": [
                "Owned by Self",
                "Owned by Family"
              ],
              "token_type": "string"
            }
          ]
        },
        "consequent": {
          "decision": "GO"
        }
      }
    ]
  },
  "version": 1
}
```

## A scoring rule involving multiple parameters
|Rule set Name|Weightage|
|:-----------:|:-------:|
|no_of_running_bl_pl|0.3|
|last_loan_drawn_in_months|0.3|
|no_of_bl_paid_off_successfully|0.2|
|value_of_bl_paid_successfully|0.2|

### no_of_running_bl_pl
|Condition|Score|
|:-----------:|:-------:|
|no_of_running_bl_pl >= 7 |-100|
|no_of_running_bl_pl >= 4 |-40|
|no_of_running_bl_pl >= 2 |30|
|no_of_running_bl_pl >= 0 |100|
|no_of_running_bl_pl is none |100|

### last_loan_drawn_in_months
|Condition|Score|
|:-----------:|:-------:|
|last_loan_drawn_in_months == 0 |30|
|last_loan_drawn_in_months <3 |-30|
|last_loan_drawn_in_months <= 12 |40|
|last_loan_drawn_in_months >12 |100|
|last_loan_drawn_in_months is none |100|


### no_of_bl_paid_off_successfully
|Condition|Score|
|:-----------:|:-------:|
|no_of_bl_paid_off_successfully == 0 |30|
|no_of_bl_paid_off_successfully <=2 |70|
|no_of_bl_paid_off_successfully <= 4 |85|
|no_of_bl_paid_off_successfully >4 |100|
|no_of_bl_paid_off_successfully is none |100|

### value_of_bl_paid_successfully
|Condition|Score|
|:-----------:|:-------:|
|value_of_bl_paid_successfully == 0 |30|
|value_of_bl_paid_successfully <=100000 |35|
|value_of_bl_paid_successfully <= 400000 |50|
|value_of_bl_paid_successfully > 400000 |100|
|value_of_bl_paid_successfully is none |100|

### Test Cases
|no_of_running_bl_pl|last_loan_drawn_in_months|no_of_bl_paid_off_successfully|value_of_bl_paid_successfully|Final Score|
|:-----------:|:-------:|:-----------:|:-------:|:---------:|
|8|2|0|0| -27|  
|0|13|5|none| 100|

### Rule Specification
```json
{ 
    "rule_name" : "bureau_score_loans", 
    "rule_description" : "bureau_score_loans", 
    "rule_type" : "score", 
    "rule_set" : [
        {
            "set_name" : "no_of_running_bl_pl", 
            "weight" : 0.3, 
            "rule_set_type" : "evaluate", 
            "rule_rows" : [
                {
                    "antecedent" : {
                        "token_name" : "no_of_running_bl_pl", 
                        "token_type" : "numeric", 
                        "token_category" : "organic", 
                        "operator" : ">=", 
                        "eval_value" : 7.0
                    }, 
                    "consequent" : {
                        "score" : -100.0
                    }
                }, 
                {
                    "antecedent" : {
                        "token_name" : "no_of_running_bl_pl", 
                        "token_type" : "numeric", 
                        "token_category" : "organic", 
                        "operator" : ">=", 
                        "eval_value" : 4.0
                    }, 
                    "consequent" : {
                        "score" : -40.0
                    }
                }, 
                {
                    "antecedent" : {
                        "token_name" : "no_of_running_bl_pl", 
                        "token_type" : "numeric", 
                        "token_category" : "organic", 
                        "operator" : ">=", 
                        "eval_value" : 2.0
                    }, 
                    "consequent" : {
                        "score" : 30.0
                    }
                }, 
                {
                    "antecedent" : {
                        "token_name" : "no_of_running_bl_pl", 
                        "token_type" : "numeric", 
                        "token_category" : "organic", 
                        "operator" : ">=", 
                        "eval_value" : 0.0
                    }, 
                    "consequent" : {
                        "score" : 100.0
                    }
                }, 
                {
                    "antecedent" : {
                        "token_name" : "no_of_running_bl_pl", 
                        "token_type" : "numeric", 
                        "token_category" : "organic", 
                        "operator" : "is_none"
                    }, 
                    "consequent" : {
                        "score" : 100.0
                    }
                }
            ]
        }, 
        {
            "set_name" : "last_loan_drawn_in_months", 
            "weight" : 0.3, 
            "rule_set_type" : "evaluate", 
            "rule_rows" : [
                {
                    "antecedent" : {
                        "token_name" : "last_loan_drawn_in_months", 
                        "token_type" : "numeric", 
                        "token_category" : "organic", 
                        "operator" : "==", 
                        "eval_value" : 0.0
                    }, 
                    "consequent" : {
                        "score" : 30.0
                    }
                }, 
                {
                    "antecedent" : {
                        "token_name" : "last_loan_drawn_in_months", 
                        "token_type" : "numeric", 
                        "token_category" : "organic", 
                        "operator" : "<", 
                        "eval_value" : 3.0
                    }, 
                    "consequent" : {
                        "score" : -30.0
                    }
                }, 
                {
                    "antecedent" : {
                        "token_name" : "last_loan_drawn_in_months", 
                        "token_type" : "numeric", 
                        "token_category" : "organic", 
                        "operator" : "<=", 
                        "eval_value" : 12.0
                    }, 
                    "consequent" : {
                        "score" : 40.0
                    }
                }, 
                {
                    "antecedent" : {
                        "token_name" : "last_loan_drawn_in_months", 
                        "token_type" : "numeric", 
                        "token_category" : "organic", 
                        "operator" : ">", 
                        "eval_value" : 12.0
                    }, 
                    "consequent" : {
                        "score" : 100.0
                    }
                }, 
                {
                    "antecedent" : {
                        "token_name" : "last_loan_drawn_in_months", 
                        "token_type" : "numeric", 
                        "token_category" : "organic", 
                        "operator" : "is_none"
                    }, 
                    "consequent" : {
                        "score" : 100.0
                    }
                }
            ]
        }, 
        {
            "set_name" : "no_of_bl_paid_off_successfully", 
            "weight" : 0.2, 
            "rule_set_type" : "evaluate", 
            "rule_rows" : [
                {
                    "antecedent" : {
                        "token_name" : "no_of_bl_paid_off_successfully", 
                        "token_type" : "numeric", 
                        "token_category" : "organic", 
                        "operator" : "==", 
                        "eval_value" : 0.0
                    }, 
                    "consequent" : {
                        "score" : 30.0
                    }
                }, 
                {
                    "antecedent" : {
                        "token_name" : "no_of_bl_paid_off_successfully", 
                        "token_type" : "numeric", 
                        "token_category" : "organic", 
                        "operator" : "<=", 
                        "eval_value" : 2.0
                    }, 
                    "consequent" : {
                        "score" : 70.0
                    }
                }, 
                {
                    "antecedent" : {
                        "token_name" : "no_of_bl_paid_off_successfully", 
                        "token_type" : "numeric", 
                        "token_category" : "organic", 
                        "operator" : "<=", 
                        "eval_value" : 4.0
                    }, 
                    "consequent" : {
                        "score" : 85.0
                    }
                }, 
                {
                    "antecedent" : {
                        "token_name" : "no_of_bl_paid_off_successfully", 
                        "token_type" : "numeric", 
                        "token_category" : "organic", 
                        "operator" : ">", 
                        "eval_value" : 4.0
                    }, 
                    "consequent" : {
                        "score" : 100.0
                    }
                }, 
                {
                    "antecedent" : {
                        "token_name" : "no_of_bl_paid_off_successfully", 
                        "token_type" : "numeric", 
                        "token_category" : "organic", 
                        "operator" : "is_none"
                    }, 
                    "consequent" : {
                        "score" : 100.0
                    }
                }
            ]
        }, 
        {
            "set_name" : "value_of_bl_paid_successfully", 
            "weight" : 0.2, 
            "rule_set_type" : "evaluate", 
            "rule_rows" : [
                {
                    "antecedent" : {
                        "token_name" : "value_of_bl_paid_successfully", 
                        "token_type" : "numeric", 
                        "token_category" : "organic", 
                        "operator" : "==", 
                        "eval_value" : 0.0
                    }, 
                    "consequent" : {
                        "score" : 30.0
                    }
                }, 
                {
                    "antecedent" : {
                        "token_name" : "value_of_bl_paid_successfully", 
                        "token_type" : "numeric", 
                        "token_category" : "organic", 
                        "operator" : "<=", 
                        "eval_value" : 100000.0
                    }, 
                    "consequent" : {
                        "score" : 35.0
                    }
                }, 
                {
                    "antecedent" : {
                        "token_name" : "value_of_bl_paid_successfully", 
                        "token_type" : "numeric", 
                        "token_category" : "organic", 
                        "operator" : "<=", 
                        "eval_value" : 400000.0
                    }, 
                    "consequent" : {
                        "score" : 50.0
                    }
                }, 
                {
                    "antecedent" : {
                        "token_name" : "value_of_bl_paid_successfully", 
                        "token_type" : "numeric", 
                        "token_category" : "organic", 
                        "operator" : ">", 
                        "eval_value" : 400000.0
                    }, 
                    "consequent" : {
                        "score" : 100.0
                    }
                }, 
                {
                    "antecedent" : {
                        "token_name" : "value_of_bl_paid_successfully", 
                        "token_type" : "numeric", 
                        "token_category" : "organic", 
                        "operator" : "is_none"
                    }, 
                    "consequent" : {
                        "score" : 100.0
                    }
                }
            ]
        }
    ]
}
```


## A __chained__ score dependent on two other score rules

### Banking Score, which is dependent on inward_cheque_bounces_in_6_months and performance_ratios
```json
{ 
    "rule_name" : "banking_score", 
    "rule_description" : "banking_score", 
    "rule_type" : "score", 
    "rule_set" : [
        {
            "set_ name" : "inward_cheque_bounces_in_6_months_score", 
            "rule_name" : "inward_cheque_bounces_in_6_months", 
            "weight" : 0.4, 
            "rule_set_type" : "compute"
        }, 
        {
            "set_name" : "performance_ratios_score", 
            "rule_name" : "performance_ratios", 
            "weight" : 0.6, 
            "rule_set_type" : "compute"
        }
    ]
}
```

### inward_cheque_bounces_in_6_months
```json
{ 
    "rule_name" : "inward_cheque_bounces_in_6_months", 
    "rule_description" : "inward_cheque_bounces_in_6_months_score", 
    "rule_type" : "score", 
    "rule_set" : [
        {
            "set_name" : "inward_cheque_bounces_in_6months", 
            "weight" : 0.3, 
            "rule_set_type" : "evaluate", 
            "rule_rows" : [
                {
                    "antecedent" : {
                        "token_name" : "inward_cheque_bounces_in_6months", 
                        "token_type" : "numeric", 
                        "token_category" : "organic", 
                        "operator" : ">=", 
                        "eval_value" : 5.0
                    }, 
                    "consequent" : {
                        "score" : -100.0
                    }
                }, 
                {
                    "antecedent" : {
                        "token_name" : "inward_cheque_bounces_in_6months", 
                        "token_type" : "numeric", 
                        "token_category" : "organic", 
                        "operator" : ">=", 
                        "eval_value" : 3.0
                    }, 
                    "consequent" : {
                        "score" : 0.0
                    }
                }, 
                {
                    "antecedent" : {
                        "token_name" : "inward_cheque_bounces_in_6months", 
                        "token_type" : "numeric", 
                        "token_category" : "organic", 
                        "operator" : ">=", 
                        "eval_value" : 1.0
                    }, 
                    "consequent" : {
                        "score" : 50.0
                    }
                }, 
                {
                    "antecedent" : {
                        "token_name" : "inward_cheque_bounces_in_6months", 
                        "token_type" : "numeric", 
                        "token_category" : "organic", 
                        "operator" : "<=", 
                        "eval_value" : 0.0
                    }, 
                    "consequent" : {
                        "score" : 100.0
                    }
                }, 
                {
                    "antecedent" : {
                        "token_name" : "inward_cheque_bounces_in_6months", 
                        "token_type" : "numeric", 
                        "token_category" : "organic", 
                        "operator" : "is_none"
                    }, 
                    "consequent" : {
                        "score" : 100.0
                    }
                }
            ]
        }, 
        {
            "set_name" : "inward_cheque_bounces_in_3months", 
            "weight" : 0.7, 
            "rule_set_type" : "evaluate", 
            "rule_rows" : [
                {
                    "antecedent" : {
                        "token_name" : "inward_cheque_bounces_in_3months", 
                        "token_type" : "numeric", 
                        "token_category" : "organic", 
                        "operator" : ">=", 
                        "eval_value" : 3.0
                    }, 
                    "consequent" : {
                        "score" : -100.0
                    }
                }, 
                {
                    "antecedent" : {
                        "token_name" : "inward_cheque_bounces_in_3months", 
                        "token_type" : "numeric", 
                        "token_category" : "organic", 
                        "operator" : ">=", 
                        "eval_value" : 2.0
                    }, 
                    "consequent" : {
                        "score" : 0.0
                    }
                }, 
                {
                    "antecedent" : {
                        "token_name" : "inward_cheque_bounces_in_3months", 
                        "token_type" : "numeric", 
                        "token_category" : "organic", 
                        "operator" : ">=", 
                        "eval_value" : 1.0
                    }, 
                    "consequent" : {
                        "score" : 30.0
                    }
                }, 
                {
                    "antecedent" : {
                        "token_name" : "inward_cheque_bounces_in_3months", 
                        "token_type" : "numeric", 
                        "token_category" : "organic", 
                        "operator" : "==", 
                        "eval_value" : 0.0
                    }, 
                    "consequent" : {
                        "score" : 100.0
                    }
                }, 
                {
                    "antecedent" : {
                        "token_name" : "inward_cheque_bounces_in_3months", 
                        "token_type" : "numeric", 
                        "token_category" : "organic", 
                        "operator" : "is_none"
                    }, 
                    "consequent" : {
                        "score" : 100.0
                    }
                }
            ]
        }
    ]
}
```

### performance_ratios

```json
{ 
    "rule_name" : "performance_ratios", 
    "rule_description" : "performance_ratios_score", 
    "rule_type" : "score", 
    "rule_set" : [
        {
            "set_name" : "txn_value_growth_qoq_cq_pq", 
            "weight" : 0.4, 
            "rule_set_type" : "evaluate", 
            "rule_rows" : [
                {
                    "antecedent" : {
                        "token_name" : "txn_value_growth_qoq_cq_pq", 
                        "token_type" : "numeric", 
                        "token_category" : "organic", 
                        "operator" : "<", 
                        "eval_value" : 0.5
                    }, 
                    "consequent" : {
                        "score" : -100.0
                    }
                }, 
                {
                    "antecedent" : {
                        "token_name" : "txn_value_growth_qoq_cq_pq", 
                        "token_type" : "numeric", 
                        "token_category" : "organic", 
                        "operator" : "<", 
                        "eval_value" : 0.8
                    }, 
                    "consequent" : {
                        "score" : 35.0
                    }
                }, 
                {
                    "antecedent" : {
                        "token_name" : "txn_value_growth_qoq_cq_pq", 
                        "token_type" : "numeric", 
                        "token_category" : "organic", 
                        "operator" : "<", 
                        "eval_value" : 1.0
                    }, 
                    "consequent" : {
                        "score" : 70.0
                    }
                }, 
                {
                    "antecedent" : {
                        "token_name" : "txn_value_growth_qoq_cq_pq", 
                        "token_type" : "numeric", 
                        "token_category" : "organic", 
                        "operator" : ">=", 
                        "eval_value" : 1.0
                    }, 
                    "consequent" : {
                        "score" : 100.0
                    }
                }, 
                {
                    "antecedent" : {
                        "token_name" : "txn_value_growth_qoq_cq_pq", 
                        "token_type" : "numeric", 
                        "token_category" : "organic", 
                        "operator" : "is_none"
                    }, 
                    "consequent" : {
                        "score" : 0.0
                    }
                }
            ]
        }, 
        {
            "set_name" : "txn_value_growth_mom_cm_pm", 
            "weight" : 0.4, 
            "rule_set_type" : "evaluate", 
            "rule_rows" : [
                {
                    "antecedent" : {
                        "token_name" : "txn_value_growth_mom_cm_pm", 
                        "token_type" : "numeric", 
                        "token_category" : "organic", 
                        "operator" : "<", 
                        "eval_value" : 0.5
                    }, 
                    "consequent" : {
                        "score" : -100.0
                    }
                }, 
                {
                    "antecedent" : {
                        "token_name" : "txn_value_growth_mom_cm_pm", 
                        "token_type" : "numeric", 
                        "token_category" : "organic", 
                        "operator" : "<", 
                        "eval_value" : 0.8
                    }, 
                    "consequent" : {
                        "score" : 35.0
                    }
                }, 
                {
                    "antecedent" : {
                        "token_name" : "txn_value_growth_mom_cm_pm", 
                        "token_type" : "numeric", 
                        "token_category" : "organic", 
                        "operator" : "<", 
                        "eval_value" : 1.0
                    }, 
                    "consequent" : {
                        "score" : 70.0
                    }
                }, 
                {
                    "antecedent" : {
                        "token_name" : "txn_value_growth_mom_cm_pm", 
                        "token_type" : "numeric", 
                        "token_category" : "organic", 
                        "operator" : ">=", 
                        "eval_value" : 1.0
                    }, 
                    "consequent" : {
                        "score" : 100.0
                    }
                }, 
                {
                    "antecedent" : {
                        "token_name" : "txn_value_growth_mom_cm_pm", 
                        "token_type" : "numeric", 
                        "token_category" : "organic", 
                        "operator" : "is_none"
                    }, 
                    "consequent" : {
                        "score" : 0.0
                    }
                }
            ]
        }, 
        {
            "set_name" : "txn_value_variance_momin_momax", 
            "weight" : 0.2, 
            "rule_set_type" : "evaluate", 
            "rule_rows" : [
                {
                    "antecedent" : {
                        "token_name" : "txn_value_variance_momin_momax", 
                        "token_type" : "numeric", 
                        "token_category" : "organic", 
                        "operator" : "<", 
                        "eval_value" : 0.2
                    }, 
                    "consequent" : {
                        "score" : 0.0
                    }
                }, 
                {
                    "antecedent" : {
                        "token_name" : "txn_value_variance_momin_momax", 
                        "token_type" : "numeric", 
                        "token_category" : "organic", 
                        "operator" : "<", 
                        "eval_value" : 0.4
                    }, 
                    "consequent" : {
                        "score" : 30.0
                    }
                }, 
                {
                    "antecedent" : {
                        "token_name" : "txn_value_variance_momin_momax", 
                        "token_type" : "numeric", 
                        "token_category" : "organic", 
                        "operator" : "<", 
                        "eval_value" : 0.6
                    }, 
                    "consequent" : {
                        "score" : 60.0
                    }
                }, 
                {
                    "antecedent" : {
                        "token_name" : "txn_value_variance_momin_momax", 
                        "token_type" : "numeric", 
                        "token_category" : "organic", 
                        "operator" : ">=", 
                        "eval_value" : 0.6
                    }, 
                    "consequent" : {
                        "score" : 100.0
                    }
                }, 
                {
                    "antecedent" : {
                        "token_name" : "txn_value_variance_momin_momax", 
                        "token_type" : "numeric", 
                        "token_category" : "organic", 
                        "operator" : "is_none"
                    }, 
                    "consequent" : {
                        "score" : 0.0
                    }
                }
            ]
        }
    ]
}
```

# API Specification

## Get all rules

1. This end point gets all the rules that are part of the DB repository
 

### Method

__GET__

### Input

None

### Output

The rules stored in the DB repository are sent back. 
Fields exposed:
1. Rule name, 
2. Rule description 
3. Rule type (Score or Decision)  

## Get Rule Details

1. This end point gets the facts required for a rule
2. The same endpoint works for both Decision and Score rules.
 

### Method

__GET__

### Input

Specify rule name as part of the URL path

### Output

The facts required for the rule along with their type (numeric or string) are returned.

### Execute a rule

1. This end point executes a rule against the facts passed and produces rule engine output. 
2. The same endpoint works for both Decision and Score rules.

### Input

The input is a json with a root node __"facts"__. Under "facts", specify the name of the fact followed by the value, as a key value pair.

### Output

1. The output produces a __final_decision__ if the rule is a Decision rule (or) a __final_score__ if the rule is a Score rule.
2. The service also produces a detailed audit of which paths were evaluated as True during rule execution under the node __result_set__.
