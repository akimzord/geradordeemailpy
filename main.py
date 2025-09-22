import tkinter as tk
from tkinter import messagebox, simpledialog, Listbox, Frame, Label, Entry, Button, Text, Scrollbar, font
import requests
import json
import os
import threading
import logging
import time
import random

# --- MODO DE SIMULAÇÃO ---
# Mude para False para tentar usar a API real.
# Deixe como True para usar dados falsos e testar a interface.
USE_MOCK_API = False

# --- Configuração de Logs ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Constantes ---
EMAILS_FILE = 'emails.json'

# --- Cores e Fontes para o Novo Design ---
BG_COLOR = "#1e1e2e"
FRAME_COLOR = "#181825"
TEXT_COLOR = "#cdd6f4"
ACCENT_COLOR = "#89b4fa"
HOVER_ACCENT_COLOR = "#a6e3a1"
SECONDARY_COLOR = "#585b70"
HOVER_SECONDARY_COLOR = "#6c7086"
DANGER_COLOR = "#f38ba8"
HOVER_DANGER_COLOR = "#eba0ac"
PLACEHOLDER_COLOR = "#6c7086"

# --- Classes de Widgets Personalizados ---
class HoverButton(tk.Button):
    """Um botão que muda de cor ao passar o mouse por cima."""
    def __init__(self, master, hover_color, **kwargs):
        super().__init__(master, **kwargs)
        self.default_bg = self["background"]
        self.hover_color = hover_color
        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)

    def on_enter(self, e):
        self['background'] = self.hover_color

    def on_leave(self, e):
        self['background'] = self.default_bg

# --- Classes da API ---
class FireMailClient:
    """Cliente para interagir com a API real do FireMail."""
    def __init__(self):
        self.api_url = 'https://firemail.com.br/api'
        self.timeout = 15

    def _make_request(self, method, endpoint, **kwargs):
        url = f'{self.api_url}/{endpoint}'
        logging.info(f"Fazendo requisição {method.upper()} para: {url} com dados: {kwargs.get('json')}")
        response = None
        try:
            response = requests.request(method, url, timeout=self.timeout, **kwargs)
            response.raise_for_status()
            return response.json()
        except json.JSONDecodeError:
            response_text = response.text if response else "Nenhuma resposta recebida"
            logging.error(f"Falha ao decodificar JSON. Status: {response.status_code if response else 'N/A'}. Resposta: '{response_text[:200]}...'")
            if response_text.strip().lower().startswith("<!doctype html>"):
                error_msg = "A API parece estar em manutenção (retornou HTML).\nPor favor, tente novamente mais tarde."
            else:
                error_msg = "A API retornou uma resposta inválida (não era JSON).\nIsso pode ser um erro temporário do servidor."
            raise requests.exceptions.RequestException(error_msg)
        except requests.exceptions.HTTPError as e:
            logging.error(f"Erro HTTP: {e.response.status_code} - Resposta: {e.response.text}")
            raise e
        except requests.exceptions.RequestException as e:
            logging.error(f"Erro de conexão para {url}: {type(e).__name__} - {e}")
            raise e
    
    def create_email(self, username=None):
        data = {'email': username} if username else {}
        return self._make_request('post', 'email/create', json=data)

    def check_email(self, email_name):
        return self._make_request('get', f'email/check/{email_name}')

    def get_message(self, email_name, message_id):
        return self._make_request('get', f'email/message/{email_name}/{message_id}')

class MockFireMailClient:
    """Cliente de API Falso para testes de UI quando a API real está offline."""
    def __init__(self):
        logging.info("AVISO: Usando o cliente de API Falso (Mock). As mensagens são simuladas.")

    def create_email(self, username=None):
        time.sleep(0.5) # Simula latência da rede
        if username:
            if len(username) < 3:
                return {'status': 'error', 'message': 'O nome de usuário é muito curto.'}
            email = f"{username}@firemail.com.br"
        else:
            name = "".join(random.choices("abcdefghijklmnopqrstuvwxyz1234567890", k=8))
            email = f"{name}@firemail.com.br"
        return {'status': 'success', 'data': {'email': email}}

    def check_email(self, email_name):
        time.sleep(1)
        if random.random() < 0.3: # 30% de chance de não ter e-mails
            return {'status': 'success', 'data': {'message_count': 0, 'messages': []}}
        
        count = random.randint(1, 5)
        messages = []
        for i in range(count):
            messages.append({
                "id": f"mock_id_{i}",
                "from": {"name": f"Remetente {i}", "email": f"remetente{i}@example.com"},
                "subject": f"Assunto de Teste {i}"
            })
        return {'status': 'success', 'data': {'message_count': count, 'messages': messages}}

    def get_message(self, email_name, message_id):
        time.sleep(0.3)
        body = ("Olá,\n\nEste é um corpo de e-mail de teste gerado pelo sistema de simulação.\n"
                "Ele serve para demonstrar como as mensagens serão exibidas na interface.\n\n"
                "Atenciosamente,\nO Simulador FireMail")
        return {'status': 'success', 'data': {'body': body}}


