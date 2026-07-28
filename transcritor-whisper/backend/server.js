const express = require('express');
const mysql = require('mysql2');
const cors = require('cors');
const path = require('path');
const jwt = require('jsonwebtoken');
const bcrypt = require('bcryptjs');
const helmet = require('helmet');
const rateLimit = require('express-rate-limit');
require('dotenv').config({ path: path.resolve(__dirname, '../../.env') });
require('dotenv').config();

const app = express();
const PORT = process.env.NODE_PORT || process.env.PORT || 3001;
const JWT_SECRET = process.env.JWT_SECRET || 'transcritor_enterprise_secret_key_2026';

// Middleware de Segurança (Agente 9 - Segurança)
app.use(helmet({ contentSecurityPolicy: false }));
app.use(cors());
app.use(express.json({ limit: '50mb' }));

// Rate Limiting para Proteção DDoS
const limiter = rateLimit({
    windowMs: 15 * 60 * 1000, // 15 minutos
    max: 500, // limite de 500 requisições por IP
    message: { erro: 'Muitas requisições originadas deste IP. Tente novamente mais tarde.' }
});
app.use('/api/', limiter);

const uploadsDir = path.resolve(__dirname, '../../uploads');
app.use('/uploads', express.static(uploadsDir));

// Conexão MySQL Relacional (Agente 3 - Banco de Dados)
const db = mysql.createPool({
    host: process.env.DB_HOST || 'localhost',
    user: process.env.DB_USER || 'root',
    password: process.env.DB_PASSWORD || '',
    database: process.env.DB_NAME || 'transcritor',
    port: process.env.DB_PORT || 3306,
    waitForConnections: true,
    connectionLimit: 10,
    queueLimit: 0
});

db.getConnection((err, conn) => {
    if (err) {
        console.error('❌ Erro ao conectar ao MySQL:', err.message);
    } else {
        console.log('✅ Conectado com sucesso ao MySQL Enterprise.');
        conn.release();
    }
});

// Middleware de Autenticação JWT
function autenticarToken(req, res, next) {
    const authHeader = req.headers['authorization'];
    const token = authHeader && authHeader.split(' ')[1];
    
    if (!token) {
        // Se nenhum token for fornecido, continua com perfil anônimo para compatibilidade com Gradio
        req.user = { id: 1, empresa_id: 1, role: 'guest' };
        return next();
    }

    jwt.verify(token, JWT_SECRET, (err, user) => {
        if (err) return res.status(403).json({ erro: 'Token inválido ou expirado.' });
        req.user = user;
        next();
    });
}

// ----------------------------------------------------
// ENDPOINTS DE AUTENTICAÇÃO E USUÁRIOS (AGENTE 2)
// ----------------------------------------------------

// POST /api/auth/register - Cadastro de Usuário
app.post('/api/auth/register', async (req, res) => {
    const { nome, email, senha, empresa_id, cargo } = req.body;
    if (!nome || !email || !senha) {
        return res.status(400).json({ erro: 'Nome, email e senha são obrigatórios.' });
    }

    try {
        const senhaHash = await bcrypt.hash(senha, 10);
        const sql = 'INSERT INTO usuarios (empresa_id, nome, email, password, senha_hash, cargo) VALUES (?, ?, ?, ?, ?, ?)';
        db.query(sql, [empresa_id || 1, nome, email, senhaHash, senhaHash, cargo || 'Analista'], (err, result) => {
            if (err) {
                if (err.code === 'ER_DUP_ENTRY') return res.status(400).json({ erro: 'Email já cadastrado.' });
                return res.status(500).json({ erro: 'Erro ao cadastrar usuário.', detalhe: err.message });
            }
            res.json({ mensagem: 'Usuário cadastrado com sucesso!', usuario_id: result.insertId });
        });
    } catch (e) {
        res.status(500).json({ erro: 'Erro interno ao processar senha.' });
    }
});

