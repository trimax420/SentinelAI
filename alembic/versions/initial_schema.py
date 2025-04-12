"""initial schema

Revision ID: initial_schema
Revises: 
Create Date: 2024-04-10 12:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'initial_schema'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Create cameras table
    op.create_table(
        'cameras',
        sa.Column('camera_id', sa.String(50), primary_key=True),
        sa.Column('name', sa.String, nullable=True),
        sa.Column('source', sa.String, nullable=True),
        sa.Column('rtsp_url', sa.String, nullable=True),
        sa.Column('zones', postgresql.JSON, server_default='{}'),
        sa.Column('is_active', sa.Boolean, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('last_active', sa.DateTime(timezone=True), nullable=True)
    )

    # Create suspects table
    op.create_table(
        'suspects',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('aliases', postgresql.ARRAY(sa.String), nullable=True),
        sa.Column('physical_description', sa.Text, nullable=True),
        sa.Column('biometric_markers', postgresql.JSON, nullable=True),
        sa.Column('priority_level', sa.Integer, server_default='1'),
        sa.Column('is_active', sa.Boolean, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now())
    )

    # Create cases table
    op.create_table(
        'cases',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('case_number', sa.String(50), unique=True),
        sa.Column('title', sa.String(200), nullable=True),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('status', sa.String(50), nullable=True),
        sa.Column('priority', sa.Integer, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now())
    )

    # Create suspect_case_association table
    op.create_table(
        'suspect_case_association',
        sa.Column('suspect_id', sa.Integer, sa.ForeignKey('suspects.id', ondelete="CASCADE")),
        sa.Column('case_id', sa.Integer, sa.ForeignKey('cases.id', ondelete="CASCADE"))
    )

    # Create suspect_images table
    op.create_table(
        'suspect_images',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('suspect_id', sa.Integer, sa.ForeignKey('suspects.id', ondelete="CASCADE")),
        sa.Column('image_path', sa.String(255), nullable=False),
        sa.Column('thumbnail_path', sa.String(255), nullable=True),
        sa.Column('feature_vector', postgresql.JSON, nullable=True),
        sa.Column('confidence_score', sa.Float, nullable=True),
        sa.Column('capture_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('source', sa.String(100), nullable=True),
        sa.Column('is_primary', sa.Boolean, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now())
    )

    # Create suspect_locations table
    op.create_table(
        'suspect_locations',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('suspect_id', sa.Integer, sa.ForeignKey('suspects.id', ondelete="CASCADE")),
        sa.Column('camera_id', sa.String(50), sa.ForeignKey('cameras.camera_id')),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('confidence', sa.Float, nullable=True),
        sa.Column('coordinates', postgresql.JSON, nullable=True),
        sa.Column('movement_vector', postgresql.JSON, nullable=True),
        sa.Column('frame_number', sa.Integer, nullable=True)
    )

    # Create alerts table
    op.create_table(
        'alerts',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('alert_type', sa.String(50), nullable=False),
        sa.Column('severity', sa.Integer, nullable=False),
        sa.Column('track_id', sa.String(50), nullable=True),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('snapshot_path', sa.String(255), nullable=True),
        sa.Column('video_clip_path', sa.String(255), nullable=True),
        sa.Column('acknowledged', sa.Boolean, server_default='false'),
        sa.Column('acknowledged_by', sa.String(100), nullable=True),
        sa.Column('acknowledged_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('suspect_id', sa.Integer, sa.ForeignKey('suspects.id', ondelete="SET NULL"), nullable=True)
    )

    # Create detection_events table
    op.create_table(
        'detection_events',
        sa.Column('id', sa.String(50), primary_key=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('camera_id', sa.String(50), sa.ForeignKey('cameras.camera_id')),
        sa.Column('track_id', sa.String(50), nullable=True),
        sa.Column('confidence', sa.Float, nullable=True),
        sa.Column('detection_data', postgresql.JSON, nullable=True),
        sa.Column('snapshot_path', sa.String, nullable=True),
        sa.Column('video_clip_path', sa.String, nullable=True),
        sa.Column('processed', sa.Boolean, server_default='false'),
        sa.Column('person_count', sa.Integer, nullable=True),
        sa.Column('x', sa.Float, nullable=True),
        sa.Column('y', sa.Float, nullable=True)
    )

    # Create analytics table
    op.create_table(
        'analytics',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('timestamp', sa.DateTime, server_default=sa.func.now()),
        sa.Column('camera_id', sa.String(50), sa.ForeignKey('cameras.camera_id', ondelete="CASCADE")),
        sa.Column('total_people', sa.Integer, nullable=True),
        sa.Column('people_per_zone', postgresql.JSON, nullable=True),
        sa.Column('movement_patterns', postgresql.JSON, nullable=True),
        sa.Column('dwell_times', postgresql.JSON, nullable=True),
        sa.Column('entry_count', sa.Integer, nullable=True),
        sa.Column('exit_count', sa.Integer, nullable=True)
    )

def downgrade():
    # Drop tables in reverse order of creation
    op.drop_table('analytics')
    op.drop_table('detection_events')
    op.drop_table('alerts')
    op.drop_table('suspect_locations')
    op.drop_table('suspect_images')
    op.drop_table('suspect_case_association')
    op.drop_table('cases')
    op.drop_table('suspects')
    op.drop_table('cameras') 