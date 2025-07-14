import tkinter as tk
from tkinter import messagebox, simpledialog, Listbox, Frame, Label, Entry, Button, Text, Scrollbar
import requests
import time
import json
import os
import threading

EMAILS_FILE = 'emails.json'

class FireMailClient:
    def __init__(self):
        self.api_url = 'https://firemail.com.br/api'

    def create_email(self, username=None):
        endpoint = f'{self.api_url}/email/create'
        data = {'email': username} if username else {}
        response = requests.post(endpoint, json=data)
        response.raise_for_status()
        return response.json()

    def check_email(self, email_name):
        endpoint = f'{self.api_url}/email/check/{email_name}'
        response = requests.get(endpoint)
        response.raise_for_status()
        return response.json()

    def get_message(self, email_name, message_id):
        endpoint = f'{self.api_url}/email/message/{email_name}/{message_id}'
        response = requests.get(endpoint)
        response.raise_for_status()
        return response.json()

def load_emails():
    if os.path.exists(EMAILS_FILE):
        with open(EMAILS_FILE, 'r', encoding='utf-8') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []
    return []

def save_emails(emails):
    with open(EMAILS_FILE, 'w', encoding='utf-8') as f:
        json.dump(emails, f, indent=4, ensure_ascii=False)

class EmailApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("X - @akimright9 - Gestor de E-mail Temporário")
        self.geometry("800x600")
        self.minsize(600, 400)

        self.client = FireMailClient()
        self.emails = load_emails()

        left_frame = Frame(self, width=250, padx=10, pady=10)
        left_frame.pack(side="left", fill="y")
        left_frame.pack_propagate(False)

        right_frame = Frame(self, padx=10, pady=10)
        right_frame.pack(side="right", fill="both", expand=True)

        Label(left_frame, text="E-mail Gerado:", font=("Arial", 12, "bold")).pack(pady=(0, 5), anchor='w')
        
        self.email_entry = Entry(left_frame, font=("Arial", 10), width=35)
        self.email_entry.pack(fill="x", pady=(0, 5))

        Button(left_frame, text="Gerar Novo E-mail", command=self.generate_new_email).pack(fill="x", pady=2)
        Button(left_frame, text="Copiar E-mail", command=self.copy_to_clipboard).pack(fill="x", pady=2)
        Button(left_frame, text="Eliminar E-mail", bg="#ff4d4d", fg="white", command=self.delete_email).pack(fill="x", pady=2)
        
        Label(left_frame, text="E-mails Salvos:", font=("Arial", 12, "bold")).pack(pady=(10, 5), anchor='w')

        self.email_listbox = Listbox(left_frame)
        self.email_listbox.pack(fill="both", expand=True)
        self.email_listbox.bind("<<ListboxSelect>>", self.on_email_select)

        Label(right_frame, text="Caixa de Entrada", font=("Arial", 14, "bold")).pack()
        
        self.messages_text = Text(right_frame, wrap="word", state="disabled", padx=5, pady=5, relief="sunken", borderwidth=1)
        
        self.messages_text.tag_configure("header", font=("Arial", 12, "bold"), justify='center')
        self.messages_text.tag_configure("label", font=("Arial", 10, "bold"))
        self.messages_text.tag_configure("separator", foreground="gray", justify='center')
        self.messages_text.tag_configure("info", foreground="blue", justify='center', font=("Arial", 10, "italic"))

        scrollbar = Scrollbar(self.messages_text)
        self.messages_text.pack(fill="both", expand=True, pady=5)
        scrollbar.pack(side='right', fill='y')
        self.messages_text.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.messages_text.yview)
        
        self.populate_email_list()

    def run_in_thread(self, target_func, *args):
        thread = threading.Thread(target=target_func, args=args)
        thread.daemon = True
        thread.start()

    def generate_new_email(self):
        def task():
            try:
                result = self.client.create_email()
                if result.get('status') == 'success':
                    email = result['data']['email']
                    email_name = email.split('@')[0]
                    
                    self.email_entry.delete(0, tk.END)
                    self.email_entry.insert(0, email)
                    
                    self.emails.append({'email': email, 'name': email_name})
                    save_emails(self.emails)
                    self.populate_email_list()
                    
                    messagebox.showinfo("Sucesso", f"E-mail criado: {email}")
                else:
                    messagebox.showerror("Erro", result.get('message', 'Erro desconhecido ao criar e-mail.'))
            except requests.exceptions.RequestException as e:
                messagebox.showerror("Erro de Conexão", f"Não foi possível conectar à API: {e}")

        self.run_in_thread(task)

    def populate_email_list(self):
        self.email_listbox.delete(0, tk.END)
        for email_info in self.emails:
            self.email_listbox.insert(tk.END, email_info['email'])

    def on_email_select(self, event):
        selected_indices = self.email_listbox.curselection()
        if not selected_indices:
            return
        
        selected_index = selected_indices[0]
        selected_email = self.email_listbox.get(selected_index)
        
        self.email_entry.delete(0, tk.END)
        self.email_entry.insert(0, selected_email)
        
        self.render_messages([("A verificar a caixa de entrada... Por favor, aguarde.", "info")])
        self.run_in_thread(self.fetch_and_prepare_messages, selected_email)

    def fetch_and_prepare_messages(self, email):
        content_parts = []
        try:
            email_name = email.split('@')[0]
            messages_data = self.client.check_email(email_name)
            
            content_parts.append((f"--- Mensagens para {email} ---\n\n", "header"))
            
            if messages_data.get('status') == 'success' and messages_data.get('data', {}).get('message_count', 0) > 0:
                content_parts.append((f"Total de mensagens: {messages_data['data']['message_count']}\n\n", "info"))
                
                for i, msg_summary in enumerate(messages_data['data']['messages']):
                    if i > 0:
                         content_parts.append(("\n" + "="*60 + "\n\n", "separator"))

                    content_parts.append(("De: ", "label"))
                    content_parts.append((f"{msg_summary['from']['name']} <{msg_summary['from']['email']}>\n", None))
                    
                    content_parts.append(("Assunto: ", "label"))
                    content_parts.append((f"{msg_summary['subject']}\n", None))
                    
                    full_message = self.client.get_message(email_name, msg_summary['id'])
                    if full_message.get('status') == 'success':
                        body = full_message['data'].get('body', 'Corpo da mensagem não disponível.')
                        content_parts.append(("\nConteúdo:\n", "label"))
                        content_parts.append((f"{body}\n", None))
                    else:
                        content_parts.append(("\nConteúdo:\n", "label"))
                        content_parts.append(("Erro ao carregar o corpo da mensagem.\n", "info"))
            else:
                content_parts.append(("Nenhuma nova mensagem encontrada.", "info"))
            
        except requests.exceptions.RequestException as e:
            content_parts = [(f"Erro de conexão: {e}", "info")]
        except Exception as e:
            content_parts = [(f"Ocorreu um erro inesperado: {e}", "info")]
        
        self.after(0, self.render_messages, content_parts)

    def render_messages(self, content_parts):
        self.messages_text.config(state="normal")
        self.messages_text.delete("1.0", tk.END)
        
        for text, tag in content_parts:
            if tag:
                self.messages_text.insert(tk.END, text, tag)
            else:
                self.messages_text.insert(tk.END, text)
                
        self.messages_text.config(state="disabled")

    def copy_to_clipboard(self):
        email = self.email_entry.get()
        if email:
            self.clipboard_clear()
            self.clipboard_append(email)
            messagebox.showinfo("Copiado", "O endereço de e-mail foi copiado para a área de transferência.")

    def delete_email(self):
        selected_indices = self.email_listbox.curselection()
        if not selected_indices:
            messagebox.showwarning("Nenhum E-mail Selecionado", "Por favor, selecione um e-mail da lista para eliminar.")
            return

        selected_index = selected_indices[0]
        email_to_delete = self.email_listbox.get(selected_index)

        confirm = messagebox.askyesno("Confirmar Eliminação", f"Tem a certeza de que deseja eliminar o e-mail {email_to_delete}?\nEsta ação não pode ser desfeita.")

        if confirm:
            self.emails = [email for email in self.emails if email['email'] != email_to_delete]
            save_emails(self.emails)
            self.populate_email_list()
            
            self.email_entry.delete(0, tk.END)
            self.render_messages([("E-mail eliminado. Selecione outro e-mail ou gere um novo.", "info")])
            
            messagebox.showinfo("Sucesso", f"O e-mail {email_to_delete} foi eliminado.")

if __name__ == '__main__':
    app = EmailApp()
    app.mainloop()