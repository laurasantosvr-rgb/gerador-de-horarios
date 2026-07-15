import streamlit as st
from datetime import date
from run_scheduler import gerar_horario

st.set_page_config(
    page_title="Gerador de Horários",
    layout="wide"
)

# ==========================================================
# CSS
# ==========================================================

st.markdown("""
<style>

#MainMenu {visibility:hidden;}
header {visibility:hidden;}
footer {visibility:hidden;}

.stApp{
    background-color:#D47A4D;
}

.block-container{
    max-width:1200px;
    padding-top:3rem;
}

/* Campos DD MM AAAA */
input{
    text-align:center !important;
    font-size:20px !important;
    border-radius:8px !important;
}

/* Botão */
.stButton > button{

    background:#2C1018;
    color:white;

    border:none;

    border-radius:10px;

    height:55px;

    font-size:22px;

    font-weight:bold;
}

.stButton > button:hover{

    background:#401821;

}

</style>
""", unsafe_allow_html=True)

# ==========================================================
# LAYOUT
# ==========================================================

col_logo, col_form = st.columns([1.6,1])

# ==========================================================
# LOGO
# ==========================================================

with col_logo:

    st.write("")
    st.write("")
    st.write("")
    st.write("")

    st.image("assets/logo.png", width=520)

# ==========================================================
# FORMULÁRIO
# ==========================================================

with col_form:

    # -------------------------
    # DATA DE INÍCIO
    # -------------------------

    st.markdown(
        "<h4 style='color:white;'>Data de Início</h4>",
        unsafe_allow_html=True
    )

    c1, c2, c3 = st.columns([1,1,2])

    with c1:
        dia_inicio = st.text_input(
            "",
            placeholder="DD",
            max_chars=2,
            key="di"
        )

    with c2:
        mes_inicio = st.text_input(
            "",
            placeholder="MM",
            max_chars=2,
            key="mi"
        )

    with c3:
        ano_inicio = st.text_input(
            "",
            placeholder="AAAA",
            max_chars=4,
            key="ai"
        )

    st.write("")

    # -------------------------
    # DATA DE FIM
    # -------------------------

    st.markdown(
        "<h4 style='color:white;'>Data de Fim</h4>",
        unsafe_allow_html=True
    )

    c1, c2, c3 = st.columns([1,1,2])

    with c1:
        dia_fim = st.text_input(
            "",
            placeholder="DD",
            max_chars=2,
            key="df"
        )

    with c2:
        mes_fim = st.text_input(
            "",
            placeholder="MM",
            max_chars=2,
            key="mf"
        )

    with c3:
        ano_fim = st.text_input(
            "",
            placeholder="AAAA",
            max_chars=4,
            key="af"
        )

    st.write("")

    # -------------------------
    # RESTRIÇÕES
    # -------------------------

    st.markdown(
        "<h4 style='color:white;'>Ficheiro de Restrições</h4>",
        unsafe_allow_html=True
    )

    restricoes = st.file_uploader(
        "",
        type=["xlsx"],
        label_visibility="collapsed",
        key="restricoes"
    )

    st.write("")

    # -------------------------
    # HORÁRIO ANTERIOR
    # -------------------------

    st.markdown(
        "<h4 style='color:white;'>Horário Anterior (Opcional)</h4>",
        unsafe_allow_html=True
    )

    horario_anterior = st.file_uploader(
        "",
        type=["xlsx"],
        label_visibility="collapsed",
        key="horario_anterior"
    )

    st.write("")
    st.write("")

    # -------------------------
    # BOTÃO
    # -------------------------

    gerar = st.button(
        "Gerar Horário",
        use_container_width=True
    )

# ==========================================================
# AÇÃO
# ==========================================================

if gerar:

    if restricoes is None:
        st.error("Selecione o ficheiro de restrições.")
        st.stop()

    try:

        data_inicio = date(
            int(ano_inicio),
            int(mes_inicio),
            int(dia_inicio)
        )

        data_fim = date(
            int(ano_fim),
            int(mes_fim),
            int(dia_fim)
        )

        with st.spinner("A gerar horário..."):

            resultado = gerar_horario(
                excel_file=restricoes,
                start_date=data_inicio,
                end_date=data_fim,
                previous_schedule_file=horario_anterior,
            )

        st.success("Horário gerado com sucesso!")

        with open(resultado, "rb") as f:

            nome_ficheiro = f"Horario_de_{data_inicio.strftime('%d-%m-%Y')}_a_{data_fim.strftime('%d-%m-%Y')}.xlsx"

            st.download_button(
                label="📥 Descarregar Excel",
                data=excel_bytes,
                file_name=nome_ficheiro,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

    except Exception as e:

        st.exception(e)
