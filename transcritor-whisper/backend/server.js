const express = require('express');
const mysql = require('mysql2');
const cors = require('cors');
const path = require('path');
require('dotenv').config({ path: path.resolve(__dirname, '../../.env') });
require('dotenv').config();

const app = express();
const PORT = process.env.NODE_PORT || process.env.PORT || 3001;

app.use(cors());
app.use(express.json({ limit: '50mb' }));

const uploadsDir = path.resolve(__dirname, '../../uploads');
app.use('/uploads', express.static(uploadsDir));

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
        console.log('✅ Conectado com sucesso ao MySQL.');
        conn.release();
    }
});

app.post('/api/salvar', (req, res) => {
    const { nome_arquivo, url, texto } = req.body;
    if (!nome_arquivo || !url || !texto) {
        return res.status(400).json({ erro: 'Preencha nome_arquivo, url e texto' });
    }
    const sql = 'INSERT INTO transcricoes (nome_arquivo, url, texto, quantidade_palavras, quantidade_caracteres, criado_em) VALUES (?, ?, ?, ?, ?, NOW())';
    const palavras = texto.trim().split(/\s+/).filter(Boolean).length;
    const caracteres = texto.length;
    db.query(sql, [nome_arquivo, url, texto, palavras, caracteres], (err, result) => {
        if (err) {
            console.error('Erro ao salvar no banco:', err);
            return res.status(500).json({ erro: 'Erro interno ao salvar' });
        }
        res.json({ mensagem: 'Transcricao salva com sucesso!', id: result.insertId });
    });
});

app.post('/api/salvar-completo', (req, res) => {
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
            nome_arquivo, url, caminho, tamanho_bytes, duracao_segundos,
            idioma, modelo_whisper, modelo_llama, tempo_transcricao, tempo_resumo,
            tempo_total, status, texto, resumo, quantidade_palavras,
            quantidade_caracteres, data_upload, data_processamento, hash_sha256,
            usuario, tags, entidades, criado_em
        ) VALUES (
            ?, ?, ?, ?, ?,
            ?, ?, ?, ?, ?,
            ?, ?, ?, ?, ?,
            ?, NOW(), NOW(), ?,
            ?, ?, ?, NOW()
        )
    `;

    const params = [
        nome_arquivo, url || '', caminho || '', tamanho_bytes || 0, duracao_segundos || 0,
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

app.get('/api/transcricoes', (req, res) => {
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
            SELECT id, nome_arquivo, url, duracao_segundos, idioma, status,
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

app.get('/api/transcricoes/:id', (req, res) => {
    const id = req.params.id;
    db.query('SELECT * FROM transcricoes WHERE id = ?', [id], (err, rows) => {
        if (err || rows.length === 0) {
            return res.status(404).json({ erro: 'Transcricao nao encontrada.' });
        }
        res.json(rows[0]);
    });
});

app.delete('/api/transcricoes/:id', (req, res) => {
    const id = req.params.id;
    db.query('DELETE FROM transcricoes WHERE id = ?', [id], (err, result) => {
        if (err) {
            return res.status(500).json({ erro: 'Erro ao excluir transcricao.' });
        }
        res.json({ mensagem: 'Transcricao excluida com sucesso.', id });
    });
});

app.get('/api/stats', (req, res) => {
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
    console.log(`🚀 API REST Transcritor Inteligente rodando em http://localhost:${PORT}`);
});
