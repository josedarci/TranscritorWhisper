-- Migration v2: Expansão da Tabela transcricoes
-- Este script atualiza a tabela existente preservando todos os registros pré-existentes.

CREATE TABLE IF NOT EXISTS transcricoes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nome_arquivo VARCHAR(255) NOT NULL,
    url VARCHAR(255) NOT NULL,
    texto LONGTEXT NOT NULL,
    criado_em DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Adição dos novos campos de metadados, métricas e análise semântica
ALTER TABLE transcricoes
    ADD COLUMN IF NOT EXISTS caminho VARCHAR(512) DEFAULT NULL AFTER url,
    ADD COLUMN IF NOT EXISTS tamanho_bytes BIGINT DEFAULT 0 AFTER caminho,
    ADD COLUMN IF NOT EXISTS duracao_segundos FLOAT DEFAULT 0 AFTER tamanho_bytes,
    ADD COLUMN IF NOT EXISTS idioma VARCHAR(20) DEFAULT 'pt' AFTER duracao_segundos,
    ADD COLUMN IF NOT EXISTS modelo_whisper VARCHAR(50) DEFAULT 'base' AFTER idioma,
    ADD COLUMN IF NOT EXISTS modelo_llama VARCHAR(50) DEFAULT 'llama3' AFTER modelo_whisper,
    ADD COLUMN IF NOT EXISTS tempo_transcricao FLOAT DEFAULT 0 AFTER modelo_llama,
    ADD COLUMN IF NOT EXISTS tempo_resumo FLOAT DEFAULT 0 AFTER tempo_transcricao,
    ADD COLUMN IF NOT EXISTS tempo_total FLOAT DEFAULT 0 AFTER tempo_resumo,
    ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'Concluído' AFTER tempo_total,
    ADD COLUMN IF NOT EXISTS resumo LONGTEXT DEFAULT NULL AFTER texto,
    ADD COLUMN IF NOT EXISTS quantidade_palavras INT DEFAULT 0 AFTER resumo,
    ADD COLUMN IF NOT EXISTS quantidade_caracteres INT DEFAULT 0 AFTER quantidade_palavras,
    ADD COLUMN IF NOT EXISTS data_upload DATETIME DEFAULT CURRENT_TIMESTAMP AFTER quantidade_caracteres,
    ADD COLUMN IF NOT EXISTS data_processamento DATETIME DEFAULT CURRENT_TIMESTAMP AFTER data_upload,
    ADD COLUMN IF NOT EXISTS hash_sha256 VARCHAR(64) DEFAULT NULL AFTER data_processamento,
    ADD COLUMN IF NOT EXISTS usuario VARCHAR(100) DEFAULT 'sistema' AFTER hash_sha256,
    ADD COLUMN IF NOT EXISTS tags JSON DEFAULT NULL AFTER usuario,
    ADD COLUMN IF NOT EXISTS entidades JSON DEFAULT NULL AFTER tags;

-- Índices para otimização de busca rápida
CREATE INDEX IF NOT EXISTS idx_nome_arquivo ON transcricoes(nome_arquivo);
CREATE INDEX IF NOT EXISTS idx_status ON transcricoes(status);
CREATE INDEX IF NOT EXISTS idx_data_upload ON transcricoes(data_upload);
CREATE INDEX IF NOT EXISTS idx_usuario ON transcricoes(usuario);
