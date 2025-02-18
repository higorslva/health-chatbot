
$(document).ready(function () {
    $('#enviar').on('click', function () {
        var pergunta = $('#pergunta').val().trim();
        if (pergunta === '') return;
        
        $('#chat-box').append('<div class="message user-message">' + pergunta + '</div>');
        $('#pergunta').val('');
        $('#chat-box').scrollTop($('#chat-box')[0].scrollHeight);
        
        $.ajax({
            type: 'POST',
            url: '/pergunta',
            data: { pergunta: pergunta },
            success: function (response) {
                $('#chat-box').append('<div class="message bot-message">' + response.resposta + '</div>');
                $('#chat-box').scrollTop($('#chat-box')[0].scrollHeight);
            },
            error: function () {
                $('#chat-box').append('<div class="message bot-message">Erro ao processar.</div>');
            }
        });
    });
    
    $('#pergunta').on('keypress', function (e) {
        if (e.which === 13) $('#enviar').click();
    });
});