def load_emails():
    """Carrega os e-mails salvos do arquivo JSON."""
    if os.path.exists(EMAILS_FILE):
        with open(EMAILS_FILE, 'r', encoding='utf-8') as f:
            try: return json.load(f)
            except json.JSONDecodeError: return []
    return []

def save_emails(emails):
    """Salva a lista de e-mails no arquivo JSON."""
    with open(EMAILS_FILE, 'w', encoding='utf-8') as f:
        json.dump(emails, f, indent=4, ensure_ascii=False)

class EmailApp(tk.Tk):
    """Classe principal da aplicação de e-mail."""
    def __init__(self):
        super().__init__()
        self.title("FireMail - Gerenciador de E-mails Temporários")
        self.geometry("950x700")

        # --- ADICIONAR ÍCONE ---
        # Esta linha define o ícone da janela.
        # Certifique-se de ter um arquivo chamado "icone.ico" na mesma pasta.
        try:
            self.iconbitmap('icone.ico')
        except tk.TclError:
            print("Aviso: 'icone.ico' não encontrado. O ícone padrão será usado.")

        self.minsize(750, 550)
        self.configure(bg=BG_COLOR)

        self.font_bold = font.Font(family="Arial", size=12, weight="bold")
        self.font_normal = font.Font(family="Arial", size=10)
        self.font_small = font.Font(family="Arial", size=9, weight="bold")
        
        self.client = MockFireMailClient() if USE_MOCK_API else FireMailClient()
        self.emails = load_emails()
        self.connection_status = "Conectando..."

        self.setup_ui()
        self.populate_email_list()
        self.run_in_thread(self.fetch_and_set_connection_status)

    def setup_ui(self):
        """Configura a interface gráfica da aplicação."""
        main_frame = Frame(self, bg=BG_COLOR, padx=10, pady=10)
        main_frame.pack(fill="both", expand=True)
        
        # --- Frame Esquerdo ---
        left_frame = Frame(main_frame, width=320, bg=FRAME_COLOR, padx=15, pady=15)
        left_frame.pack(side="left", fill="y", padx=(0, 10))
        left_frame.pack_propagate(False)

        # --- Frame Direito ---
        right_frame = Frame(main_frame, bg=FRAME_COLOR, padx=15, pady=15)
        right_frame.pack(side="right", fill="both", expand=True)

        # --- Widgets do Frame Esquerdo ---
        Label(left_frame, text="Seu E-mail", font=self.font_bold, bg=FRAME_COLOR, fg=TEXT_COLOR).pack(pady=(0, 5), anchor='w')
        self.email_entry = Entry(left_frame, font=self.font_normal, bg=BG_COLOR, fg=TEXT_COLOR, relief="flat", insertbackground=TEXT_COLOR)
        self.email_entry.pack(fill="x", pady=(0, 10), ipady=8, padx=2)

        create_buttons_frame = Frame(left_frame, bg=FRAME_COLOR)
        create_buttons_frame.pack(fill="x", pady=2)
        
        HoverButton(create_buttons_frame, text="🪄 Gerar Aleatório", command=self.generate_random_email, relief="flat", bg=ACCENT_COLOR, fg=BG_COLOR, font=self.font_small, width=15, hover_color=HOVER_ACCENT_COLOR).pack(side="left", expand=True, padx=(0, 2), ipady=5)
        HoverButton(create_buttons_frame, text="✨ Criar Personalizado", command=self.create_custom_email, relief="flat", bg=SECONDARY_COLOR, fg=TEXT_COLOR, font=self.font_small, width=15, hover_color=HOVER_SECONDARY_COLOR).pack(side="left", expand=True, padx=(2, 0), ipady=5)

        HoverButton(left_frame, text="📋 Copiar E-mail", command=self.copy_to_clipboard, relief="flat", bg=SECONDARY_COLOR, fg=TEXT_COLOR, font=self.font_small, hover_color=HOVER_SECONDARY_COLOR).pack(fill="x", pady=2, ipady=5)
        HoverButton(left_frame, text="🗑️ Eliminar E-mail", command=self.delete_email, relief="flat", bg=DANGER_COLOR, fg=BG_COLOR, font=self.font_small, hover_color=HOVER_DANGER_COLOR).pack(fill="x", pady=2, ipady=5)
        
        Label(left_frame, text="E-mails Salvos", font=self.font_bold, bg=FRAME_COLOR, fg=TEXT_COLOR).pack(pady=(20, 5), anchor='w')
        self.email_listbox = Listbox(left_frame, bg=BG_COLOR, fg=TEXT_COLOR, relief="flat", selectbackground=ACCENT_COLOR, selectforeground=BG_COLOR, highlightthickness=0, activestyle="none", font=self.font_normal)
        self.email_listbox.pack(fill="both", expand=True, pady=(0, 5))
        self.email_listbox.bind("<<ListboxSelect>>", self.on_email_select)

        # --- Widgets do Frame Direito ---
        self.messages_text = Text(right_frame, wrap="word", state="disabled", padx=15, pady=15, relief="flat", bg=BG_COLOR, fg=TEXT_COLOR, font=self.font_normal, insertbackground=TEXT_COLOR)
        self.messages_text.pack(fill="both", expand=True)
        self.setup_message_tags()
        self.show_welcome_message()

        # --- Barra de Status ---
        self.status_bar = Label(self, text=self.connection_status, font=("Arial", 8), bg=FRAME_COLOR, fg=TEXT_COLOR, anchor='w', padx=10)
        self.status_bar.pack(side="bottom", fill="x")

    def setup_message_tags(self):
        self.messages_text.tag_configure("header", font=("Arial", 16, "bold"), foreground=ACCENT_COLOR, justify='center', spacing3=20)
        self.messages_text.tag_configure("label", font=self.font_bold, foreground=TEXT_COLOR)
        self.messages_text.tag_configure("separator", foreground="#45475a", justify='center')
        self.messages_text.tag_configure("info", foreground=PLACEHOLDER_COLOR, justify='center', font=self.font_small)
        self.messages_text.tag_configure("body", font=self.font_normal, foreground=TEXT_COLOR)
        self.messages_text.tag_configure("welcome_title", font=("Arial", 24, "bold"), foreground=TEXT_COLOR, justify='center', spacing3=10)
        self.messages_text.tag_configure("welcome_text", font=("Arial", 11), foreground=PLACEHOLDER_COLOR, justify='center', spacing3=20)

    def show_welcome_message(self):
        self.render_messages([
            ("\n\n\n\nBem-vindo ao FireMail\n", "welcome_title"),
            ("Selecione um e-mail na lista à esquerda ou\ngere um novo para começar a ver suas mensagens.", "welcome_text")
        ])

    def update_status(self, message):
        self.status_bar.config(text=message)
        self.update_idletasks()

    def fetch_and_set_connection_status(self):
        """Busca o IP público e atualiza a barra de status permanentemente."""
        try:
            ip = requests.get('https://api.ipify.org', timeout=5).text
            self.connection_status = f"Você está conectado com o IP: {ip}"
        except requests.exceptions.RequestException:
            self.connection_status = "Status da Conexão: Offline"
        self.after(0, self.update_status, self.connection_status)

    def run_in_thread(self, target_func, *args):
        thread = threading.Thread(target=target_func, args=args)
        thread.daemon = True
        thread.start()

    def generate_random_email(self):
        self.run_in_thread(self.create_email_task)

    def create_custom_email(self):
        username = simpledialog.askstring("E-mail Personalizado", "Digite o nome de usuário desejado (sem @...):", parent=self)
        if username: self.run_in_thread(self.create_email_task, username)

    def create_email_task(self, username=None):
        self.update_status(f"Criando e-mail {'personalizado' if username else 'aleatório'}...")
        try:
            result = self.client.create_email(username)
            if result.get('status') == 'success':
                email = result['data']['email']
                email_name = email.split('@')[0]
                self.email_entry.delete(0, tk.END); self.email_entry.insert(0, email)
                self.emails.append({'email': email, 'name': email_name}); save_emails(self.emails)
                self.populate_email_list()
                self.after(0, lambda: messagebox.showinfo("Sucesso", f"E-mail criado: {email}"))
            else:
                self.after(0, lambda: messagebox.showerror("Erro", result.get('message', 'Erro desconhecido.')))
        except requests.exceptions.HTTPError as e:
            error_message = f"Erro da API: {e.response.status_code}\n{e.response.text}"
            self.after(0, lambda: messagebox.showerror("Erro da API", error_message))
        except requests.exceptions.RequestException as e:
            error_message = f"Não foi possível conectar à API.\n\nDetalhes: {e}"
            self.after(0, lambda: messagebox.showerror("Erro de Conexão", error_message))
        finally:
            self.update_status(self.connection_status)

    def populate_email_list(self):
        self.email_listbox.delete(0, tk.END)
        for email_info in self.emails: self.email_listbox.insert(tk.END, email_info['email'])

    def on_email_select(self, event):
        if not self.email_listbox.curselection(): return
        selected_email = self.email_listbox.get(self.email_listbox.curselection()[0])
        self.email_entry.delete(0, tk.END); self.email_entry.insert(0, selected_email)
        self.render_messages([("A verificar a caixa de entrada... Por favor, aguarde.", "info")])
        self.run_in_thread(self.fetch_and_prepare_messages, selected_email)

    def fetch_and_prepare_messages(self, email):
        self.update_status(f"Buscando mensagens para {email}...")
        content_parts = []
        try:
            email_name = email.split('@')[0]
            messages_data = self.client.check_email(email_name)
            content_parts.append((f"Mensagens para {email}\n\n", "header"))
            if messages_data.get('status') == 'success' and messages_data.get('data', {}).get('message_count', 0) > 0:
                count = messages_data['data']['message_count']
                content_parts.append((f"Total de mensagens: {count}\n\n", "info"))
                for i, msg in enumerate(messages_data['data']['messages']):
                    if i > 0: content_parts.append(("\n" + "─"*60 + "\n\n", "separator"))
                    content_parts.append(("De: ", "label")); content_parts.append((f"{msg['from']['name']} <{msg['from']['email']}>\n", "body"))
                    content_parts.append(("Assunto: ", "label")); content_parts.append((f"{msg['subject']}\n", "body"))
                    full_msg = self.client.get_message(email_name, msg['id'])
                    if full_msg.get('status') == 'success':
                        content_parts.append(("\nConteúdo:\n", "label")); content_parts.append((f"{full_msg['data'].get('body', 'N/A')}\n", "body"))
                    else:
                        content_parts.append(("\nConteúdo:\n", "label")); content_parts.append(("Erro ao carregar o corpo.\n", "info"))
            else:
                content_parts.append(("Nenhuma nova mensagem encontrada.", "info"))
        except requests.exceptions.RequestException as e:
            error_message = f"Erro de conexão ao buscar mensagens: {e}"
            content_parts = [(error_message, "info")]
        except Exception as e:
            error_message = f"Ocorreu um erro inesperado: {type(e).__name__}"
            logging.error("Erro inesperado", exc_info=True)
            content_parts = [(error_message, "info")]
        finally:
            self.after(0, self.render_messages, content_parts)
            self.update_status(self.connection_status)

    def render_messages(self, content_parts):
        self.messages_text.config(state="normal")
        self.messages_text.delete("1.0", tk.END)
        for text, tag in content_parts: self.messages_text.insert(tk.END, text, tag)
        self.messages_text.config(state="disabled")

    def copy_to_clipboard(self):
        email = self.email_entry.get()
        if email:
            self.clipboard_clear(); self.clipboard_append(email)
            messagebox.showinfo("Copiado", "O endereço de e-mail foi copiado!")

    def delete_email(self):
        if not self.email_listbox.curselection():
            messagebox.showwarning("Atenção", "Selecione um e-mail da lista para eliminar.")
            return
        email_to_delete = self.email_listbox.get(self.email_listbox.curselection()[0])
        if messagebox.askyesno("Confirmar", f"Tem certeza que deseja eliminar {email_to_delete}?"):
            self.emails = [e for e in self.emails if e['email'] != email_to_delete]
            save_emails(self.emails); self.populate_email_list()
            self.email_entry.delete(0, tk.END)
            self.show_welcome_message()
            self.update_status(f"E-mail {email_to_delete} eliminado.")

if __name__ == '__main__':
    app = EmailApp()
    app.mainloop()