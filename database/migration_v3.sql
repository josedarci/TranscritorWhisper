-- Migration v3: Autenticação, RBAC, Multi-Tenancy (Empresas) e Auditoria Enterprise
-- Preserva 100% dos dados existentes na tabela transcricoes.

-- 1. Tabela de Empresas (Multi-Tenancy)
CREATE TABLE IF NOT EXISTS empresas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    razao_social VARCHAR(255) NOT NULL,
    nome_fantasia VARCHAR(255) DEFAULT NULL,
    cnpj VARCHAR(20) DEFAULT NULL,
    status VARCHAR(50) DEFAULT 'Ativo',
    criado_em DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 2. Tabela de Perfis de Acesso (Roles)
CREATE TABLE IF NOT EXISTS roles (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(50) NOT NULL UNIQUE,
    descricao VARCHAR(255) DEFAULT NULL,
    criado_em DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 3. Tabela de Permissões (Permissions)
CREATE TABLE IF NOT EXISTS permissions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(100) NOT NULL UNIQUE,
    modulo VARCHAR(50) NOT NULL,
    descricao VARCHAR(255) DEFAULT NULL,
    criado_em DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 4. Tabela de Usuários
CREATE TABLE IF NOT EXISTS usuarios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    empresa_id INT DEFAULT 1,
    nome VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    senha_hash VARCHAR(255) NOT NULL,
    cargo VARCHAR(100) DEFAULT 'Analista',
    status VARCHAR(50) DEFAULT 'Ativo',
    criado_em DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (empresa_id) REFERENCES empresas(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 5. Tabela de Associação Usuário-Role
CREATE TABLE IF NOT EXISTS user_roles (
    usuario_id INT NOT NULL,
    role_id INT NOT NULL,
    atribuido_em DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (usuario_id, role_id),
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE,
    FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 6. Tabela de Trilha de Auditoria (Audit Log)
CREATE TABLE IF NOT EXISTS audit_log (
    id INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT DEFAULT NULL,
    empresa_id INT DEFAULT NULL,
    acao VARCHAR(100) NOT NULL,
    recurso VARCHAR(255) NOT NULL,
    detalhes JSON DEFAULT NULL,
    ip VARCHAR(45) DEFAULT NULL,
    user_agent VARCHAR(255) DEFAULT NULL,
    criado_em DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 7. Tabela de API Keys
CREATE TABLE IF NOT EXISTS api_keys (
    id INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT NOT NULL,
    empresa_id INT NOT NULL,
    chave_hash VARCHAR(255) NOT NULL,
    nome VARCHAR(100) NOT NULL,
    ativa BOOLEAN DEFAULT TRUE,
    criado_em DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE,
    FOREIGN KEY (empresa_id) REFERENCES empresas(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 8. Tabelas de Estruturação de Reuniões (Agente 3 - Banco de Dados)
CREATE TABLE IF NOT EXISTS uploads (
    id INT AUTO_INCREMENT PRIMARY KEY,
    empresa_id INT DEFAULT 1,
    usuario_id INT DEFAULT 1,
    nome_original VARCHAR(255) NOT NULL,
    caminho VARCHAR(512) NOT NULL,
    tipo VARCHAR(50) DEFAULT 'audio/mp3',
    tamanho_bytes BIGINT DEFAULT 0,
    criado_em DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS embeddings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    transcricao_id INT NOT NULL,
    chunk_index INT NOT NULL,
    vetor JSON NOT NULL,
    criado_em DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS chat_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT NOT NULL,
    transcricao_id INT DEFAULT NULL,
    pergunta TEXT NOT NULL,
    resposta TEXT NOT NULL,
    criado_em DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS meeting_summary (
    id INT AUTO_INCREMENT PRIMARY KEY,
    transcricao_id INT NOT NULL,
    resumo_executivo LONGTEXT,
    resumo_tecnico LONGTEXT,
    sentimento VARCHAR(50) DEFAULT 'Neutro',
    criado_em DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS meeting_decisions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    transcricao_id INT NOT NULL,
    decisao TEXT NOT NULL,
    impacto VARCHAR(100),
    criado_em DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS meeting_tasks (
    id INT AUTO_INCREMENT PRIMARY KEY,
    transcricao_id INT NOT NULL,
    tarefa TEXT NOT NULL,
    responsavel VARCHAR(100),
    prazo VARCHAR(50),
    status VARCHAR(50) DEFAULT 'Pendente',
    criado_em DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 9. Dados Iniciais (Empresa Padrão e Administrador)
INSERT IGNORE INTO empresas (id, razao_social, nome_fantasia, status) 
VALUES (1, 'Empresa XYZ Sistemas', 'Empresa XYZ', 'Ativo');

INSERT IGNORE INTO roles (id, nome, descricao) VALUES
(1, 'admin', 'Administrador Geral do Sistema'),
(2, 'user', 'Usuário Operacional');

INSERT IGNORE INTO usuarios (id, empresa_id, nome, email, senha_hash, cargo, status)
VALUES (1, 1, 'Administrador Enterprise', 'admin@transcritor.com', '$2a$10$w8T0iLgX7u1Gq3E/54sW.O6kP9/Rz7ePjP7eX6sK9G6H7J8K9L0M1', 'Administrador', 'Ativo');

INSERT IGNORE INTO user_roles (usuario_id, role_id) VALUES (1, 1);
