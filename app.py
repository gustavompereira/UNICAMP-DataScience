from datetime import date, datetime
from pathlib import Path

import pandas as pd
import streamlit as st

CONVENIOS = ["Particular", "Unimed", "Bradesco Saúde", "SulAmérica", "Outro"]
COLUNAS = ["hora", "nome", "idade", "convenio", "prioridade", "motivo"]
ARQUIVO_CSV = Path(__file__).resolve().parent / "pacientes.csv"


def calcular_idade(data_nascimento: str) -> int:
    data_nascimento = data_nascimento.strip()
    try:
        nascimento = datetime.strptime(data_nascimento, "%d/%m/%Y").date()
    except ValueError as erro:
        raise ValueError(
            "Informe uma data válida no formato dd/mm/aaaa."
        ) from erro

    if nascimento.strftime("%d/%m/%Y") != data_nascimento:
        raise ValueError("Use exatamente o formato dd/mm/aaaa.")

    hoje = date.today()
    if nascimento > hoje:
        raise ValueError("A data de nascimento não pode ser futura.")

    return hoje.year - nascimento.year - (
        (hoje.month, hoje.day) < (nascimento.month, nascimento.day)
    )


st.set_page_config(page_title="Cadastro de Pacientes", layout="centered")
st.title("Cadastro de Pacientes")
st.write("Preencha os dados do paciente para registrar a chegada.")

if "pacientes" not in st.session_state:
    st.session_state.pacientes = pd.DataFrame(columns=COLUNAS)
if "ultima_idade" not in st.session_state:
    st.session_state.ultima_idade = None


with st.form("cadastro_paciente"):
    nome = st.text_input("Nome do paciente")
    data_nascimento = st.text_input(
        "Data de nascimento",
        placeholder="dd/mm/aaaa",
        help="Informe a data no formato dia/mês/ano.",
    )
    convenio = st.selectbox("Convênio", CONVENIOS)
    prioridade = st.slider(
        "Prioridade do atendimento (5 = urgente)",
        min_value=1,
        max_value=5,
        value=3,
        step=1,
    )
    motivo = st.text_area("Motivo da consulta / observações")
    enviado = st.form_submit_button("Cadastrar")

if enviado:
    nome = nome.strip()
    if not nome:
        st.error("Informe o nome do paciente.")
    else:
        try:
            idade = calcular_idade(data_nascimento)
        except ValueError as erro:
            st.error(str(erro))
        else:
            nova_linha = {
                "hora": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "nome": nome,
                "idade": idade,
                "convenio": convenio,
                "prioridade": prioridade,
                "motivo": motivo.strip(),
            }
            novo_paciente = pd.DataFrame([nova_linha], columns=COLUNAS)
            arquivo_tem_cabecalho = (
                ARQUIVO_CSV.exists() and ARQUIVO_CSV.stat().st_size > 0
            )
            novo_paciente.to_csv(
                ARQUIVO_CSV,
                mode="a",
                header=not arquivo_tem_cabecalho,
                index=False,
                encoding="utf-8",
            )
            st.session_state.pacientes = pd.concat(
                [st.session_state.pacientes, novo_paciente],
                ignore_index=True,
            )
            st.session_state.ultima_idade = idade
            st.success("Paciente cadastrado com sucesso!")

if st.session_state.ultima_idade is not None:
    st.write(f"Idade do paciente cadastrado: {st.session_state.ultima_idade} anos")

st.subheader("Últimos pacientes cadastrados")
st.dataframe(
    st.session_state.pacientes.tail(5),
    width="stretch",
    hide_index=True,
)

csv = st.session_state.pacientes.to_csv(index=False).encode("utf-8")
st.download_button(
    "Baixar CSV da sessão",
    data=csv,
    file_name="pacientes.csv",
    mime="text/csv",
    disabled=st.session_state.pacientes.empty,
)
