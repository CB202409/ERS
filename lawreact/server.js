const express = require('express');
const cors = require('cors');
const bodyParser = require('body-parser');
const axios = require('axios');
require('dotenv').config();  // 환경 변수 로드

const app = express();
const PORT = 5000;

app.use(cors());
app.use(bodyParser.json());

const OPENAI_API_KEY = process.env.OPENAI_API_KEY;  //API 가져오기

app.post('/chat', async (req, res) => {
    const { query, session_id } = req.body;  // 클라이언트에서 받은 query와 session_id
    console.log(`Received message: ${query}, session_id: ${session_id}`);

    try {
        const response = await axios.post('https://api.openai.com/v1/chat/completions', {
            model: 'gpt-3.5-turbo',
            messages: [{ role: 'user', content: query }],  // query 값 전송
            max_tokens: 150,
            temperature: 0.9,
        }, {
            headers: {
                'Authorization': `Bearer ${OPENAI_API_KEY}`,
                'Content-Type': 'application/json'
            }
        });

        const aiResponse = response.data.choices[0].message.content.trim();
        res.json({ response: aiResponse });
    } catch (error) {
        console.error('Error calling OpenAI API:', error);
        res.status(500).json({ response: '서버에 문제가 발생했습니다.' });
    }
});

app.listen(PORT, () => {
    console.log(`Server is running on http://localhost:${PORT}`);
});
