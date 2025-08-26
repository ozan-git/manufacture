from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    openupgrade.logged_query(
        env.cr,
        "ALTER TABLE qc_inspection ADD COLUMN IF NOT EXISTS lot_name varchar",
    )
