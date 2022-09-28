# simple-serverless-rule-engine
A _lightweight_ yet _powerful_ rule engine that allows declarative specification of business rules and **saves tons of repeated development work**.

This framework already powered more than 100K scores & decisions at [FUNDSCORNER](https://www.fundscorner.com) and can be deployed as a serverless function (FaaS) or as a container.

For an object oriented take on this rule engine, please see [Simple Rule Engine](https://github.com/jeyabalajis/simple-rule-engine)

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
