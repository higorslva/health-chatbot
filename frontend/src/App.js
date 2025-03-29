import React, { useState } from 'react';
import axios from 'axios';
import ReactMarkdown from 'react-markdown'; // Importe aqui

function App() {
  const [input, setInput] = useState('');
  const [resposta, setResposta] = useState('');
  const [carregando, setCarregando] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setCarregando(true);
    
    try {
      const response = await axios.post('http://localhost:5000/pergunta', {
        pergunta: input
      });
      
      setResposta(response.data.resposta);
    } catch (error) {
      setResposta(`Erro: ${error.response?.data?.erro || error.message}`);
    } finally {
      setCarregando(false);
    }
  };

  return (
    <div style={{ maxWidth: '800px', margin: '0 auto', padding: '20px' }}>
      <h1>Sistema de Recomendação Médica</h1>
      
      <form onSubmit={handleSubmit}>
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Descreva seus sintomas ou informe o ID do paciente..."
          rows={4}
          style={{ width: '100%', marginBottom: '10px' }}
        />
        <button type="submit" disabled={carregando}>
          {carregando ? 'Processando...' : 'Enviar'}
        </button>
      </form>

      {resposta && (
        <div style={{ marginTop: '20px', borderTop: '1px solid #ccc', paddingTop: '20px' }}>
          {/* Renderize o Markdown aqui: */}
          <ReactMarkdown className="markdown-style">{resposta}</ReactMarkdown>
        </div>
      )}
    </div>
  );
}

export default App;