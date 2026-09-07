"""
Management command: add_missing_columns
Directly adds ALL columns that models expect but database tables are missing.
Safe to run multiple times — skips columns that already exist.

Usage:
    python manage.py add_missing_columns --settings=config.settings.local
"""
from django.core.management.base import BaseCommand
from django.db import connection


COLUMNS = [
    # revenue_goals
    ("revenue_goals",   "updated_at",               "DATETIME"),
    # ads (meta_integration)
    ("ads",             "updated_at",               "DATETIME"),
    ("ads",             "ad_format",                "VARCHAR(50) DEFAULT ''"),
    ("ads",             "spend",                    "DECIMAL(14,2) DEFAULT 0"),
    ("ads",             "revenue",                  "DECIMAL(14,2) DEFAULT 0"),
    ("ads",             "roi",                      "DECIMAL(10,2) DEFAULT 0"),
    ("ads",             "conversations",            "INTEGER DEFAULT 0"),
    # campaigns
    ("campaigns",       "updated_at",               "DATETIME"),
    ("campaigns",       "spend",                    "DECIMAL(14,2) DEFAULT 0"),
    ("campaigns",       "revenue",                  "DECIMAL(14,2) DEFAULT 0"),
    ("campaigns",       "roi",                      "DECIMAL(10,2) DEFAULT 0"),
    ("campaigns",       "aov",                      "DECIMAL(10,2) DEFAULT 0"),
    ("campaigns",       "conversations",            "INTEGER DEFAULT 0"),
    ("campaigns",       "sales_count",              "INTEGER DEFAULT 0"),
    # ad_accounts
    ("ad_accounts",     "updated_at",               "DATETIME"),
    ("ad_accounts",     "account_name",             "VARCHAR(200) DEFAULT ''"),
    ("ad_accounts",     "instagram_business_account_id", "VARCHAR(50) DEFAULT ''"),
    ("ad_accounts",     "instagram_username",       "VARCHAR(100) DEFAULT ''"),
    ("ad_accounts",     "last_synced",              "DATETIME"),
    ("ad_accounts",     "sync_enabled",             "BOOLEAN DEFAULT 1"),
    # sales — customer fields
    ("sales","customer_name",  "VARCHAR(200) DEFAULT ''"),
    ("sales","customer_phone", "VARCHAR(20) DEFAULT ''"),
    # ad_spend_records
    ("ad_spend_records","impressions",            "INTEGER DEFAULT 0"),
    ("ad_spend_records","clicks",                 "INTEGER DEFAULT 0"),
    ("ad_spend_records","dm_conversations",       "INTEGER DEFAULT 0"),
    ("ad_spend_records","is_partial",             "BOOLEAN DEFAULT 0"),
    ("ad_spend_records","updated_at",             "DATETIME"),
    # pipeline_deals
    ("pipeline_deals",  "updated_at",               "DATETIME"),
    ("pipeline_deals",  "last_contacted_at",        "DATETIME"),
    ("pipeline_deals",  "expected_close_date",      "DATE"),
    # sales
    ("sales",           "updated_at",               "DATETIME"),
    ("sales",           "is_confirmed",             "BOOLEAN DEFAULT 1"),
    ("sales",           "pipeline_deal_id",         "TEXT"),
    ("sales",           "bulk_upload_id",           "TEXT"),
    # metric_snapshots
    ("metric_snapshots","facebook_spend",           "DECIMAL(14,2) DEFAULT 0"),
    ("metric_snapshots","instagram_spend",          "DECIMAL(14,2) DEFAULT 0"),
    ("metric_snapshots","total_sales",              "INTEGER DEFAULT 0"),
    ("metric_snapshots","facebook_sales",           "INTEGER DEFAULT 0"),
    ("metric_snapshots","instagram_sales",          "INTEGER DEFAULT 0"),
    ("metric_snapshots","organic_sales",            "INTEGER DEFAULT 0"),
    ("metric_snapshots","total_impressions",        "INTEGER DEFAULT 0"),
    ("metric_snapshots","total_clicks",             "INTEGER DEFAULT 0"),
    ("metric_snapshots","pipeline_total_deals",     "INTEGER DEFAULT 0"),
    ("metric_snapshots","pipeline_won_deals",       "INTEGER DEFAULT 0"),
    ("metric_snapshots","pipeline_lost_deals",      "INTEGER DEFAULT 0"),
    ("metric_snapshots","pipeline_open_value",      "DECIMAL(14,2) DEFAULT 0"),
    ("metric_snapshots","avg_deal_velocity_hours",  "DECIMAL(10,2) DEFAULT 0"),
    ("metric_snapshots","facebook_roi",             "DECIMAL(10,2) DEFAULT 0"),
    ("metric_snapshots","instagram_roi",            "DECIMAL(10,2) DEFAULT 0"),
    ("metric_snapshots","facebook_cost_per_sale",   "DECIMAL(10,2) DEFAULT 0"),
    ("metric_snapshots","instagram_cost_per_sale",  "DECIMAL(10,2) DEFAULT 0"),
    ("metric_snapshots","revenue_per_client",       "DECIMAL(12,2) DEFAULT 0"),
    ("metric_snapshots","is_partial",               "BOOLEAN DEFAULT 0"),
    # mpesa
    ("mpesa_configs",   "account_reference",        "VARCHAR(50) DEFAULT ''"),
    ("mpesa_configs",   "updated_at",               "DATETIME"),
    ("mpesa_transactions","middle_name",            "VARCHAR(100) DEFAULT ''"),
    ("mpesa_transactions","business_shortcode",     "VARCHAR(20) DEFAULT ''"),
    ("mpesa_transactions","raw_callback",           "TEXT DEFAULT ''"),
    ("mpesa_transactions","matched_pipeline_deal_id","TEXT"),
    # recommendations
    ("recommendations", "message",                  "TEXT DEFAULT ''"),
    ("recommendations", "generated_at",             "DATETIME"),
    ("recommendations", "is_dismissed",             "BOOLEAN DEFAULT 0"),
    ("recommendations", "is_applied",               "BOOLEAN DEFAULT 0"),
    ("recommendations", "action",                   "TEXT DEFAULT ''"),
    ("recommendations", "suggested_budget_increase_amount", "DECIMAL(12,2)"),
    ("recommendations", "suggested_new_budget",    "DECIMAL(12,2)"),
    ("recommendations", "budget_cap_applied_percent","DECIMAL(5,2) DEFAULT 0"),
    ("recommendations", "dismissed_at",            "DATETIME"),
    ("recommendations", "applied_at",              "DATETIME"),
    ("recommendations", "expires_at",              "DATETIME"),
    # sms
    ("sms_messages",    "updated_at",               "DATETIME"),
    ("sms_messages",    "delivered_at",             "DATETIME"),
    # external_api
    ("external_api_keys","can_create_pipeline_deals","BOOLEAN DEFAULT 1"),
    ("external_api_keys","can_read_sales",          "BOOLEAN DEFAULT 0"),
    ("external_api_keys","notes",                   "TEXT DEFAULT ''"),
    # tenants
    ("tenants",         "onboarded_at",             "DATETIME"),
    ("tenants",         "notes",                    "TEXT DEFAULT ''"),
]


