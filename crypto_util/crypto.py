import base64
import boto3
import blowfish
import logging
import os
from botocore.exceptions import ClientError
import json

__logger = logging.getLogger(__name__)


# Jeya@12-Nov-2018 New function created to retrieve secret from aws secrets manager
def __get_secret():

    secret_name = "prod/accessKey"
    region_name = "ap-south-1"

    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )

    # In this sample we only handle the specific exceptions for the 'GetSecretValue' API.
    # See https://docs.aws.amazon.com/secretsmanager/latest/apireference/API_GetSecretValue.html
    # We rethrow the exception by default.

    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
    except ClientError as e:
        if e.response['Error']['Code'] == 'DecryptionFailureException':
            # Secrets Manager can't decrypt the protected secret text using the provided KMS key.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response['Error']['Code'] == 'InternalServiceErrorException':
            # An error occurred on the server side.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response['Error']['Code'] == 'InvalidParameterException':
            # You provided an invalid value for a parameter.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response['Error']['Code'] == 'InvalidRequestException':
            # You provided a parameter value that is not valid for the current state of the resource.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response['Error']['Code'] == 'ResourceNotFoundException':
            # We can't find the resource that you asked for.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
    else:
        # Decrypts secret using the associated KMS CMK.
        # Depending on whether the secret is a string or binary, one of these fields will be populated.
        if 'SecretString' in get_secret_value_response:
            secret = get_secret_value_response['SecretString']
            return secret
        else:
            decoded_binary_secret = base64.b64decode(get_secret_value_response['SecretBinary'])
            return decoded_binary_secret


def decrypt(encrypted_value):
    """

    :param encrypted_value:
    :return:
    """

    __logger.info("Decrypt value..." + encrypted_value)

    # Jeya@12-Nov-2018 Access Key is obtained from aws secrets manager.
    # session = botocore.session.get_session()
    #
    # assert isinstance(session, object)
    # access_key = session.get_credentials().access_key
    # access_key = os.environ.get('access_key')

    secret = __get_secret()
    secret_json = json.loads(secret)

    if "access_key" in secret_json:
        access_key = secret_json["access_key"]
    else:
        return None

    access_key_bytes = base64.b64decode(access_key)

    # initialize blow fish cipher object using aws access key credential
    cipher = blowfish.Cipher(access_key_bytes)

    # pass encrypted password to the cipher to decrypt
    db_pwd_bytes = bytes(encrypted_value, 'utf-8')

    db_pwd_encrypted = base64.b64decode(db_pwd_bytes)

    data_decrypted = b"".join(cipher.decrypt_ecb_cts(db_pwd_encrypted))

    # convert decrypted password into string
    data_decrypt = data_decrypted.decode('utf-8')

    return data_decrypt
