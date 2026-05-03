from tortoise import fields, Model

from enums import FileType, FileSource

class File(Model):
    # File properties
    uid = fields.UUIDField(primary_key=True)
    name = fields.CharField(max_length=1024, required=True)
    size = fields.IntField(required=True)
    file_type = fields.CharEnumField(FileType, null=True)

    # File data
    # The location of the file on the server or cloud storage
    location = fields.CharField(max_length=2048, null=True)
    source = fields.CharEnumField(FileSource, null=True)

    # File heirarchy and ownership
    user = fields.ForeignKeyField('models.Locker', related_name='files')
    parent = fields.ForeignKeyField('models.File', related_name='children', null=True)

    created_at = fields.DatetimeField(auto_now_add=True)
