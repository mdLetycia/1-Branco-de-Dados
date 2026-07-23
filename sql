import tkinter as tk
from tkinter import messagebox
import mysql.connector


def conectar():
    return mysql.connector.connect(
        host="localhost",
        user="aluno",
        password="aluno",
        database="cadastro"
    )


def gravar():
    nome = entrada_nome.get()

    if nome == "":
        messagebox.showwarning("Aviso", "Digite um nome.")
        return

    try:
        conexao = conectar()
        cursor = conexao.cursor()

        sql = "INSERT INTO pessoas (nome) VALUES (%s)"
        valores = (nome,)
        cursor.execute(sql, valores)

        conexao.commit()

        cursor.close()
        conexao.close()

        messagebox.showinfo("Sucesso", "Nome gravado!")
        entrada_nome.delete(0, tk.END)

    except Exception as erro:
        messagebox.showerror("Erro", f"Erro de conexão:\n{erro}")


janela = tk.Tk()
janela.title("Cadastro")
janela.geometry("300x150")


tk.Label(janela, text="Nome").pack(pady=5)


entrada_nome = tk.Entry(janela, width=30)
entrada_nome.pack()


botao = tk.Button(
    janela,
    text="Gravar",
    command=gravar
)
botao.pack(pady=10)


janela.mainloop()
