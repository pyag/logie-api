from tortoise import fields, Model

class Locker(Model):
    uid = fields.UUIDField(primary_key=True)
    name = fields.CharField(max_length=255, unique=True, required=True)
    pwd = fields.CharField(max_length=255, required=True)
    email = fields.CharField(max_length=255, null=True)

    created_at = fields.DatetimeField(auto_now_add=True)
