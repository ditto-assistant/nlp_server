class ReqQuery:
    def __init__(self, args):
        self.args = args

    def offset(self, default=0):
        return self.args.get("offset", default)

    def limit(self, default=10):
        return self.args.get("limit", default)

    def is_asc_order(self, default=False):
        default = "ASC" if default else "DESC"
        order = self.args.get("order", default).upper()
        if order not in ["ASC", "DESC"]:
            return ErrInvalidQuery("order", order)
        return True if order == "ASC" else False


def ErrInvalidQuery(key: str, val: str):
    return '{"error": "invalid query param %s: %s"}' % (key, val)
