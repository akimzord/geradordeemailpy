import requests
import time
import json
import os # Importar para verificar a existência do arquivo

# Nome do arquivo JSON onde os e-mails serão salvos
EMAILS_FILE = 'emails.json'

class FireMailClient:
    def __init__(self):
        # Define a URL base da API FireMail
        self.api_url = 'https://firemail.com.br/api'

    def create_email(self, username=None):
        # Constrói o endpoint para criação de e-mail
        endpoint = f'{self.api_url}/email/create'
        # Prepara os dados para a requisição (opcionalmente com um nome de usuário)
        data = {'email': username} if username else {}
        # Envia uma requisição POST para criar o e-mail
        response = requests.post(endpoint, json=data)
        # Levanta um erro HTTP se a requisição não for bem-sucedida
        response.raise_for_status()
        # Retorna a resposta JSON da API
        return response.json()

    def check_email(self, email_name):
        # Constrói o endpoint para verificar e-mails
        endpoint = f'{self.api_url}/email/check/{email_name}'
        # Envia uma requisição GET para verificar as mensagens
        response = requests.get(endpoint)
        # Levanta um erro HTTP se a requisição não for bem-sucedida
        response.raise_for_status()
        # Retorna a resposta JSON da API
        return response.json()

    def get_message(self, email_name, message_id):
        # Constrói o endpoint para obter uma mensagem específica
        endpoint = f'{self.api_url}/email/message/{email_name}/{message_id}'
        # Envia uma requisição GET para obter os detalhes da mensagem
        response = requests.get(endpoint)
        # Levanta um erro HTTP se a requisição não for bem-sucedida
        response.raise_for_status()
        # Retorna a resposta JSON da API
        return response.json()

    def wait_for_verification(self, email, expected_sender, timeout=300):
        # Extrai o nome do e-mail da string completa
        email_name = email.split('@')[0]
        start_time = time.time()
        # Loop para verificar mensagens até o timeout
        while time.time() - start_time < timeout:
            data = self.check_email(email_name)
            # Verifica se a requisição foi bem-sucedida e se há mensagens
            if data.get('status') == 'success' and data.get('data', {}).get('message_count', 0) > 0:
                for msg in data['data']['messages']:
                    # Procura por uma mensagem do remetente esperado
                    if expected_sender in msg['from']['email']:
                        # Retorna a mensagem completa se encontrada
                        return self.get_message(email_name, msg['id'])
            # Espera 5 segundos antes de tentar novamente
            time.sleep(5)
        # Retorna None se o tempo limite for excedido
        return None

def load_emails():
    # Carrega a lista de e-mails do arquivo JSON
    if os.path.exists(EMAILS_FILE):
        with open(EMAILS_FILE, 'r') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                # Retorna uma lista vazia se o arquivo estiver corrompido ou vazio
                return []
    return [] # Retorna uma lista vazia se o arquivo não existir

def save_emails(emails):
    # Salva a lista de e-mails no arquivo JSON
    with open(EMAILS_FILE, 'w') as f:
        json.dump(emails, f, indent=4) # Usa indent para formatar o JSON de forma legível

def display_messages(client, email):
    # Exibe as mensagens de um e-mail específico
    email_name = email.split('@')[0]
    print(f"\n--- Mensagens para {email} ---")
    try:
        messages_data = client.check_email(email_name)
        if messages_data.get('status') == 'success' and messages_data.get('data', {}).get('message_count', 0) > 0:
            print(f"Mensagens recebidas ({messages_data['data']['message_count']}):")
            for msg_summary in messages_data['data']['messages']:
                print(f"\n  ID da Mensagem: {msg_summary['id']}")
                print(f"  De: {msg_summary['from']['name']} <{msg_summary['from']['email']}>")
                print(f"  Assunto: {msg_summary['subject']}")
                # Pega o conteúdo completo da mensagem
                full_message = client.get_message(email_name, msg_summary['id'])
                if full_message.get('status') == 'success':
                    # Decodifica o corpo da mensagem, se necessário (ex: de HTML para texto)
                    print(f"  Conteúdo:\n{full_message['data']['body']}")
                else:
                    print(f"  Erro ao obter conteúdo da mensagem: {full_message.get('message', 'Erro desconhecido')}")
            
        else:
            print("Nenhuma nova mensagem.")
    except requests.exceptions.RequestException as e:
        print(f"Erro de conexão ao verificar mensagens: {e}")
    except Exception as e:
        print(f"Ocorreu um erro inesperado ao exibir mensagens: {e}")

def main_loop():
    client = FireMailClient()
    
    while True:
        print('\n--- Gerador e Leitor de E-mail Temporário ---')
        emails = load_emails() # Carrega os e-mails salvos

        print("\nEscolha uma opção:")
        print("1. Gerar novo e-mail")
        if emails: # Só mostra a opção se houver e-mails salvos
            print("2. Acessar e-mail salvo")
        print("3. Sair")

        choice = input("Digite o número da opção: ")

        if choice == '1':
            print('\nCriando e-mail temporário...')
            try:
                result = client.create_email()
                if result.get('status') == 'success':
                    email = result['data']['email']
                    email_name = email.split('@')[0]
                    print(f'E-mail temporário criado: {email}')
                    print(f"Você pode acessar este e-mail através da URL: {client.api_url}/email/check/{email_name}")
                    
                    # Adiciona o novo e-mail à lista e salva
                    emails.append({'email': email, 'name': email_name})
                    save_emails(emails)
                    print(f"E-mail {email} salvo em {EMAILS_FILE}.")

                    while True:
                        access_now = input("Deseja acessar este e-mail agora? (s/n): ").lower()
                        if access_now == 's':
                            display_messages(client, email)
                            break
                        elif access_now == 'n':
                            break
                        else:
                            print("Opção inválida. Por favor, digite 's' ou 'n'.")
                else:
                    print(f"Erro ao criar e-mail: {result.get('message', 'Erro desconhecido')}")
            except requests.exceptions.RequestException as e:
                print(f"Erro de conexão: {e}")
            except Exception as e:
                print(f"Ocorreu um erro inesperado: {e}")

        elif choice == '2' and emails:
            print("\n--- Seus E-mails Salvos ---")
            for i, email_info in enumerate(emails):
                print(f"{i + 1}. {email_info['email']}")
            
            while True:
                try:
                    email_index = input("Digite o número do e-mail que deseja acessar (ou 'v' para voltar ao menu principal): ")
                    if email_index.lower() == 'v':
                        break
                    
                    email_index = int(email_index) - 1
                    if 0 <= email_index < len(emails):
                        selected_email = emails[email_index]['email']
                        display_messages(client, selected_email)
                        break # Sai do loop de seleção após exibir as mensagens
                    else:
                        print("Número inválido. Por favor, digite um número da lista.")
                except ValueError:
                    print("Entrada inválida. Por favor, digite um número ou 'v'.")
                except Exception as e:
                    print(f"Ocorreu um erro ao acessar o e-mail salvo: {e}")

        elif choice == '3':
            print("Encerrando o programa. Obrigado!")
            break # Sai do loop principal

        else:
            print("Opção inválida. Por favor, selecione uma opção válida.")

if __name__ == '__main__':
    main_loop()
