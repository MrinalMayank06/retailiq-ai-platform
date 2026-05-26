class RetailIQError(Exception):
    pass


class DataValidationError(RetailIQError):
    pass


class ModelNotFoundError(RetailIQError):
    pass