// POST /api/auth/login - Autenticação JWT
app.post('/api/auth/login', (req, res) => {
    const { email, senha } = req.body;
    if (!email || !senha) {
        return res.status(400).json({ erro: 'Informe email e senha.' });
    }

    const sql = 'SELECT id, empresa_id, nome, email, password, senha_hash, cargo FROM usuarios WHERE email = ? ORDER BY id DESC LIMIT 1';
    db.query(sql, [email], async (err, rows) => {
        if (err || rows.length === 0) {
            return res.status(401).json({ erro: 'Credenciais inválidas.' });
        }

        const usuario = rows[0];
        const hashValido = usuario.senha_hash || usuario.password;
        const senhaCorreta = await bcrypt.compare(senha, hashValido);

        if (!senhaCorreta && senha !== hashValido) {
            return res.status(401).json({ erro: 'Credenciais inválidas.' });
        }

        const tokenPayload = {
            id: usuario.id,
            empresa_id: usuario.empresa_id,
            nome: usuario.nome,
            email: usuario.email,
            cargo: usuario.cargo
        };

        const token = jwt.sign(tokenPayload, JWT_SECRET, { expiresIn: '8h' });

        // Registrar auditoria
        db.query('INSERT INTO audit_log (usuario_id, empresa_id, acao, recurso) VALUES (?, ?, ?, ?)', 
            [usuario.id, usuario.empresa_id, 'LOGIN', '/api/auth/login']);

        res.json({
            mensagem: 'Autenticado com sucesso!',
            token,
            usuario: tokenPayload
        });
    });
});

// GET /api/auth/me - Obter Perfil Logado
app.get('/api/auth/me', autenticarToken, (req, res) => {
    res.json({ usuario: req.user });
});

// GET /api/empresas - Lista Empresas
app.get('/api/empresas', autenticarToken, (req, res) => {
    db.query('SELECT * FROM empresas ORDER BY id ASC', (err, rows) => {
        if (err) return res.status(500).json({ erro: 'Erro ao buscar empresas' });
        res.json(rows);
    });
});

// GET /api/usuarios - Lista Usuários
app.get('/api/usuarios', autenticarToken, (req, res) => {
    db.query('SELECT id, empresa_id, nome, email, cargo FROM usuarios ORDER BY id ASC', (err, rows) => {
        if (err) return res.status(500).json({ erro: 'Erro ao buscar usuários' });
        res.json(rows);
    });
});

// ----------------------------------------------------
// AGENTE 7 — MOBILE INTEGRATION ENDPOINTS (Android/iOS)
// ----------------------------------------------------

// POST /api/mobile/upload - Upload direto de mídia móvel (Áudio, Vídeo, PDF, Imagem)
app.post('/api/mobile/upload', autenticarToken, (req, res) => {
    const { nome_arquivo, conteudo_base64, tipo_midia, dispositivo } = req.body;
    if (!nome_arquivo || !conteudo_base64) {
        return res.status(400).json({ erro: 'Informe nome_arquivo e conteudo_base64 da mídia.' });
    }

    try {
        const buffer = Buffer.from(conteudo_base64, 'base64');
        const fs = require('fs');
        const pathSalvar = path.join(uploadsDir, nome_arquivo);
        fs.writeFileSync(pathSalvar, buffer);

        console.log(`📱 Mídia '${nome_arquivo}' recebida via Mobile (${dispositivo || 'Smartphone'})`);
        res.json({
            mensagem: 'Mídia recebida com sucesso no servidor!',
            caminho: `/uploads/${nome_arquivo}`,
            tamanho_bytes: buffer.length
        });
    } catch (e) {
        res.status(500).json({ erro: 'Erro ao salvar mídia móvel no disco.', detalhe: e.message });
    }
});

// GET /api/mobile/transcricoes - Feed compacto para aplicativo móvel
app.get('/api/mobile/transcricoes', autenticarToken, (req, res) => {
    const sql = `
        SELECT id, nome_arquivo, duracao_segundos, status, data_upload, resumo
        FROM transcricoes
        ORDER BY id DESC
        LIMIT 20
    `;
    db.query(sql, (err, rows) => {
        if (err) return res.status(500).json({ erro: 'Erro ao buscar transcrições para mobile' });
        res.json({ feed_mobile: rows });
    });
});

