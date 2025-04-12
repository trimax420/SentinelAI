"""add s3 storage support

Revision ID: add_s3_storage
Revises: initial_schema
Create Date: 2024-04-10 12:45:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_s3_storage'
down_revision = 'initial_schema'
branch_labels = None
depends_on = None

def upgrade():
    # Add S3 URL columns to alerts table
    op.add_column('alerts', sa.Column('s3_snapshot_url', sa.String(255), nullable=True))
    op.add_column('alerts', sa.Column('s3_video_url', sa.String(255), nullable=True))
    
    # Add S3 URL columns to detection_events table
    op.add_column('detection_events', sa.Column('s3_snapshot_url', sa.String(255), nullable=True))
    op.add_column('detection_events', sa.Column('s3_video_url', sa.String(255), nullable=True))
    
    # Add S3 URL columns to suspect_images table
    op.add_column('suspect_images', sa.Column('s3_image_url', sa.String(255), nullable=True))
    op.add_column('suspect_images', sa.Column('s3_thumbnail_url', sa.String(255), nullable=True))

def downgrade():
    # Remove S3 URL columns from alerts table
    op.drop_column('alerts', 's3_snapshot_url')
    op.drop_column('alerts', 's3_video_url')
    
    # Remove S3 URL columns from detection_events table
    op.drop_column('detection_events', 's3_snapshot_url')
    op.drop_column('detection_events', 's3_video_url')
    
    # Remove S3 URL columns from suspect_images table
    op.drop_column('suspect_images', 's3_image_url')
    op.drop_column('suspect_images', 's3_thumbnail_url') 