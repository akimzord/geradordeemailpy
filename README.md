Gerador de E-mail - Gestor de E-mail Temporário
Um gestor de e-mails temporários desktop, construído em Python com uma interface gráfica (GUI) utilizando Tkinter. A aplicação interage com a API do FireMail para criar e gerir endereços de e-mail descartáveis de forma simples e rápida.

📥 Download
Para baixar a versão já compilada para Windows, clique no link abaixo:

Baixar [FiremailGerenciador.exe](https://github.com/akimzord/geradordeemailpy/raw/refs/heads/main/FiremailGerenciador.exe)

✨ Funcionalidades
Geração Rápida: Crie novos endereços de e-mail temporários com um único clique.

Caixa de Entrada Integrada: Visualize os e-mails recebidos diretamente na aplicação, com uma formatação clara que separa remetente, assunto e corpo da mensagem.

Gestão de E-mails: Todos os e-mails gerados são guardados localmente, permitindo-lhe aceder a eles sempre que precisar.

Copiar e Eliminar: Copie facilmente o endereço de e-mail para a área de transferência ou elimine e-mails que já não são necessários.

Persistência: A sua lista de e-mails é guardada num ficheiro emails.json, para que não perca o acesso às suas caixas de entrada ao fechar a aplicação.

Interface Responsiva: A interface foi desenhada para ser intuitiva e adapta-se a diferentes tamanhos de janela.

🚀 Tecnologias Utilizadas
Python 3: Linguagem de programação principal.

Tkinter: Biblioteca padrão do Python para a criação da interface gráfica.

Requests: Biblioteca para realizar as chamadas HTTP à API do FireMail.

🛠️ Como Executar (a partir do código)
Para executar o projeto localmente, siga estes passos:

Clone o repositório:

git clone [https://github.com/akimzord/geradordeemailpy.git](https://github.com/akimzord/geradordeemailpy.git)
cd geradordeemailpy

Instale as dependências:
A única dependência externa é a biblioteca requests. Pode instalá-la usando o pip.

pip install requests

Execute a aplicação:

python main.py

📂 Estrutura do Código
O código está organizado principalmente em duas classes:

FireMailClient: Esta classe é o "motor" da aplicação. É responsável por toda a comunicação com a API do FireMail, incluindo a criação de e-mails, a verificação da caixa de entrada e a obtenção de mensagens individuais.

EmailApp: Esta é a classe principal da interface gráfica, que herda de tk.Tk. Ela constrói todos os elementos visuais (janelas, botões, caixas de texto) e gere os eventos do utilizador (cliques de botão, seleções na lista). Para evitar que a interface "congele" durante as chamadas à rede, utiliza threading para executar as operações de API em segundo plano.

emails.json: Um ficheiro JSON simples que é criado na primeira execução para armazenar a lista de endereços de e-mail que foram gerados.

🤝 Contribuições
Contribuições são bem-vindas! Se tiver ideias para novas funcionalidades, melhorias na interface ou correções de bugs, sinta-se à vontade para abrir uma issue ou submeter um pull request.

📄 Licença
Este projeto está licenciado sob a Licença MIT. Veja o ficheiro LICENSE para mais detalhes.
