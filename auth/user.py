global claims
claims = {}


def get_claims():
    """

    :return:
    """
    global claims
    return claims


def get_claims(key):
    """

    :return:
    """
    global claims
    return claims.get(key)


def set_claims(p_claims):
    """

    :param p_claims:
    :return:
    """
    global claims
    claims = p_claims
