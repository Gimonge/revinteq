"""
Revinteq v3 — Emergency Table Creator
Creates all custom app tables directly via SQL.
Use when migrations are not being detected.

Usage:
    python manage.py create_tables --settings=config.settings.local
"""
from django.core.management.base import BaseCommand
from django.db import connection


TABLES = [
    # tenants
    """CREATE TABLE IF NOT EXISTS tenants (
        id TEXT PRIMARY KEY,
        name VARCHAR(200) NOT NULL,
        slug VARCHAR(100) UNIQUE NOT NULL,
        status VARCHAR(20) DEFAULT 'trial',
        contact_name VARCHAR(200) DEFAULT '',
        contact_email VARCHAR(254) DEFAULT '',
        contact_phone VARCHAR(20) DEFAULT '',
        industry VARCHAR(100) DEFAULT '',
        location VARCHAR(200) DEFAULT '',
        currency VARCHAR(10) DEFAULT 'KES',
        whatsapp_number VARCHAR(20) DEFAULT '',
        whatsapp_default_message TEXT DEFAULT '',
        meta_fb_connected BOOLEAN DEFAULT 0,
        meta_ig_connected BOOLEAN DEFAULT 0,
        meta_fb_access_token TEXT DEFAULT '',
        meta_fb_token_expires_at DATETIME,
        budget_increase_cap_percent INTEGER DEFAULT 20,
        onboarding_complete BOOLEAN DEFAULT 0,
        created_at DATETIME NOT NULL,
        updated_at DATETIME NOT NULL,
        created_by_id INTEGER REFERENCES auth_user(id) ON DELETE SET NULL
    )""",

    """CREATE TABLE IF NOT EXISTS tenant_users (
        id TEXT PRIMARY KEY,
        role VARCHAR(20) DEFAULT 'CLIENT',
        is_active BOOLEAN DEFAULT 1,
        joined_at DATETIME NOT NULL,
        user_id INTEGER NOT NULL REFERENCES auth_user(id) ON DELETE CASCADE,
        tenant_id TEXT NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
        invited_by_id INTEGER REFERENCES auth_user(id) ON DELETE SET NULL
    )""",

    """CREATE TABLE IF NOT EXISTS tenant_invitations (
        id TEXT PRIMARY KEY,
        email VARCHAR(254) NOT NULL,
        role VARCHAR(20) DEFAULT 'CLIENT',
        token VARCHAR(100) UNIQUE NOT NULL,
        status VARCHAR(20) DEFAULT 'pending',
        expires_at DATETIME NOT NULL,
        created_at DATETIME NOT NULL,
        accepted_at DATETIME,
        tenant_id TEXT NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
        invited_by_id INTEGER REFERENCES auth_user(id) ON DELETE SET NULL
    )""",

    # accounts
    """CREATE TABLE IF NOT EXISTS user_profiles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        full_name VARCHAR(200) DEFAULT '',
        phone_number VARCHAR(20) DEFAULT '',
        timezone VARCHAR(50) DEFAULT 'Africa/Nairobi',
        onboarding_complete BOOLEAN DEFAULT 0,
        created_at DATETIME NOT NULL,
        updated_at DATETIME NOT NULL,
        user_id INTEGER UNIQUE NOT NULL REFERENCES auth_user(id) ON DELETE CASCADE
    )""",

    # meta_integration
    """CREATE TABLE IF NOT EXISTS ad_accounts (
        id TEXT PRIMARY KEY,
        meta_account_id VARCHAR(50) NOT NULL,
        name VARCHAR(200) NOT NULL,
        platform VARCHAR(20) DEFAULT 'facebook',
        currency VARCHAR(10) DEFAULT 'KES',
        access_token TEXT DEFAULT '',
        token_expires_at DATETIME,
        is_active BOOLEAN DEFAULT 1,
        last_synced_at DATETIME,
        created_at DATETIME NOT NULL,
        tenant_id TEXT NOT NULL REFERENCES tenants(id) ON DELETE CASCADE
    )""",

    """CREATE TABLE IF NOT EXISTS campaigns (
        id TEXT PRIMARY KEY,
        meta_campaign_id VARCHAR(50) NOT NULL,
        name VARCHAR(300) NOT NULL,
        status VARCHAR(20) DEFAULT 'ACTIVE',
        objective VARCHAR(50) DEFAULT '',
        daily_budget DECIMAL(12,2),
        lifetime_budget DECIMAL(12,2),
        platform VARCHAR(20) DEFAULT 'facebook',
        created_at DATETIME NOT NULL,
        updated_at DATETIME NOT NULL,
        ad_account_id TEXT NOT NULL REFERENCES ad_accounts(id) ON DELETE CASCADE
    )""",

    """CREATE TABLE IF NOT EXISTS ads (
        id TEXT PRIMARY KEY,
        meta_ad_id VARCHAR(50) NOT NULL,
        name VARCHAR(300) NOT NULL,
        status VARCHAR(20) DEFAULT 'ACTIVE',
        format VARCHAR(50) DEFAULT '',
        created_at DATETIME NOT NULL,
        campaign_id TEXT NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE
    )""",

    """CREATE TABLE IF NOT EXISTS ad_spend_records (
        id TEXT PRIMARY KEY,
        date DATE NOT NULL,
        spend DECIMAL(12,2) DEFAULT 0,
        views INTEGER DEFAULT 0,
        clicks INTEGER DEFAULT 0,
        conversations_started INTEGER DEFAULT 0,
        messaging_first_reply INTEGER DEFAULT 0,
        messaging_new_connections INTEGER DEFAULT 0,
        messaging_blocked INTEGER DEFAULT 0,
        created_at DATETIME NOT NULL,
        ad_id TEXT NOT NULL REFERENCES ads(id) ON DELETE CASCADE
    )""",

    # customers
    """CREATE TABLE IF NOT EXISTS customers (
        id TEXT PRIMARY KEY,
        name VARCHAR(200) DEFAULT '',
        phone_number VARCHAR(30) DEFAULT '',
        email VARCHAR(254) DEFAULT '',
        instagram_handle VARCHAR(100) DEFAULT '',
        facebook_profile_name VARCHAR(200) DEFAULT '',
        messenger_user_id VARCHAR(100) DEFAULT '',
        source_platform VARCHAR(20) DEFAULT 'facebook',
        first_seen_date DATE NOT NULL,
        last_contact_date DATE,
        total_purchases INTEGER DEFAULT 0,
        total_spend DECIMAL(14,2) DEFAULT 0,
        preferred_payment_method VARCHAR(30) DEFAULT '',
        sms_opt_in BOOLEAN DEFAULT 1,
        email_opt_in BOOLEAN DEFAULT 0,
        tags VARCHAR(500) DEFAULT '',
        notes TEXT DEFAULT '',
        created_at DATETIME NOT NULL,
        updated_at DATETIME NOT NULL,
        tenant_id TEXT NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
        first_ad_id TEXT REFERENCES ads(id) ON DELETE SET NULL
    )""",

    # pipeline
    """CREATE TABLE IF NOT EXISTS pipeline_deals (
        id TEXT PRIMARY KEY,
        platform VARCHAR(20) DEFAULT 'facebook',
        source VARCHAR(30) DEFAULT 'manual',
        whatsapp_message_id VARCHAR(100) DEFAULT '',
        messenger_thread_id VARCHAR(100) DEFAULT '',
        instagram_thread_id VARCHAR(100) DEFAULT '',
        mpesa_reference VARCHAR(20) UNIQUE DEFAULT '',
        customer_name VARCHAR(200) DEFAULT '',
        customer_phone VARCHAR(20) DEFAULT '',
        stage VARCHAR(20) DEFAULT 'new_click',
        estimated_value DECIMAL(12,2),
        velocity VARCHAR(10) DEFAULT 'cold',
        notes TEXT DEFAULT '',
        days_in_current_stage INTEGER DEFAULT 0,
        new_click_at DATETIME,
        contacted_at DATETIME,
        interested_at DATETIME,
        negotiating_at DATETIME,
        won_at DATETIME,
        lost_at DATETIME,
        lost_reason VARCHAR(200) DEFAULT '',
        created_at DATETIME NOT NULL,
        updated_at DATETIME NOT NULL,
        tenant_id TEXT NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
        ad_id TEXT REFERENCES ads(id) ON DELETE SET NULL,
        campaign_id TEXT REFERENCES campaigns(id) ON DELETE SET NULL,
        customer_id TEXT REFERENCES customers(id) ON DELETE SET NULL
    )""",

    """CREATE TABLE IF NOT EXISTS stage_transition_logs (
        id TEXT PRIMARY KEY,
        from_stage VARCHAR(20) NOT NULL,
        to_stage VARCHAR(20) NOT NULL,
        notes TEXT DEFAULT '',
        source VARCHAR(30) DEFAULT '',
        transitioned_at DATETIME NOT NULL,
        deal_id TEXT NOT NULL REFERENCES pipeline_deals(id) ON DELETE CASCADE,
        transitioned_by_id INTEGER REFERENCES auth_user(id) ON DELETE SET NULL
    )""",

    # sales
    """CREATE TABLE IF NOT EXISTS sales (
        id TEXT PRIMARY KEY,
        product_name VARCHAR(300) NOT NULL,
        amount DECIMAL(14,2) NOT NULL,
        payment_method VARCHAR(30) DEFAULT 'cash',
        payment_reference VARCHAR(100) DEFAULT '',
        platform_source VARCHAR(20) DEFAULT 'facebook',
        sale_date DATE NOT NULL,
        notes TEXT DEFAULT '',
        is_confirmed BOOLEAN DEFAULT 1,
        created_at DATETIME NOT NULL,
        updated_at DATETIME NOT NULL,
        tenant_id TEXT NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
        ad_id TEXT REFERENCES ads(id) ON DELETE SET NULL,
        campaign_id TEXT REFERENCES campaigns(id) ON DELETE SET NULL,
        pipeline_deal_id TEXT REFERENCES pipeline_deals(id) ON DELETE SET NULL,
        bulk_upload_id TEXT REFERENCES bulk_sales_uploads(id) ON DELETE SET NULL,
        created_by_id INTEGER REFERENCES auth_user(id) ON DELETE SET NULL
    )""",

    # bulk_upload
    """CREATE TABLE IF NOT EXISTS bulk_sales_uploads (
        id TEXT PRIMARY KEY,
        original_filename VARCHAR(255) NOT NULL,
        file VARCHAR(255) DEFAULT '',
        status VARCHAR(20) DEFAULT 'pending',
        total_rows INTEGER DEFAULT 0,
        valid_rows INTEGER DEFAULT 0,
        error_rows INTEGER DEFAULT 0,
        saved_rows INTEGER DEFAULT 0,
        preview_data TEXT DEFAULT '[]',
        error_summary TEXT DEFAULT '[]',
        created_at DATETIME NOT NULL,
        completed_at DATETIME,
        tenant_id TEXT NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
        uploaded_by_id INTEGER REFERENCES auth_user(id) ON DELETE SET NULL
    )""",

    # metrics
    """CREATE TABLE IF NOT EXISTS metric_snapshots (
        id TEXT PRIMARY KEY,
        period_type VARCHAR(10) DEFAULT 'month',
        period_start DATE NOT NULL,
        period_end DATE NOT NULL,
        total_revenue DECIMAL(14,2) DEFAULT 0,
        facebook_revenue DECIMAL(14,2) DEFAULT 0,
        instagram_revenue DECIMAL(14,2) DEFAULT 0,
        total_spend DECIMAL(14,2) DEFAULT 0,
        roi DECIMAL(10,2) DEFAULT 0,
        avg_order_value DECIMAL(12,2) DEFAULT 0,
        facebook_aov DECIMAL(12,2) DEFAULT 0,
        instagram_aov DECIMAL(12,2) DEFAULT 0,
        total_sales_count INTEGER DEFAULT 0,
        total_conversations INTEGER DEFAULT 0,
        facebook_conversations INTEGER DEFAULT 0,
        instagram_conversations INTEGER DEFAULT 0,
        whatsapp_conversations INTEGER DEFAULT 0,
        conversion_rate DECIMAL(6,2) DEFAULT 0,
        cost_per_conversation DECIMAL(10,2) DEFAULT 0,
        cost_per_sale DECIMAL(10,2) DEFAULT 0,
        revenue_goal DECIMAL(14,2),
        goal_progress_percent DECIMAL(6,2) DEFAULT 0,
        goal_status VARCHAR(20) DEFAULT '',
        revenue_gap DECIMAL(14,2) DEFAULT 0,
        required_daily_revenue DECIMAL(12,2) DEFAULT 0,
        computed_at DATETIME NOT NULL,
        tenant_id TEXT NOT NULL REFERENCES tenants(id) ON DELETE CASCADE
    )""",

    # revenue_goals
    """CREATE TABLE IF NOT EXISTS revenue_goals (
        id TEXT PRIMARY KEY,
        month DATE NOT NULL,
        target_amount DECIMAL(14,2) NOT NULL,
        primary_channel VARCHAR(30) DEFAULT 'whatsapp',
        notes TEXT DEFAULT '',
        created_at DATETIME NOT NULL,
        tenant_id TEXT NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
        created_by_id INTEGER REFERENCES auth_user(id) ON DELETE SET NULL
    )""",

    # recommendations
    """CREATE TABLE IF NOT EXISTS recommendations (
        id TEXT PRIMARY KEY,
        rule_id VARCHAR(10) NOT NULL,
        title VARCHAR(300) NOT NULL,
        body TEXT NOT NULL,
        priority VARCHAR(10) DEFAULT 'MEDIUM',
        platform VARCHAR(20) DEFAULT '',
        is_dismissed BOOLEAN DEFAULT 0,
        is_applied BOOLEAN DEFAULT 0,
        generated_at DATETIME NOT NULL,
        tenant_id TEXT NOT NULL REFERENCES tenants(id) ON DELETE CASCADE
    )""",

    # mpesa
    """CREATE TABLE IF NOT EXISTS mpesa_configs (
        id TEXT PRIMARY KEY,
        shortcode VARCHAR(20) NOT NULL,
        shortcode_type VARCHAR(10) DEFAULT 'till',
        consumer_key VARCHAR(200) DEFAULT '',
        consumer_secret VARCHAR(200) DEFAULT '',
        passkey VARCHAR(200) DEFAULT '',
        environment VARCHAR(15) DEFAULT 'sandbox',
        is_active BOOLEAN DEFAULT 1,
        created_at DATETIME NOT NULL,
        tenant_id TEXT UNIQUE NOT NULL REFERENCES tenants(id) ON DELETE CASCADE
    )""",

    """CREATE TABLE IF NOT EXISTS mpesa_transactions (
        id TEXT PRIMARY KEY,
        transaction_id VARCHAR(50) UNIQUE NOT NULL,
        transaction_type VARCHAR(30) DEFAULT '',
        amount DECIMAL(12,2) NOT NULL,
        msisdn VARCHAR(20) DEFAULT '',
        first_name VARCHAR(100) DEFAULT '',
        last_name VARCHAR(100) DEFAULT '',
        bill_ref_number VARCHAR(50) DEFAULT '',
        business_short_code VARCHAR(20) DEFAULT '',
        transaction_time DATETIME NOT NULL,
        status VARCHAR(20) DEFAULT 'pending',
        match_confidence VARCHAR(30) DEFAULT '',
        received_at DATETIME NOT NULL,
        matched_at DATETIME,
        tenant_id TEXT NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
        matched_deal_id TEXT REFERENCES pipeline_deals(id) ON DELETE SET NULL,
        matched_sale_id TEXT REFERENCES sales(id) ON DELETE SET NULL
    )""",

    # sms
    """CREATE TABLE IF NOT EXISTS sms_configs (
        id TEXT PRIMARY KEY,
        username VARCHAR(100) NOT NULL,
        api_key VARCHAR(200) DEFAULT '',
        sender_id VARCHAR(20) DEFAULT '',
        is_active BOOLEAN DEFAULT 1,
        credit_balance DECIMAL(10,4) DEFAULT 0,
        created_at DATETIME NOT NULL,
        tenant_id TEXT UNIQUE NOT NULL REFERENCES tenants(id) ON DELETE CASCADE
    )""",

    """CREATE TABLE IF NOT EXISTS sms_messages (
        id TEXT PRIMARY KEY,
        recipient_number VARCHAR(20) NOT NULL,
        recipient_name VARCHAR(200) DEFAULT '',
        message TEXT NOT NULL,
        source VARCHAR(20) DEFAULT 'manual',
        trigger VARCHAR(50) DEFAULT '',
        status VARCHAR(20) DEFAULT 'queued',
        at_message_id VARCHAR(100) DEFAULT '',
        at_status_code VARCHAR(10) DEFAULT '',
        cost REAL DEFAULT 0.0,
        sent_at DATETIME,
        created_at DATETIME NOT NULL,
        tenant_id TEXT NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
        sent_by_id INTEGER REFERENCES auth_user(id) ON DELETE SET NULL
    )""",

    """CREATE TABLE IF NOT EXISTS sms_triggers (
        id TEXT PRIMARY KEY,
        trigger VARCHAR(50) NOT NULL,
        message_template TEXT NOT NULL,
        is_active BOOLEAN DEFAULT 1,
        created_at DATETIME NOT NULL,
        tenant_id TEXT NOT NULL REFERENCES tenants(id) ON DELETE CASCADE
    )""",

    # external_api
    """CREATE TABLE IF NOT EXISTS external_api_keys (
        id TEXT PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        key VARCHAR(100) UNIQUE NOT NULL,
        is_active BOOLEAN DEFAULT 1,
        can_create_sales BOOLEAN DEFAULT 1,
        can_read_metrics BOOLEAN DEFAULT 0,
        last_used_at DATETIME,
        created_at DATETIME NOT NULL,
        tenant_id TEXT NOT NULL REFERENCES tenants(id) ON DELETE CASCADE
    )""",

    """CREATE TABLE IF NOT EXISTS webhook_endpoints (
        id TEXT PRIMARY KEY,
        url VARCHAR(200) NOT NULL,
        secret VARCHAR(100) DEFAULT '',
        is_active BOOLEAN DEFAULT 1,
        events TEXT DEFAULT '[]',
        created_at DATETIME NOT NULL,
        tenant_id TEXT NOT NULL REFERENCES tenants(id) ON DELETE CASCADE
    )""",

    """CREATE TABLE IF NOT EXISTS webhook_deliveries (
        id TEXT PRIMARY KEY,
        event VARCHAR(50) NOT NULL,
        payload TEXT DEFAULT '{}',
        status VARCHAR(20) DEFAULT 'pending',
        response_status_code INTEGER,
        response_body TEXT DEFAULT '',
        attempt_count INTEGER DEFAULT 0,
        delivered_at DATETIME,
        created_at DATETIME NOT NULL,
        endpoint_id TEXT NOT NULL REFERENCES webhook_endpoints(id) ON DELETE CASCADE
    )""",
]