class Command(BaseCommand):
    help = 'Add all missing columns to existing database tables'

    def handle(self, *args, **options):
        added = 0
        skipped = 0

        with connection.cursor() as cursor:
            for table, column, col_type in COLUMNS:
                # Check if column already exists
                try:
                    cursor.execute(f"SELECT {column} FROM {table} LIMIT 1")
                    skipped += 1
                    self.stdout.write(f'  skip  {table}.{column} (exists)')
                except Exception:
                    # Column doesn't exist — add it
                    try:
                        cursor.execute(
                            f"ALTER TABLE {table} ADD COLUMN {column} {col_type}"
                        )
                        added += 1
                        self.stdout.write(
                            self.style.SUCCESS(f'  added {table}.{column}')
                        )
                    except Exception as e:
                        self.stdout.write(
                            self.style.WARNING(f'  ERROR {table}.{column}: {e}')
                        )

        # Fix NULL values in boolean/important columns on existing rows
        fixes = [
            "UPDATE sales SET is_confirmed=1 WHERE is_confirmed IS NULL",
            "UPDATE recommendations SET is_dismissed=0 WHERE is_dismissed IS NULL",
            "UPDATE recommendations SET is_applied=0 WHERE is_applied IS NULL",
        ]
        fixed_rows = 0
        for sql in fixes:
            try:
                with connection.cursor() as cur:
                    cur.execute(sql)
                    fixed_rows += cur.rowcount
            except Exception:
                pass

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(
            f'Done — {added} columns added, {skipped} already existed, {fixed_rows} rows updated.'
        ))
