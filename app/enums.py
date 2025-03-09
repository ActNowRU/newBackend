import enum

class ModerationState(enum.Enum):
    on_check = "on_check"
    allowed = "allowed"
    denied = "denied"


class Gender(enum.Enum):
    male = "male"
    female = "female"


class Role(enum.Enum):
    admin = "admin"  # Admin of the platform
    org_admin = "org.admin"  # Admin of an organization
    # org_staff = "org.staff" # Staff member of an organization
    consumer = "consumer"  # Customer


class OrganizationType(enum.Enum):
    cafe = "кафе"
    restaurant = "ресторан"
    tattoo = "тату-салон"
    anticafe = "антикафе"
    bar = "бар"
    club = "клуб"
    beauty = "салон красоты"
    karaoke = "караоке"
    clinic = "клиника"


class CodeType(enum.Enum):
    qr_code = "qr"
    barcode = "barcode"
    digital = "digital"