class Command(BaseCommand):
    help = 'Create all Revinteq database tables directly via SQL (bypasses migration system)'

    def handle(self, *args, **options):
        self.stdout.write('Creating Revinteq tables...\n')
        created = 0
        with connection.cursor() as cursor:
            for sql in TABLES:
                table_name = sql.strip().split('IF NOT EXISTS ')[1].split(' ')[0].strip('(')
                try:
                    cursor.execute(sql)
                    self.stdout.write(self.style.SUCCESS(f'  ✓ {table_name}'))
                    created += 1
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'  ✗ {table_name}: {e}'))

        # Add missing columns to existing tables
        alter_ok = 0
        for sql in ALTER_COLUMNS:
            try:
                cursor.execute(sql)
                alter_ok += 1
            except Exception:
                pass  # Column may already exist — that's fine

        self.stdout.write(f'\n{created}/{len(TABLES)} tables ready.')
        self.stdout.write(f'{alter_ok} column additions applied.')
        self.stdout.write(self.style.SUCCESS(
            '\nDone. Now run: python manage.py createsuperuser --settings=config.settings.local'
        ))


# Additional ALTER TABLE commands to add columns missing from initial migrations
ALTER_COLUMNS = [
    # tenants
    "ALTER TABLE tenants ADD COLUMN IF NOT EXISTS onboarded_at DATETIME",
    "ALTER TABLE tenants ADD COLUMN IF NOT EXISTS notes TEXT DEFAULT ''",
    # meta_integration
    "ALTER TABLE ad_accounts ADD COLUMN IF NOT EXISTS account_name VARCHAR(200) DEFAULT ''",
    "ALTER TABLE ad_accounts ADD COLUMN IF NOT EXISTS instagram_business_account_id VARCHAR(50) DEFAULT ''",
    "ALTER TABLE ad_accounts ADD COLUMN IF NOT EXISTS instagram_username VARCHAR(100) DEFAULT ''",
    "ALTER TABLE ad_accounts ADD COLUMN IF NOT EXISTS last_synced DATETIME",
    "ALTER TABLE ad_accounts ADD COLUMN IF NOT EXISTS sync_enabled BOOLEAN DEFAULT 1",
    "ALTER TABLE ads ADD COLUMN IF NOT EXISTS impressions INTEGER DEFAULT 0",
    "ALTER TABLE ads ADD COLUMN IF NOT EXISTS dm_conversations INTEGER DEFAULT 0",
    # sales
    "ALTER TABLE sales ADD COLUMN IF NOT EXISTS pipeline_deal_id TEXT REFERENCES pipeline_deals(id) ON DELETE SET NULL",
    "ALTER TABLE sales ADD COLUMN IF NOT EXISTS bulk_upload_id TEXT REFERENCES bulk_sales_uploads(id) ON DELETE SET NULL",
    # metrics
    "ALTER TABLE metric_snapshots ADD COLUMN IF NOT EXISTS facebook_spend DECIMAL(14,2) DEFAULT 0",
    "ALTER TABLE metric_snapshots ADD COLUMN IF NOT EXISTS instagram_spend DECIMAL(14,2) DEFAULT 0",
    "ALTER TABLE metric_snapshots ADD COLUMN IF NOT EXISTS is_partial BOOLEAN DEFAULT 0",
    "ALTER TABLE metric_snapshots ADD COLUMN IF NOT EXISTS total_sales INTEGER DEFAULT 0",
    "ALTER TABLE metric_snapshots ADD COLUMN IF NOT EXISTS facebook_sales INTEGER DEFAULT 0",
    "ALTER TABLE metric_snapshots ADD COLUMN IF NOT EXISTS instagram_sales INTEGER DEFAULT 0",
    "ALTER TABLE metric_snapshots ADD COLUMN IF NOT EXISTS organic_sales INTEGER DEFAULT 0",
    "ALTER TABLE metric_snapshots ADD COLUMN IF NOT EXISTS total_impressions INTEGER DEFAULT 0",
    "ALTER TABLE metric_snapshots ADD COLUMN IF NOT EXISTS total_clicks INTEGER DEFAULT 0",
    "ALTER TABLE metric_snapshots ADD COLUMN IF NOT EXISTS pipeline_total_deals INTEGER DEFAULT 0",
    "ALTER TABLE metric_snapshots ADD COLUMN IF NOT EXISTS pipeline_won_deals INTEGER DEFAULT 0",
    "ALTER TABLE metric_snapshots ADD COLUMN IF NOT EXISTS pipeline_lost_deals INTEGER DEFAULT 0",
    "ALTER TABLE metric_snapshots ADD COLUMN IF NOT EXISTS pipeline_open_value DECIMAL(14,2) DEFAULT 0",
    "ALTER TABLE metric_snapshots ADD COLUMN IF NOT EXISTS avg_deal_velocity_hours DECIMAL(10,2) DEFAULT 0",
    "ALTER TABLE metric_snapshots ADD COLUMN IF NOT EXISTS facebook_roi DECIMAL(10,2) DEFAULT 0",
    "ALTER TABLE metric_snapshots ADD COLUMN IF NOT EXISTS instagram_roi DECIMAL(10,2) DEFAULT 0",
    "ALTER TABLE metric_snapshots ADD COLUMN IF NOT EXISTS facebook_cost_per_sale DECIMAL(10,2) DEFAULT 0",
    "ALTER TABLE metric_snapshots ADD COLUMN IF NOT EXISTS instagram_cost_per_sale DECIMAL(10,2) DEFAULT 0",
    "ALTER TABLE metric_snapshots ADD COLUMN IF NOT EXISTS revenue_per_client DECIMAL(12,2) DEFAULT 0",
    # revenue_goals
    "ALTER TABLE revenue_goals ADD COLUMN IF NOT EXISTS updated_at DATETIME",
    # recommendations
    "ALTER TABLE recommendations ADD COLUMN IF NOT EXISTS message TEXT DEFAULT ''",
    "ALTER TABLE recommendations ADD COLUMN IF NOT EXISTS action TEXT DEFAULT ''",
    "ALTER TABLE recommendations ADD COLUMN IF NOT EXISTS suggested_budget_increase_amount DECIMAL(12,2)",
    "ALTER TABLE recommendations ADD COLUMN IF NOT EXISTS suggested_new_budget DECIMAL(12,2)",
    "ALTER TABLE recommendations ADD COLUMN IF NOT EXISTS dismissed_at DATETIME",
    "ALTER TABLE recommendations ADD COLUMN IF NOT EXISTS applied_at DATETIME",
    "ALTER TABLE recommendations ADD COLUMN IF NOT EXISTS expires_at DATETIME",
    # mpesa
    "ALTER TABLE mpesa_configs ADD COLUMN IF NOT EXISTS account_reference VARCHAR(50) DEFAULT ''",
    "ALTER TABLE mpesa_configs ADD COLUMN IF NOT EXISTS updated_at DATETIME",
    "ALTER TABLE mpesa_transactions ADD COLUMN IF NOT EXISTS middle_name VARCHAR(100) DEFAULT ''",
    "ALTER TABLE mpesa_transactions ADD COLUMN IF NOT EXISTS business_shortcode VARCHAR(20) DEFAULT ''",
    "ALTER TABLE mpesa_transactions ADD COLUMN IF NOT EXISTS raw_callback TEXT DEFAULT ''",
    # sms
    "ALTER TABLE sms_messages ADD COLUMN IF NOT EXISTS updated_at DATETIME",
    # external_api
    "ALTER TABLE external_api_keys ADD COLUMN IF NOT EXISTS can_create_pipeline_deals BOOLEAN DEFAULT 1",
    "ALTER TABLE external_api_keys ADD COLUMN IF NOT EXISTS can_read_sales BOOLEAN DEFAULT 0",
    "ALTER TABLE external_api_keys ADD COLUMN IF NOT EXISTS notes TEXT DEFAULT ''",
]
