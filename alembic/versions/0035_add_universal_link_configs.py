"""Add universal_link_configs table for Universal Links and App Links management

Revision ID: 0035_add_universal_link_configs
Revises: 0034_expand_news_article_fields
Create Date: 2026-10-16 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0035_add_universal_link_configs"
down_revision = "0034_expand_news_article_fields"
branch_labels = None
depends_on = None


def upgrade() -> None:
    table = op.create_table(
        "universal_link_configs",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("key", sa.String(length=50), nullable=False, unique=True, server_default="default"),
        sa.Column("apple_team_id", sa.String(length=50), nullable=False, server_default="3VMD59LYS6"),
        sa.Column("apple_bundle_id", sa.String(length=100), nullable=False, server_default="com.kh.mytravel.app"),
        sa.Column("apple_paths", sa.JSON(), nullable=False),
        sa.Column("webcredentials_enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("android_package_name", sa.String(length=100), nullable=False, server_default="com.kh.mytravel.mytravel"),
        sa.Column("android_sha256_fingerprints", sa.JSON(), nullable=False),
        sa.Column("primary_domain", sa.String(length=100), nullable=False, server_default="mytravel.taxi"),
        sa.Column("custom_scheme", sa.String(length=50), nullable=False, server_default="mytravel://"),
        sa.Column("fallback_url", sa.String(length=255), nullable=False, server_default="https://mytravel.taxi/"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_universal_link_configs_key", "universal_link_configs", ["key"])

    # Seed default record
    op.bulk_insert(
        table,
        [
            {
                "key": "default",
                "apple_team_id": "3VMD59LYS6",
                "apple_bundle_id": "com.kh.mytravel.app",
                "apple_paths": ["/trips/*", "/t/*", "/news/*", "/ads/*", "/promotions/*", "/travel/*"],
                "webcredentials_enabled": True,
                "android_package_name": "com.kh.mytravel.mytravel",
                "android_sha256_fingerprints": [
                    {
                        "fingerprint": "4B:33:E5:28:B3:A4:59:1A:D1:77:90:CD:9F:49:CB:47:EF:A9:9F:EF:D9:58:75:B7:29:3D:FE:87:E1:FE:47:73",
                        "label": "Google Play App Signing (Production)",
                        "type": "production",
                    },
                    {
                        "fingerprint": "0C:B8:64:C9:26:44:67:E9:21:9F:A5:F4:D2:0B:66:40:2F:1C:F2:B1:FA:05:2F:BF:42:6F:EF:40:6F:9D:ED:47",
                        "label": "Release Keystore (Keystone.jks)",
                        "type": "release",
                    },
                    {
                        "fingerprint": "ED:F9:37:D3:54:59:0B:A8:73:D3:8E:DD:AE:E3:7E:1A:D6:C8:33:CD:25:74:18:08:70:77:F3:EA:B9:37:DC:F8",
                        "label": "Local Debug Keystore",
                        "type": "debug",
                    },
                ],
                "primary_domain": "mytravel.taxi",
                "custom_scheme": "mytravel://",
                "fallback_url": "https://mytravel.taxi/",
                "is_active": True,
            }
        ],
    )


def downgrade() -> None:
    op.drop_index("ix_universal_link_configs_key", table_name="universal_link_configs")
    op.drop_table("universal_link_configs")
