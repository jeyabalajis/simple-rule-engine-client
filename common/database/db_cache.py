global db_cache
db_cache = {}


def __is_empty(any_structure):
    if any_structure:
        return False
    else:
        return True


def get_db_cache(db_name):
    """

    :param db_name:
    :return:
    """
    global db_cache
    if not __is_empty(db_cache) and db_name in db_cache:
        return db_cache[db_name]
    else:
        return {}


def set_db_cache(db_name, db_handle):
    """

    :param db_name:
    :param db_handle:
    :return:
    """

    global db_cache
    db_cache[db_name] = db_handle
