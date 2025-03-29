const Medicos = ({ medicos }) => {
    if (!medicos?.length) return null;
  
    return (
      <div style={{ marginTop: '15px' }}>
        <h3>Médicos Recomendados:</h3>
        <ul style={{ listStyle: 'none', padding: 0 }}>
          {medicos.map((medico, index) => (
            <li key={index} style={{ marginBottom: '15px', borderBottom: '1px solid #eee', paddingBottom: '10px' }}>
              <strong>{medico.Nome}</strong> ({medico.Especialidade})<br />
              📍 {medico.Lotação} | {medico.Endereço}<br />
              📞 {medico.Telefone}
            </li>
          ))}
        </ul>
      </div>
    );
  };
  
  export default Medicos;