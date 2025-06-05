require('dotenv').config(); // <-- Adicionado aqui
const express = require('express');
const mysql = require('mysql2');
const cors = require('cors');

const app = express();
app.use(cors());
app.use(express.json());

// Usa as variáveis de ambiente
const db = mysql.createPool({
    host: process.env.DB_HOST,
    user: process.env.DB_USER,
    password: process.env.DB_PASSWORD,
    database: process.env.DB_NAME,
    waitForConnections: true,
    connectionLimit: 10,
    queueLimit: 0
});




// Endpoint para salvar transcrição
app.post('/api/salvar', (req, res) => {
    const { nome_arquivo, url, texto } = req.body;
    const criado_em = new Date();

    if (!nome_arquivo || !url || !texto) {
        return res.status(400).json({ erro: 'Dados incompletos' });
    }

    const sql = `
        INSERT INTO transcricoes (nome_arquivo, url, texto, criado_em)
        VALUES (?, ?, ?, ?)
    `;

    db.query(sql, [nome_arquivo, url, texto, criado_em], (err, result) => {
        if (err) {
            console.error("Erro ao salvar no banco:", err);
            return res.status(500).json({ erro: 'Erro interno ao salvar' });
        }
        res.json({ sucesso: true, id: result.insertId });
    });
});

// Inicializa o servidor
const PORT = 3001;
app.listen(PORT, () => {
    console.log(`? API rodando em http://localhost:${PORT}`);
});
