from config import cognito_pkey
from config import config

def pool_url(aws_region, aws_user_pool):
    """ Create an Amazon cognito issuer URL from a region and pool id
    Args:
        aws_region (string): The region the pool was created in.
        aws_user_pool (string): The Amazon region ID.
    Returns:
        string: a URL
    """
    return (
        "https://cognito-idp.{}.amazonaws.com/{}".
        format(aws_region, aws_user_pool)
    )


def aws_key_dict(aws_region, aws_user_pool):
    """ Fetches the AWS JWT validation file (if necessary) and then converts
    this file into a keyed dictionary that can be used to validate a web-token
    we've been passed
    Args:
        aws_region (string): aws region for the user pool
        aws_user_pool (string): the ID for the user pool
    Returns:
        dict: a dictonary of values
    """

    """    
    filename = os.path.abspath(
        os.path.join(
            os.path.dirname(sys.argv[0]), 'aws_{}.json'.format(aws_user_pool)
        )
    )

    if not os.path.isfile(filename):
        # If we can't find the file already, try to download it.
        aws_data = requests.get(
            pool_url(aws_region, aws_user_pool) + '/.well-known/jwks.json'
        )
        aws_jwt = json.loads(aws_data.text)
        with open(filename, 'w+') as json_data:
            json_data.write(aws_data.text)
            json_data.close()

    else:
        with open(filename) as json_data:
            aws_jwt = json.load(json_data)
            json_data.close()
    """

    aws_jwt = cognito_pkey.cognito_user_pool_jwks
    # We want a dictionary keyed by the kid, not a list.
    result = {}
    env = config.get_config('env')
    if 'envs' in aws_jwt:
        for aws_jwt_env in aws_jwt['envs']:
            if aws_jwt_env["name"] == env:
                for item in aws_jwt_env['keys']:
                    result[item['kid']] = item

    return result
# def aws_key_dict

