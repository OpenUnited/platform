from enum import IntEnum

class CurrencyTypes(IntEnum):
  USD = 1
  EUR = 2
  GBP = 3
  
  @classmethod
  def choices(cls):
    return [(key.value, key.name) for key in cls]

class PointTypes(IntEnum):
    NONLIQUID = 1
    LIQUID = 2
  
    @classmethod
    def choices(cls):
        return [(key.value, key.name) for key in cls]

class OrganisationAccountCreditReasons(IntEnum):
    GRANT = 1
    SALE = 2

    @classmethod
    def choices(cls):
        return [(key.value, key.name) for key in cls]


class PaymentTypes(IntEnum):
    NONE = 1
    ONLINE = 2
    OFFLINE = 3
    
    @classmethod
    def choices(cls):
        return [(key.value, key.name) for key in cls]


class PaymentStatusOptions(IntEnum):
    PENDING = 1
    PAID = 2
    CANCELLED = 3
    REFUNDED = 4
    
    @classmethod
    def choices(cls):
        return [(key.value, key.name) for key in cls]


class LifecycleStatusOptions(IntEnum):
    NEW = 1
    COMPLETE = 2
    CANCELLED = 3

    @classmethod
    def choices(cls):
        return [(key.value, key.name) for key in cls]


class CommunityStatusOptions(IntEnum):
    DRONE = 1
    HONEY_BEE = 2
    TRUSTED_BEE = 3
    QUEEN_BEE = 4
    BEE_KEEPER = 5

    @classmethod
    def choices(cls):
        return [(key.value, key.name) for key in cls]
