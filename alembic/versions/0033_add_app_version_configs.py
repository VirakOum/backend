"""Add app_version_configs table for app version control

Revision ID: 0033_add_app_version_configs
Revises: 0032_expand_user_notification_system_types
Create Date: 2026-09-21 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "0033_add_app_version_configs"
down_revision = "0032_expand_user_notification_system_types"
branch_labels = None
depends_on = None


def upgrade() -> None:
    table = op.create_table(
        "app_version_configs",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("platform", sa.String(length=20), nullable=False, unique=True),
        sa.Column("latest_version", sa.String(length=30), nullable=False, server_default="1.0.0"),
        sa.Column("min_version", sa.String(length=30), nullable=False, server_default="1.0.0"),
        sa.Column("force_update", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("update_url", sa.String(length=500), nullable=False, server_default=""),
        sa.Column("title", sa.String(length=200), nullable=False, server_default="New Version Available"),
        sa.Column("title_km", sa.String(length=200), nullable=False, server_default="មានកំណែថ្មីនៃកម្មវិធី"),
        sa.Column("release_notes", sa.Text(), nullable=False, server_default=""),
        sa.Column("release_notes_km", sa.Text(), nullable=False, server_default=""),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("platform IN ('android', 'ios', 'all')", name="app_version_platform_check"),
    )
    op.create_index("ix_app_version_configs_platform", "app_version_configs", ["platform"])

    # Seed default configs for Android and iOS
    op.bulk_insert(
        table,
        [
            {
                "platform": "android",
                "latest_version": "1.0.0",
                "min_version": "1.0.0",
                "force_update": False,
                "update_url": "https://play.google.com/store/apps/details?id=com.mytravel.app",
                "title": "New Version Available",
                "title_km": "មានកំណែថ្មីនៃកម្មវិធី",
                "release_notes": "• Performance enhancements\n• Bug fixes and stability improvements",
                "release_notes_km": "• បង្កើនល្បឿន និងស្ថេរភាពនៃកម្មវិធី\n• កែសម្រួលចំណុចខ្វះខាតនានា",
                "is_active": True,
            },
            {
                "platform": "ios",
                "latest_version": "1.0.0",
                "min_version": "1.0.0",
                "force_update": False,
                "update_url": "https://apps.apple.com/app/mytravel/id000000000",
                "title": "New Version Available",
                "title_km": "មានកំណែថ្មីនៃកម្មវិធី",
                "release_notes": "• Performance enhancements\n• Bug fixes and stability improvements",
                "release_notes_km": "• បង្កើនល្បឿន និងស្ថេរភាពនៃកម្មវិធី\n• កែសម្រួលចំណុចខ្វះខាតនានា",
                "is_active": True,
            },
        ],
    )


def downgrade() -> None:
    op.drop_index("ix_app_version_configs_platform", table_name="app_version_configs")
    op.drop_table("app_version_configs")
