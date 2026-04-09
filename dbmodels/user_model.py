from tortoise import fields, Model

class UserTable(Model):
    uid = fields.UUIDField(primary_key=True)
    email = fields.CharField(max_length=510)
    phone = fields.CharField(max_length=13)
    pwd = fields.CharField(max_length=255)
