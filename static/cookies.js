document.addEventListener('DOMContentLoaded', function() {
  const cookieBanner = document.querySelector('.cookie-banner');
  const acceptButton = document.querySelector('.btn-accept-cookies');

  // Verifica se o usuário já aceitou os cookies
  if (!localStorage.getItem('cookiesAccepted')) {
    // Mostra o banner após um pequeno delay para garantir a animação
    setTimeout(() => {
      cookieBanner.classList.add('show');
    }, 500);
  }

  // Adiciona evento de clique no botão de aceitar
  acceptButton.addEventListener('click', function() {
    // Salva a preferência do usuário
    localStorage.setItem('cookiesAccepted', 'true');
    
    // Remove a classe show para iniciar a animação de saída
    cookieBanner.classList.remove('show');
  });
});