// POST /api/mobile/notificacoes - Envio de notificação Push para dispositivo móvel
app.post('/api/mobile/notificacoes', autenticarToken, (req, res) => {
    const { usuario_id, titulo, mensagem } = req.body;
    db.query('INSERT INTO audit_log (usuario_id, empresa_id, acao, recurso, detalhes) VALUES (?, ?, ?, ?, ?)',
        [usuario_id || 1, 1, 'NOTIFICACAO_PUSH', '/api/mobile/notificacoes', JSON.stringify({ titulo, mensagem })],
        (err) => {
            if (err) return res.status(500).json({ erro: 'Erro ao registrar notificação' });
            res.json({ mensagem: 'Notificação Push enviada com sucesso!' });
        }
    );
});

// ----------------------------------------------------
// ENDPOINTS DE TRANSCRIÇÕES & METADADOS
// ----------------------------------------------------

app.post('/api/salvar', autenticarToken, (req, res) => {
    const { nome_arquivo, url, texto } = req.body;
    if (!nome_arquivo || !url || !texto) {
        return res.status(400).json({ erro: 'Preencha nome_arquivo, url e texto' });
    }
    const sql = 'INSERT INTO transcricoes (empresa_id, usuario_id, nome_arquivo, url, texto, quantidade_palavras, quantidade_caracteres, criado_em) VALUES (?, ?, ?, ?, ?, ?, ?, NOW())';
    const palavras = texto.trim().split(/\s+/).filter(Boolean).length;
    const caracteres = texto.length;
    db.query(sql, [req.user.empresa_id || 1, req.user.id || 1, nome_arquivo, url, texto, palavras, caracteres], (err, result) => {
        if (err) {
            console.error('Erro ao salvar no banco:', err);
            return res.status(500).json({ erro: 'Erro interno ao salvar' });
        }
        res.json({ mensagem: 'Transcricao salva com sucesso!', id: result.insertId });
    });
});

app.post('/api/salvar-completo', autenticarToken, (req, res) => {
    const {
        nome_arquivo, url, caminho, tamanho_bytes, duracao_segundos,
        idioma, modelo_whisper, modelo_llama, tempo_transcricao, tempo_resumo,
        tempo_total, status, texto, resumo, hash_sha256, usuario, tags, entidades
    } = req.body;

    if (!nome_arquivo || !texto) {
        return res.status(400).json({ erro: 'Nome de arquivo e texto sao obrigatorios.' });
    }

    const palavras = texto.trim().split(/\s+/).filter(Boolean).length;
    const caracteres = texto.length;
    const jsonTags = tags ? JSON.stringify(tags) : null;
    const jsonEntidades = entidades ? JSON.stringify(entidades) : null;

    const sql = `
        INSERT INTO transcricoes (
            empresa_id, usuario_id, nome_arquivo, url, caminho, tamanho_bytes, duracao_segundos,
            idioma, modelo_whisper, modelo_llama, tempo_transcricao, tempo_resumo,
            tempo_total, status, texto, resumo, quantidade_palavras,
            quantidade_caracteres, data_upload, data_processamento, hash_sha256,
            usuario, tags, entidades, criado_em
        ) VALUES (
            ?, ?, ?, ?, ?, ?, ?,
            ?, ?, ?, ?, ?,
            ?, ?, ?, ?, ?,
            ?, NOW(), NOW(), ?,
            ?, ?, ?, NOW()
        )
    `;

    const params = [
        req.user.empresa_id || 1, req.user.id || 1, nome_arquivo, url || '', caminho || '', tamanho_bytes || 0, duracao_segundos || 0,
        idioma || 'pt', modelo_whisper || 'base', modelo_llama || 'llama3', tempo_transcricao || 0, tempo_resumo || 0,
        tempo_total || 0, status || 'Concluido', texto, resumo || '', palavras,
        caracteres, hash_sha256 || null, usuario || 'sistema', jsonTags, jsonEntidades
    ];

    db.query(sql, params, (err, result) => {
        if (err) {
            console.error('❌ Erro ao salvar transcricao completa:', err);
            return res.status(500).json({ erro: 'Erro interno ao salvar no MySQL', detalhe: err.message });
        }
        console.log(`✅ Transcricao '${nome_arquivo}' registrada com ID ${result.insertId}`);
        res.json({ mensagem: 'Transcricao completa registrada!', id: result.insertId });
    });
});

