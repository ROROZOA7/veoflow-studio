"""add_script_generation_tables

Revision ID: 64200476832f
Revises: 858bb2aaa154
Create Date: 2025-12-14 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite


# revision identifiers, used by Alembic.
revision = '64200476832f'
down_revision = '858bb2aaa154'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Check if scripts table exists before creating it
    from sqlalchemy import inspect
    conn = op.get_bind()
    inspector = inspect(conn)
    existing_tables = inspector.get_table_names()
    
    # Create scripts table only if it doesn't exist
    if 'scripts' not in existing_tables:
        op.create_table('scripts',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('project_id', sa.String(), nullable=False),
        sa.Column('main_content', sa.Text(), nullable=False),
        sa.Column('video_duration', sa.Integer(), nullable=False),
        sa.Column('style', sa.String(), nullable=False),
        sa.Column('target_audience', sa.String(), nullable=False),
        sa.Column('aspect_ratio', sa.String(), nullable=False),
        sa.Column('language', sa.String(), nullable=True),
        sa.Column('voice_style', sa.String(), nullable=True),
        sa.Column('music_style', sa.String(), nullable=True),
        sa.Column('color_palette', sa.String(), nullable=True),
        sa.Column('transition_style', sa.String(), nullable=True),
        sa.Column('full_script', sa.Text(), nullable=True),
        sa.Column('story_structure', sa.JSON(), nullable=True),
        sa.Column('scene_count', sa.Integer(), nullable=True),
        sa.Column('generated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('project_id')
    )
    
    # Add new columns to characters table (with existence check for SQLite)
    # Note: SQLite doesn't support IF NOT EXISTS for ALTER TABLE ADD COLUMN
    # So we check if column exists first to avoid errors
    from sqlalchemy import inspect
    conn = op.get_bind()
    inspector = inspect(conn)
    
    # Get existing columns
    char_cols = {col['name'] for col in inspector.get_columns('characters')}
    scene_cols = {col['name'] for col in inspector.get_columns('scenes')}
    
    # Add characters columns only if they don't exist
    char_columns_to_add = [
        ('age_description', sa.String()),
        ('species', sa.String()),
        ('voice_personality', sa.Text()),
        ('body_build', sa.String()),
        ('face_shape', sa.String()),
        ('skin_or_fur_color', sa.String()),
        ('signature_feature', sa.Text()),
        ('outfit_top', sa.String()),
        ('outfit_bottom', sa.String()),
        ('helmet_or_hat', sa.String()),
        ('shoes_or_footwear', sa.String()),
        ('props', sa.JSON()),
        ('body_metrics', sa.JSON()),
        ('position', sa.String()),
        ('orientation', sa.String()),
        ('pose', sa.String()),
        ('foot_placement', sa.String()),
        ('hand_detail', sa.String()),
        ('expression', sa.String()),
        ('action_flow', sa.JSON()),
    ]
    
    for col_name, col_type in char_columns_to_add:
        if col_name not in char_cols:
            op.add_column('characters', sa.Column(col_name, col_type, nullable=True))
    
    # Add scenes columns only if they don't exist
    scene_columns_to_add = [
        ('scene_description', sa.Text()),
        ('duration_sec', sa.Integer()),
        ('visual_style', sa.Text()),
        ('environment', sa.Text()),
        ('camera_angle', sa.String()),
        ('character_adaptations', sa.JSON()),
    ]
    
    for col_name, col_type in scene_columns_to_add:
        if col_name not in scene_cols:
            op.add_column('scenes', sa.Column(col_name, col_type, nullable=True))


def downgrade() -> None:
    # Remove new columns from scenes table
    op.drop_column('scenes', 'character_adaptations')
    op.drop_column('scenes', 'camera_angle')
    op.drop_column('scenes', 'environment')
    op.drop_column('scenes', 'visual_style')
    op.drop_column('scenes', 'duration_sec')
    op.drop_column('scenes', 'scene_description')
    
    # Remove new columns from characters table
    op.drop_column('characters', 'action_flow')
    op.drop_column('characters', 'expression')
    op.drop_column('characters', 'hand_detail')
    op.drop_column('characters', 'foot_placement')
    op.drop_column('characters', 'pose')
    op.drop_column('characters', 'orientation')
    op.drop_column('characters', 'position')
    op.drop_column('characters', 'body_metrics')
    op.drop_column('characters', 'props')
    op.drop_column('characters', 'shoes_or_footwear')
    op.drop_column('characters', 'helmet_or_hat')
    op.drop_column('characters', 'outfit_bottom')
    op.drop_column('characters', 'outfit_top')
    op.drop_column('characters', 'signature_feature')
    op.drop_column('characters', 'skin_or_fur_color')
    op.drop_column('characters', 'face_shape')
    op.drop_column('characters', 'body_build')
    op.drop_column('characters', 'voice_personality')
    op.drop_column('characters', 'species')
    op.drop_column('characters', 'age_description')
    
    # Drop scripts table
    op.drop_table('scripts')

