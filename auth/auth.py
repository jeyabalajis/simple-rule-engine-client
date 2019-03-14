import functools
import logging
import json
import connexion

from auth import user
from config import config
from database import sms_db_functions
import requests

__logger = logging.getLogger(__name__)


def __is_empty(any_structure: object) -> object:
    if any_structure:
        return False
    else:
        return True


def get_claims(aws_region, aws_user_pool, token, audience=None):
    """ Given a token (and optionally an audience), validate and
    return the claims for the token
    """
    """
    header = jwt.get_unverified_header(token)
    kid = header['kid']

    verify_url = aws_utils.pool_url(aws_region, aws_user_pool)

    keys = aws_utils.aws_key_dict(aws_region, aws_user_pool)

    key = keys.get(kid)

    kargs = {"issuer": verify_url}
    if audience is not None:
        kargs["audience"] = audience

    claims = jwt.decode(
        token,
        key,
        **kargs
    )
    """
    __logger.info("Inside Token validation get claims!!!")
    token_validate_url = config.get_config('cognito_token_validate_url')
    token_validate_header = {"Content-Type": config.get_config('content_type')}
    token_validate_payload = {"authorizationToken": token}

    __logger.info(json.dumps(token_validate_url, indent=4, sort_keys=True, default=str))
    __logger.info(json.dumps(token_validate_header, indent=4, sort_keys=True, default=str))
    __logger.info(json.dumps(token_validate_payload, indent=4, sort_keys=True, default=str))

    claims = {}
    try:
        resp = requests.post(token_validate_url, headers=token_validate_header, json=token_validate_payload)

        __logger.info("Response code: " + str(resp.status_code))

        if resp.status_code == 200:
            __logger.info(json.dumps(resp.json(), indent=4, sort_keys=True, default=str))
            claims = resp.json()
    except:
        import traceback
        __logger.error("calling token validator url failed!!!")
        __logger.error(traceback.format_exc())

    return claims


def __validate_store_jwt(p_jwt):
    """

    :param p_jwt:
    :return:
    """
    try:

        __logger.info("Inside validate and store jwt")

        cognito_region = config.get_config('cognito_region')
        cognito_user_pool_id = config.get_config('cognito_user_pool_id')
        cognito_client_id = config.get_config('cognito_client_id')

        claims = get_claims(cognito_region, cognito_user_pool_id, p_jwt, cognito_client_id)

        if not __is_empty(claims):
            user.set_claims(claims)
            __logger.info(claims)
            return {"code": 0, "message": "Authentication successful!"}
        else:
            return {"code": 1, "message": "Authentication failed!"}

    except:
        import traceback
        __logger.error("jwt token invalid!!!")
        __logger.error(traceback.format_exc())
        return {"code": 1, "message": "Invalid Authentication token."}


def authenticate(func):
    @functools.wraps(func)
    def authenticate_and_call(*args, **kwargs):
        __logger.info("Inside Authenticate!!!")
        if 'Bearer' in connexion.request.headers:
            __logger.info("Bearer: " + connexion.request.headers["Bearer"])

            result = __validate_store_jwt(connexion.request.headers["Bearer"])
            if not __is_empty(result):
                if result["code"] == 1:
                    return connexion.problem(400, "Authentication Failed!", result["message"])
                if result["code"] == 2:
                    return connexion.problem(400, "Authentication Failed!", result["message"])
                if result["code"] == 0:
                    __logger.info("Authentication successful!!!")
            else:
                return connexion.problem(400, "Authentication Failed!", "Invalid credentials")
        else:
            return connexion.problem(400, "Authentication Failed!", "Authentication failed. missing Bearer token.")
        return func(*args, **kwargs)

    return authenticate_and_call


def validate_access_control(api_resource, api_method):
    """

    :param api_resource:
    :param api_method:
    :return:
    """

    api_id = config.get_config('api_id')
    group_list = user.get_claims('cognito:groups')

    __logger.info(api_id)
    __logger.info(group_list)
    __logger.info(api_resource)
    __logger.info("get access control list for this api and user group")
    acl_list = sms_db_functions.sms_get_access_control_list(api_id, group_list)

    result = {"code": 1, "message": "Not Authorized to perform this action!!!"}
    if not __is_empty(acl_list) and not __is_empty(group_list):
        for acl in acl_list:
            if "functions" in acl:
                for function_acl in acl["functions"]:
                    __logger.info("resource name: " + function_acl["resource_name"])
                    if "resource_name" in function_acl and api_resource == function_acl["resource_name"]:
                        __logger.info("checking acl for resource name: " + api_resource)
                        if "methods" in function_acl:
                            for method_acl in function_acl["methods"]:
                                __logger.info("checking method: " + method_acl["acl"])
                                if "acl" in method_acl and \
                                        api_method == method_acl["method_name"] \
                                        and method_acl["acl"] == "allow":
                                    __logger.info("resource and method allowed")
                                    result = {"code": 0, "message": "Authorized to perform this action."}
                                    break

    __logger.info(json.dumps(result, indent=4, sort_keys=True, default=str))
    return result


def authorize(api_resource, api_method):
    def authorize_decorator(func):
        @functools.wraps(func)
        def authorize_and_call(*args, **kwargs):
            # Perform authorization based on user profile
            # if not Account.is_authentic(request):
            #    raise Exception('Authentication Failed.')
            __logger.info("Inside Authorize!!!")
            __logger.info(api_resource + api_method)

            result = validate_access_control(api_resource, api_method)

            if not __is_empty(result) and "code" in result and "message" in result:
                if result["code"] == 0:
                    __logger.info("call api method to perform action!")
                    return func(*args, **kwargs)
                else:
                    __logger.info("authorization failed!")
                    return connexion.problem(400, "Authorization Failed!", result["message"])
            else:
                return connexion.problem(400, "Authorization Failed!", "Authorization failed.")

        return authorize_and_call

    return authorize_decorator
