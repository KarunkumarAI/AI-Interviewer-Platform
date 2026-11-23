-- Apply to an existing PostgreSQL database before running the upgraded app.
ALTER TABLE documents ADD COLUMN IF NOT EXISTS knowledge_role VARCHAR(80) NOT NULL DEFAULT 'Shared';
CREATE INDEX IF NOT EXISTS ix_documents_knowledge_role ON documents (knowledge_role);
