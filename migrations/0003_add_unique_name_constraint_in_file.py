from tortoise import migrations
from tortoise.migrations import operations as ops
from tortoise.migrations.constraints import UniqueConstraint

class Migration(migrations.Migration):
    dependencies = [('models', '0002_add_hidden_in_file_table')]

    initial = False

    operations = [
        ops.AddConstraint(
            model_name='File',
            constraint=UniqueConstraint(fields=('name', 'parent', 'user'), name=None),
        ),
    ]
