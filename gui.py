import os
import subprocess
from tkinter import filedialog, messagebox

import customtkinter as ctk

import core

ESCALA = 1.5  # tamanho da interface: 1.0 = padrao, 2.0 = o dobro. Se ficar grande/pequeno demais, mexa so aqui.
COR_SELECIONADA = ("#3B8ED0", "#1F6AA5")  # mesmo azul padrao do tema, para destacar a sequencia aberta
COR_HOVER = ("gray75", "gray28")
COR_DICA = ("gray40", "gray60")

# (chave em core.MODOS, texto do botao)
OPCOES_MODO = (
    ("normal", "Normal (50x15 + 2×40x10)"),
    ("50x15", "Só 50x15"),
    ("40x10", "Só 40x10"),
    ("90x25", "Só 90x25"),
)

TEXTO_ATALHOS = (
    "Atalhos:  Ctrl+N nova  ·  Ctrl+1…9 trocar  ·  F2 renomear  ·  "
    "Ctrl+S salvar como  ·  Ctrl+Enter gerar  ·  Ctrl+Delete excluir"
)


def abrir_pasta(caminho_arquivo):
    """
    Abre a pasta que contem o arquivo gerado, no gerenciador de arquivos
    padrao do sistema.

    LINUX (atual): usa xdg-open na pasta.
    WINDOWS (quando trocar): troque o corpo desta funcao por
        os.startfile(pasta)
    """
    pasta = os.path.dirname(os.path.abspath(caminho_arquivo))
    try:
        subprocess.Popen(["xdg-open", pasta])
    except FileNotFoundError:
        pass


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("APTO Maker")
        # tamanho base 960x600, mas nunca maior que a tela (ja contando a escala)
        largura = min(1000, int(self.winfo_screenwidth() * 0.92 / ESCALA))
        altura = min(600, int(self.winfo_screenheight() * 0.88 / ESCALA))
        self.geometry(f"{largura}x{altura}")
        self.minsize(940, 440)  # menor que isso a linha dos 4 radios fica cortada

        # cada sequencia e um dict: nome, modo, caixa (textbox propria), linha, botao, excluir
        self.sequencias = []
        self.atual = None  # a sequencia que aparece na area de texto
        self.caminho_saida = None

        self._montar_janela()
        self._registrar_atalhos()
        self.nova_sequencia(foco_no_nome=False)  # comeca ja com uma sequencia

    # ------------------------------------------------------------ janela
    def _montar_janela(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # lateral: lista de sequencias (a ordem daqui = ordem das linhas no DXF)
        barra = ctk.CTkFrame(self, width=270)
        barra.grid(row=0, column=0, sticky="ns", padx=(15, 5), pady=15)
        barra.grid_propagate(False)
        barra.grid_rowconfigure(0, weight=1)
        barra.grid_columnconfigure(0, weight=1)

        self.lista = ctk.CTkScrollableFrame(barra, label_text="Sequências")
        self.lista.grid(row=0, column=0, sticky="nsew", padx=8, pady=(8, 4))

        ctk.CTkButton(barra, text="+ Nova sequência", command=self.nova_sequencia).grid(
            row=1, column=0, sticky="ew", padx=8, pady=(4, 8)
        )

        # painel direito: nome + texto da sequencia aberta
        painel = ctk.CTkFrame(self, fg_color="transparent")
        painel.grid(row=0, column=1, sticky="nsew", padx=(5, 15), pady=15)
        painel.grid_columnconfigure(0, weight=1)
        painel.grid_rowconfigure(4, weight=1)
        painel.bind("<Configure>", self._ajustar_quebra)  # textos longos quebram na largura do painel

        ctk.CTkLabel(painel, text="Nome da sequência:").grid(row=0, column=0, sticky="w")
        self.entrada_nome = ctk.CTkEntry(painel)
        self.entrada_nome.grid(row=1, column=0, sticky="ew", pady=(2, 10))
        self.entrada_nome.bind("<Return>", self._enter_no_nome)
        self.entrada_nome.bind("<FocusOut>", lambda e: self.confirmar_nome())

        # modo de desenho da sequencia aberta (cada sequencia guarda o seu)
        self.var_modo = ctk.StringVar(value=core.MODO_PADRAO)
        modos = ctk.CTkFrame(painel, fg_color="transparent")
        modos.grid(row=2, column=0, sticky="w", pady=(0, 10))
        ctk.CTkLabel(modos, text="Desenhar:").pack(side="left", padx=(0, 12))
        for valor, texto in OPCOES_MODO:
            ctk.CTkRadioButton(
                modos, text=texto, variable=self.var_modo, value=valor, command=self._mudar_modo
            ).pack(side="left", padx=(0, 10))

        ctk.CTkLabel(painel, text="Placas (uma por linha):").grid(row=3, column=0, sticky="w")
        self.area_texto = ctk.CTkFrame(painel, fg_color="transparent")
        self.area_texto.grid(row=4, column=0, sticky="nsew", pady=(2, 0))
        self.area_texto.grid_rowconfigure(0, weight=1)
        self.area_texto.grid_columnconfigure(0, weight=1)

        self.label_caminho = ctk.CTkLabel(painel, text="Nenhum arquivo selecionado ainda.", justify="left")
        self.label_caminho.grid(row=5, column=0, sticky="w", pady=(10, 0))

        botoes = ctk.CTkFrame(painel, fg_color="transparent")
        botoes.grid(row=6, column=0, sticky="w", pady=10)
        ctk.CTkButton(botoes, text="Salvar como...", command=self.escolher_caminho).pack(side="left", padx=(0, 10))
        ctk.CTkButton(botoes, text="Gerar DXF", command=self.gerar).pack(side="left", padx=(0, 10))
        self.var_combinado = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            botoes, text="Faixa TODAS no topo", variable=self.var_combinado
        ).pack(side="left")

        self.label_status = ctk.CTkLabel(painel, text="", justify="left")
        self.label_status.grid(row=7, column=0, sticky="w")

        self.label_dicas = ctk.CTkLabel(
            painel, text=TEXTO_ATALHOS, text_color=COR_DICA, justify="left",
            font=ctk.CTkFont(size=11),
        )
        self.label_dicas.grid(row=8, column=0, sticky="w", pady=(8, 0))

    def _ajustar_quebra(self, evento):
        # a largura do evento e em pixels reais; o wraplength do label e na escala da interface
        largura = self.label_status._reverse_widget_scaling(evento.width)
        for rotulo in (self.label_caminho, self.label_status, self.label_dicas):
            rotulo.configure(wraplength=max(200, int(largura) - 10))

    def _status(self, texto, cor):
        self.label_status.configure(text=texto, text_color=cor)

    def _mudar_modo(self):
        # o clique no radio grava o modo na sequencia aberta
        if self.atual is not None:
            self.atual["modo"] = self.var_modo.get()
            self.atual["caixa"].focus()  # devolve o foco pra caixa, pra continuar digitando

    # ----------------------------------------------------------- atalhos
    @staticmethod
    def _como_atalho(funcao):
        def tratador(evento=None):
            funcao()
            return "break"  # impede que o Tk execute tambem o atalho padrao dele (ex: Ctrl+N = descer linha)
        return tratador

    def _registrar_atalhos(self):
        """
        Atalhos que valem com o foco em qualquer lugar da janela. Nos campos de
        texto (caixas e nome) eles tambem sao ligados direto no widget, porque
        la o Tk ja usa varias dessas teclas pra mover o cursor / editar.
        """
        self._atalhos = []
        for tecla in "nN":  # as duas, pra funcionar com Caps Lock ligado
            self._atalhos.append((f"<Control-Key-{tecla}>", self.nova_sequencia))
        for tecla in "sS":
            self._atalhos.append((f"<Control-Key-{tecla}>", self.escolher_caminho))
        self._atalhos.append(("<Control-Return>", self.gerar))
        self._atalhos.append(("<Control-KP_Enter>", self.gerar))  # Enter do teclado numerico
        self._atalhos.append(("<Control-Delete>", self.excluir_atual))
        self._atalhos.append(("<F2>", self.editar_nome))
        for n in range(1, 10):
            self._atalhos.append((f"<Control-Key-{n}>", lambda n=n: self.ir_para(n)))

        for sequencia, funcao in self._atalhos:
            self.bind_all(sequencia, self._como_atalho(funcao))

        self._instalar_atalhos(self.entrada_nome)
        for tecla in "aA":  # Ctrl+A = selecionar tudo (no Linux o Tk usaria "inicio da linha")
            self.entrada_nome.bind(f"<Control-Key-{tecla}>", self._selecionar_tudo_nome)

    def _instalar_atalhos(self, campo):
        for sequencia, funcao in self._atalhos:
            campo.bind(sequencia, self._como_atalho(funcao))

    def _selecionar_tudo_texto(self, caixa):
        interno = caixa._textbox
        interno.tag_add("sel", "1.0", "end-1c")
        interno.mark_set("insert", "end-1c")
        return "break"

    def _selecionar_tudo_nome(self, evento=None):
        self.entrada_nome.select_range(0, "end")
        self.entrada_nome.icursor("end")
        return "break"

    def ir_para(self, numero):
        if numero <= len(self.sequencias):
            self.selecionar(self.sequencias[numero - 1])

    def editar_nome(self):
        self.entrada_nome.focus()
        self.entrada_nome.select_range(0, "end")

    def excluir_atual(self):
        if self.atual is not None:
            self.excluir_sequencia(self.atual)

    # ------------------------------------------------------- sequencias
    def _nome_em_uso(self, nome, ignorar=None):
        return any(s is not ignorar and s["nome"].lower() == nome.lower() for s in self.sequencias)

    def _nome_padrao(self):
        n = len(self.sequencias) + 1
        while self._nome_em_uso(f"Sequência {n}"):
            n += 1
        return f"Sequência {n}"

    def nova_sequencia(self, foco_no_nome=True):
        seq = self._criar_sequencia(self._nome_padrao())
        self.selecionar(seq)
        if foco_no_nome:  # ja deixa o nome selecionado pra voce digitar por cima
            self.entrada_nome.focus()
            self.entrada_nome.select_range(0, "end")

    def _criar_sequencia(self, nome):
        caixa = ctk.CTkTextbox(self.area_texto)  # so e colocada na tela quando selecionada
        linha = ctk.CTkFrame(self.lista, fg_color="transparent")
        linha.pack(fill="x", pady=2)

        seq = {"nome": nome, "modo": core.MODO_PADRAO, "caixa": caixa, "linha": linha}
        seq["botao"] = ctk.CTkButton(
            linha, anchor="w", fg_color="transparent", hover_color=COR_HOVER,
            command=lambda: self.selecionar(seq),
        )
        seq["botao"].pack(side="left", fill="x", expand=True)
        seq["excluir"] = ctk.CTkButton(
            linha, text="✕", width=30, fg_color="transparent", hover_color=COR_HOVER,
            command=lambda: self.excluir_sequencia(seq),
        )
        seq["excluir"].pack(side="left", padx=(4, 0))

        caixa.bind("<KeyRelease>", lambda e: self._atualizar_botao(seq))  # mantem a contagem em dia
        self._instalar_atalhos(caixa)
        for tecla in "aA":
            caixa.bind(f"<Control-Key-{tecla}>", lambda e, c=caixa: self._selecionar_tudo_texto(c))

        self.sequencias.append(seq)
        self._atualizar_botao(seq)
        self._atualizar_botoes_excluir()
        return seq

    def _atualizar_botao(self, seq):
        n = core.contar_placas(seq["caixa"].get("1.0", "end"))
        seq["botao"].configure(text=f"{seq['nome']}  ({n})")

    def _atualizar_botoes_excluir(self):
        # nunca deixa apagar a ultima sequencia que sobrou
        estado = "normal" if len(self.sequencias) > 1 else "disabled"
        for s in self.sequencias:
            s["excluir"].configure(state=estado)

    def selecionar(self, seq):
        self.confirmar_nome()  # grava um nome que ainda estava sendo editado na sequencia anterior
        if self.atual is not None and self.atual is not seq:
            self.atual["caixa"].grid_remove()  # esconde, o texto continua guardado nela
        self.atual = seq
        seq["caixa"].grid(row=0, column=0, sticky="nsew")

        self.entrada_nome.delete(0, "end")
        self.entrada_nome.insert(0, seq["nome"])
        self.var_modo.set(seq["modo"])  # os radios mostram o modo desta sequencia
        for s in self.sequencias:
            s["botao"].configure(fg_color=COR_SELECIONADA if s is seq else "transparent")
        seq["caixa"].focus()

    def confirmar_nome(self):
        seq = self.atual
        if seq is None:
            return
        novo = self.entrada_nome.get().strip()
        if novo == seq["nome"]:
            return

        if not novo:
            self._status("O nome da sequência não pode ficar vazio.", "orange")
        elif self._nome_em_uso(novo, ignorar=seq):
            self._status(f'Já existe uma sequência chamada "{novo}".', "orange")
        else:
            seq["nome"] = novo
            self._atualizar_botao(seq)
            return

        # nome recusado: devolve o campo para o ultimo nome valido
        self.entrada_nome.delete(0, "end")
        self.entrada_nome.insert(0, seq["nome"])

    def _enter_no_nome(self, evento=None):
        self.confirmar_nome()
        if self.atual is not None:
            self.atual["caixa"].focus()

    def excluir_sequencia(self, seq):
        if len(self.sequencias) <= 1:
            self._status("A última sequência não pode ser excluída.", "orange")
            return
        if seq["caixa"].get("1.0", "end").strip():
            # default="no": se apertar Enter sem pensar, nao apaga
            if not messagebox.askyesno(
                "Excluir sequência", f'Excluir "{seq["nome"]}" e o texto dela?', default="no"
            ):
                return

        posicao = self.sequencias.index(seq)
        self.sequencias.remove(seq)
        seq["caixa"].destroy()
        seq["linha"].destroy()

        if self.atual is seq:
            self.atual = None
            self.selecionar(self.sequencias[min(posicao, len(self.sequencias) - 1)])
        self._atualizar_botoes_excluir()

    # ---------------------------------------------------- salvar / gerar
    def escolher_caminho(self):
        caminho = filedialog.asksaveasfilename(
            defaultextension=".dxf",
            filetypes=[("Arquivo DXF", "*.dxf")],
            title="Salvar DXF como...",
        )
        if caminho:  # vazio se o usuario cancelar o dialogo
            self.caminho_saida = caminho
            self.label_caminho.configure(text=caminho)

    def gerar(self):
        self.confirmar_nome()  # garante que um nome em edicao entre no arquivo
        sequencias = [(s["nome"], s["caixa"].get("1.0", "end"), s["modo"]) for s in self.sequencias]

        if not any(core.contar_placas(texto) for _, texto, _ in sequencias):
            self._status("Digite pelo menos uma linha de texto primeiro.", "orange")
            return

        if not self.caminho_saida:
            self._status("Escolha onde salvar antes de gerar.", "orange")
            return

        try:
            r = core.gerar_dxf(sequencias, self.caminho_saida, combinado=self.var_combinado.get())
        except Exception as e:
            self._status(f"Erro: {e}", "red")
            return

        msg = (
            f"OK: {r['sequencias']} sequência(s), {r['total']} placas, "
            f"{r['folhas']} folha(s) -> {r['caminho']}"
        )
        if r["folhas_combinadas"]:
            msg += f"\nFaixa TODAS no topo: {r['folhas_combinadas']} folha(s)"
        if r["puladas"]:
            msg += f"\nSem texto, ficaram de fora: {', '.join(r['puladas'])}"
        self._status(msg, "green")
        abrir_pasta(r["caminho"])


def iniciar():
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    ctk.set_widget_scaling(ESCALA)  # aumenta fontes, botoes e campos juntos
    ctk.set_window_scaling(ESCALA)  # aumenta a janela na mesma proporcao
    App().mainloop()


if __name__ == "__main__":
    iniciar()
