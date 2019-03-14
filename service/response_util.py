from flask import jsonify


def get_response(status, title, detail):
    """

    :param status:
    :param title:
    :param detail:
    :return:
    """
    return jsonify(
        status=status,
        title=title,
        detail=detail
    )
