import logging
import os
from parser.service import rule_engine_service
from common.configure.config import load_config

__logger = logging.getLogger(__name__)

__logger.info("Loading environment........")
env_name = os.environ.get('env')

if not env_name:
    env_name = 'sandbox'

load_config(env_name)


def test_execute_simple_decision():
    """
    this test executes a simple decision and validates the results
    :return:
    """
    print('testing a simple decision')
    _rule_name = "eligibility_criteria"
    _body = {
        "facts": {
                "cibil_score": 700,
                "marital_status": "Married",
                "business_ownership": "Owned by Self"
            }
    }

    print(_rule_name)
    result = rule_engine_service.execute_rule_engine_service(
        _rule_name,
        _body
    )

    print(result)

    assert (
            result
            and "code" in result and result["code"] == 0
            and "message" in result and result["message"]
            and "final_decision" in result["message"]
            and result["message"]["final_decision"] == 'GO'
    )
