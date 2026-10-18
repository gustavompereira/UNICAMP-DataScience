from datetime import date, datetime
from pathlib import Path

import gradio as gr
import pandas as pd

ARQUIVO_CSV = Path(__file__).resolve().parent / "pacientes.csv"
CONVENIOS = ["Particular", "Unimed", "Bradesco Saúde", "SulAmérica", "Outro"]
COLUNAS = ["hora", "nome", "idade", "convenio", "prioridade", "motivo"]


def carregar_ultimos_pacientes() -> pd.DataFrame:
    if not ARQUIVO_CSV.exists() or ARQUIVO_CSV.stat().st_size == 0:
        return pd.DataFrame(columns=COLUNAS)

    return pd.read_csv(ARQUIVO_CSV).tail(5)


def calcular_idade(data_nascimento: str) -> int:
    try:
        nascimento = datetime.strptime(data_nascimento.strip(), "%d/%m/%Y").date()
    except ValueError as erro:
        raise ValueError("Informe uma data válida no formato dd/mm/aaaa.") from erro

    if nascimento.strftime("%d/%m/%Y") != data_nascimento.strip():
        raise ValueError("Use exatamente o formato dd/mm/aaaa.")

    hoje = date.today()
    if nascimento > hoje:
        raise ValueError("A data de nascimento não pode ser futura.")

    return hoje.year - nascimento.year - (
        (hoje.month, hoje.day) < (nascimento.month, nascimento.day)
    )


def exibir_idade(data_nascimento: str | None) -> str:
    if not (data_nascimento or "").strip():
        return ""

    try:
        return f"{calcular_idade(data_nascimento)} anos"
    except ValueError:
        return ""


def cadastrar_paciente(
    nome: str | None,
    data_nascimento: str | None,
    convenio: str | None,
    prioridade: int | float | None,
    motivo: str | None,
) -> tuple[str, str, pd.DataFrame]:
    nome = (nome or "").strip()
    if not nome:
        raise gr.Error("Informe o nome do paciente.")
    try:
        idade = calcular_idade(data_nascimento or "")
    except ValueError as erro:
        raise gr.Error(str(erro)) from erro
    if convenio not in CONVENIOS:
        raise gr.Error("Selecione um convênio válido.")
    if (
        prioridade is None
        or not float(prioridade).is_integer()
        or not 1 <= prioridade <= 5
    ):
        raise gr.Error("A prioridade deve ser um número inteiro entre 1 e 5.")

    linha = {
        "hora": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "nome": nome,
        "idade": int(idade),
        "convenio": convenio,
        "prioridade": int(prioridade),
        "motivo": (motivo or "").strip(),
    }
    novo = pd.DataFrame([linha], columns=COLUNAS)
    arquivo_tem_cabecalho = ARQUIVO_CSV.exists() and ARQUIVO_CSV.stat().st_size > 0
    novo.to_csv(
        ARQUIVO_CSV,
        mode="a",
        header=not arquivo_tem_cabecalho,
        index=False,
        encoding="utf-8",
    )

    return (
        "Paciente cadastrado com sucesso!",
        f"{idade} anos",
        carregar_ultimos_pacientes(),
    )


with gr.Blocks(title="Cadastro de Pacientes") as demo:
    gr.Markdown("# Cadastro de Pacientes")
    gr.Markdown("Preencha os dados do paciente para registrar a chegada.")

    nome = gr.Textbox(label="Nome do paciente", placeholder="Nome completo")
    data_nascimento = gr.Textbox(
        label="Data de nascimento",
        placeholder="dd/mm/aaaa",
        info="Digite a data no formato dia/mês/ano.",
    )
    idade = gr.Textbox(label="Idade", interactive=False)
    convenio = gr.Dropdown(
        choices=CONVENIOS,
        label="Convênio",
        value=None,
    )
    prioridade = gr.Slider(
        minimum=1,
        maximum=5,
        step=1,
        value=3,
        label="Prioridade do atendimento (5 = urgente)",
    )
    motivo = gr.Textbox(
        label="Motivo da consulta / observações",
        lines=3,
        placeholder="Descreva brevemente o motivo da consulta",
    )
    botao = gr.Button("Cadastrar", variant="primary")
    saida_msg = gr.Textbox(label="Status", interactive=False)
    tabela = gr.Dataframe(
        value=carregar_ultimos_pacientes(),
        headers=COLUNAS,
        label="Últimos pacientes cadastrados",
        interactive=False,
    )

    data_nascimento.change(
        fn=exibir_idade,
        inputs=data_nascimento,
        outputs=idade,
    )
    botao.click(
        fn=cadastrar_paciente,
        inputs=[nome, data_nascimento, convenio, prioridade, motivo],
        outputs=[saida_msg, idade, tabela],
    )


if __name__ == "__main__":
    demo.launch()
