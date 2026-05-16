from tortoise import migrations
from tortoise.migrations import operations as ops
from enums.file import FileSource, FileType
from tortoise.fields.base import OnDelete
from uuid import uuid4
from tortoise import fields

class Migration(migrations.Migration):
    initial = True

    operations = [
        ops.CreateModel(
            name='Locker',
            fields=[
                ('uid', fields.UUIDField(primary_key=True, default=uuid4, unique=True, db_index=True)),
                ('name', fields.CharField(unique=True, max_length=255)),
                ('pwd', fields.CharField(max_length=255)),
                ('email', fields.CharField(null=True, max_length=255)),
                ('created_at', fields.DatetimeField(auto_now=False, auto_now_add=True)),
            ],
            options={'table': 'locker', 'app': 'models', 'pk_attr': 'uid'},
            bases=['Model'],
        ),
        ops.CreateModel(
            name='File',
            fields=[
                ('uid', fields.UUIDField(primary_key=True, default=uuid4, unique=True, db_index=True)),
                ('name', fields.CharField(max_length=1024)),
                ('size', fields.IntField()),
                ('file_type', fields.CharEnumField(null=True, description='FOLDER: folder\nVIDEO: video\nIMAGE: image\nPDF: pdf\nBINARY: binary', enum_type=FileType, max_length=6)),
                ('location', fields.CharField(null=True, max_length=2048)),
                ('source', fields.CharEnumField(null=True, description='LOCAL: LOCAL', enum_type=FileSource, max_length=5)),
                ('user', fields.ForeignKeyField('models.Locker', source_field='user_id', db_constraint=True, to_field='uid', related_name='files', on_delete=OnDelete.CASCADE)),
                ('parent', fields.ForeignKeyField('models.File', source_field='parent_id', null=True, db_constraint=True, to_field='uid', related_name='children', on_delete=OnDelete.CASCADE)),
                ('created_at', fields.DatetimeField(auto_now=False, auto_now_add=True)),
            ],
            options={'table': 'file', 'app': 'models', 'pk_attr': 'uid'},
            bases=['Model'],
        ),
    ]
