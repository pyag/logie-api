from tortoise import migrations
from tortoise.migrations import operations as ops
from tortoise import fields

class Migration(migrations.Migration):
    dependencies = [('models', '0001_initial')]

    initial = False

    operations = [
        # 1. Add the column allowing NULL values temporarily so Postgres allows it
        ops.RunSQL('ALTER TABLE "file" ADD COLUMN "hidden" BOOLEAN NULL;'),
        
        # 2. Backfill all pre-existing records with your default value (false)
        ops.RunSQL('UPDATE "file" SET "hidden" = false WHERE "hidden" IS NULL;'),
        
        # 3. Alter the column to strict NOT NULL now that no NULL values exist
        ops.RunSQL('ALTER TABLE "file" ALTER COLUMN "hidden" SET NOT NULL;'),
        
        # 4. (Optional but recommended) Apply the server-level default for future DB entries
        ops.RunSQL('ALTER TABLE "file" ALTER COLUMN "hidden" SET DEFAULT false;'),
    ]