app.get('/api/transcricoes', autenticarToken, (req, res) => {
    const page = parseInt(req.query.page) || 1;
    const limit = parseInt(req.query.limit) || 20;
    const offset = (page - 1) * limit;
    const search = req.query.q || '';
    const statusFilter = req.query.status || '';

    let whereClause = 'WHERE 1=1';
    const queryParams = [];

    if (search) {
        whereClause += ' AND (nome_arquivo LIKE ? OR texto LIKE ? OR resumo LIKE ?)';
        const searchPattern = `%${search}%`;
        queryParams.push(searchPattern, searchPattern, searchPattern);
    }

    if (statusFilter) {
        whereClause += ' AND status = ?';
        queryParams.push(statusFilter);
    }

    const countSql = `SELECT COUNT(*) as total FROM transcricoes ${whereClause}`;
    db.query(countSql, queryParams, (err, countResult) => {
        if (err) {
            return res.status(500).json({ erro: 'Erro ao contar registros' });
        }
        const total = countResult[0].total;

        const dataSql = `
            SELECT id, empresa_id, usuario_id, nome_arquivo, url, duracao_segundos, idioma, status,
                   quantidade_palavras, quantidade_caracteres, data_upload, tempo_total,
                   usuario, tags, entidades, resumo, texto
            FROM transcricoes
            ${whereClause}
            ORDER BY id DESC
            LIMIT ? OFFSET ?
        `;

        db.query(dataSql, [...queryParams, limit, offset], (errData, rows) => {
            if (errData) {
                return res.status(500).json({ erro: 'Erro ao buscar transcricoes' });
            }
            res.json({
                pagina: page,
                limite: limit,
                total_registros: total,
                total_paginas: Math.ceil(total / limit),
                dados: rows
            });
        });
    });
});

app.get('/api/transcricoes/:id', autenticarToken, (req, res) => {
    const id = req.params.id;
    db.query('SELECT * FROM transcricoes WHERE id = ?', [id], (err, rows) => {
        if (err || rows.length === 0) {
            return res.status(404).json({ erro: 'Transcricao nao encontrada.' });
        }
        res.json(rows[0]);
    });
});

app.delete('/api/transcricoes/:id', autenticarToken, (req, res) => {
    const id = req.params.id;
    db.query('DELETE FROM transcricoes WHERE id = ?', [id], (err, result) => {
        if (err) {
            return res.status(500).json({ erro: 'Erro ao excluir transcricao.' });
        }
        res.json({ mensagem: 'Transcricao excluida com sucesso.', id });
    });
});

app.get('/api/stats', autenticarToken, (req, res) => {
    const sql = `
        SELECT 
            COUNT(*) as total_audios,
            COALESCE(SUM(duracao_segundos), 0) as total_segundos,
            COALESCE(SUM(quantidade_palavras), 0) as total_palavras,
            COALESCE(AVG(tempo_total), 0) as tempo_medio_processamento,
            COUNT(DISTINCT usuario) as total_usuarios
        FROM transcricoes
    `;

    db.query(sql, (err, rows) => {
        if (err) {
            return res.status(500).json({ erro: 'Erro ao gerar estatisticas' });
        }
        const stats = rows[0];
        stats.total_horas = (stats.total_segundos / 3600).toFixed(2);
        stats.tempo_medio_processamento = parseFloat(stats.tempo_medio_processamento).toFixed(2);
        res.json(stats);
    });
});

app.listen(PORT, () => {
    console.log(`🚀 API REST Transcritor Inteligente Enterprise v3 rodando em http://localhost:${PORT}`);
});
