import streamlit as st
import pandas as pd
from datetime import datetime
import os
import pytz

# 1. Configuração da página
st.set_page_config(
    page_title="App Poste - E2S",
    page_icon="👷",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# 2. CSS Personalizado
style_css = """
<style>
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    
    .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
        padding-left: 0.8rem;
        padding-right: 0.8rem;
    }
    
    div.stButton > button {
        width: 100%;
        height: 70px !important;
        font-size: 18px !important;
        font-weight: bold !important;
        border-radius: 12px !important;
        margin-bottom: 10px;
        background-color: #0F52BA;
        color: white;
        border: none;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        transition: transform 0.1s;
    }
    div.stButton > button:active {
        transform: scale(0.95);
    }
    
    /* Botão de Cancelar no Pop-up com cor diferente (Cinzento) */
    .btn-cancelar button {
        background-color: #6c757d !important;
    }
    
    /* Botão de Terminar com cor vermelha para destaque */
    .btn-terminar button {
        background-color: #dc3545 !important; 
    }
</style>
"""
st.markdown(style_css, unsafe_allow_html=True)

FILE_NAME = "registos_campo.csv"

# 3. Inicialização do Estado (Memória da App)
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'pagina' not in st.session_state:
    st.session_state.pagina = 'login'
    
if 'id_trabalhador' not in st.session_state:
    st.session_state.id_trabalhador = ""
if 'id_sessao' not in st.session_state:
    st.session_state.id_sessao = ""
    
if 'historico' not in st.session_state:
    st.session_state.historico = []
if 'sessao_selecionada' not in st.session_state:
    st.session_state.sessao_selecionada = ""

if 'chegada_registada' not in st.session_state:
    st.session_state.chegada_registada = False
if 'menu_secundario' not in st.session_state:
    st.session_state.menu_secundario = None
if 'altura_memoria' not in st.session_state:
    st.session_state.altura_memoria = 0
if 'trabalho_terminado' not in st.session_state:
    st.session_state.trabalho_terminado = False

def registar_evento(atividade, altura):
    tz_pt = pytz.timezone('Europe/Lisbon')
    agora = datetime.now(tz_pt) # Captura a hora em Lisboa
    local = "Solo" if altura == 0 else "Poste"
    
    # === CORREÇÃO: Contagem de N separada por Sessão ===
    num_registo = 1
    if os.path.exists(FILE_NAME):
        try:
            df_temp = pd.read_csv(FILE_NAME, encoding='utf-8-sig', sep=';')
            if not df_temp.empty:
                # Filtra a tabela para ver apenas os registos da SESSÃO ATUAL
                df_sessao_atual = df_temp[df_temp['Sessão'] == st.session_state.id_sessao]
                
                # Se já existirem registos para esta sessão, pega no maior "N" e soma 1
                if not df_sessao_atual.empty and 'N' in df_sessao_atual.columns:
                    num_registo = int(df_sessao_atual['N'].max()) + 1
        except:
            pass
    # =======================================================
            
    novo_registo = {
        "N": num_registo, 
        "Sessão": st.session_state.id_sessao, 
        "Data": agora.strftime("%d/%m/%Y"),
        "Trabalhador/Poste": st.session_state.id_trabalhador,
        "Hora": agora.strftime("%H:%M:%S"),
        "Atividade": atividade,
        "Local": local,
        "Altura (m)": altura
    }
    
    df_novo = pd.DataFrame([novo_registo])
    
    if os.path.exists(FILE_NAME):
        df_novo.to_csv(FILE_NAME, mode='a', header=False, index=False, encoding='utf-8-sig', sep=';')
    else:
        df_novo.to_csv(FILE_NAME, mode='w', header=True, index=False, encoding='utf-8-sig', sep=';')
    
    st.session_state.historico.insert(0, novo_registo)

# ==========================================
# 4. GESTÃO DE PÁGINAS (Navegação)
# ==========================================

if not st.session_state.logged_in:
    st.title("🔐 Login")
    utilizador = st.text_input("Utilizador")
    password = st.text_input("Palavra-passe", type="password")
    
    if st.button("Entrar"):
        if utilizador == "tbio" and password == "tbio":
            st.session_state.logged_in = True
            st.session_state.pagina = 'menu'
            st.rerun()
        else:
            st.error("Utilizador ou Palavra-passe incorretos!")

elif st.session_state.pagina == 'menu':
    st.title("🏠 Menu Principal")
    if st.button("📝 Registar Observação"):
        st.session_state.pagina = 'definir_trabalhador'
        st.rerun()
    if st.button("📂 Ver Registos / Download"):
        st.session_state.pagina = 'ver_registos'
        st.rerun()
    st.write("---")
    if st.button("🚪 Terminar Sessão (Logout)"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

elif st.session_state.pagina == 'definir_trabalhador':
    st.title("👤 Identificação")
    hoje = datetime.now().strftime("%d/%m/%Y")
    ultimo_trab_csv = ""
    ultima_sessao_csv = ""
    
    if os.path.exists(FILE_NAME):
        try:
            df_check = pd.read_csv(FILE_NAME, encoding='utf-8-sig', sep=';')
            df_check['Trabalhador/Poste'] = df_check['Trabalhador/Poste'].astype(str)
            if not df_check.empty:
                df_hoje = df_check[df_check['Data'] == hoje]
                if not df_hoje.empty:
                    ultima_linha = df_hoje.iloc[-1]
                    ultimo_trab_csv = str(ultima_linha['Trabalhador/Poste'])
                    ultima_sessao_csv = str(ultima_linha['Sessão'])
        except:
            pass
    
    if ultima_sessao_csv != "":
        st.subheader("Retomar último trabalho?")
        if st.button(f"▶️ Continuar: {ultima_sessao_csv.split('] ')[-1]}"):
            st.session_state.id_trabalhador = ultimo_trab_csv
            st.session_state.id_sessao = ultima_sessao_csv
            df_sessao = df_check[df_check['Sessão'] == ultima_sessao_csv]
            st.session_state.historico = df_sessao.tail(5).to_dict('records')[::-1]
            
            st.session_state.chegada_registada = True 
            st.session_state.menu_secundario = None
            st.session_state.trabalho_terminado = False 
            st.session_state.pagina = 'painel_registo'
            st.rerun()
        st.write("---")
        st.subheader("Ou iniciar nova observação:")
    else:
        st.write("Quem vai observar agora?")
    
    id_input = st.text_input("ID do Trabalhador / Código do Poste")
    
    if st.button("Começar Novo Registo"):
        id_limpo = id_input.strip()
        if id_limpo != "":
            st.session_state.id_trabalhador = id_limpo
            num_registo = 1
            if os.path.exists(FILE_NAME):
                try:
                    df_check = pd.read_csv(FILE_NAME, encoding='utf-8-sig', sep=';')
                    df_check['Trabalhador/Poste'] = df_check['Trabalhador/Poste'].astype(str)
                    df_hoje_trab = df_check[(df_check['Data'] == hoje) & (df_check['Trabalhador/Poste'] == id_limpo)]
                    if not df_hoje_trab.empty:
                        num_registo = df_hoje_trab['Sessão'].nunique() + 1
                except:
                    pass
            
            nova_sessao_str = f"[{hoje}] {id_limpo}_{num_registo}"
            st.session_state.id_sessao = nova_sessao_str
            st.session_state.historico = [] 
            
            st.session_state.chegada_registada = False
            st.session_state.menu_secundario = None
            st.session_state.altura_memoria = 0 
            st.session_state.trabalho_terminado = False 
            
            st.session_state.pagina = 'painel_registo'
            st.rerun()
        else:
            st.warning("Por favor, preencha o ID antes de avançar.")
            
    st.write("---")
    if st.button("⬅️ Voltar ao Menu"):
        st.session_state.pagina = 'menu'
        st.rerun()

elif st.session_state.pagina == 'painel_registo':
    st.subheader(f"👷 A observar: {st.session_state.id_sessao.split('] ')[-1]}")
    
    altura_atual = st.number_input("Altura Atual (m)", min_value=0, value=st.session_state.altura_memoria, step=1)
    st.session_state.altura_memoria = altura_atual
    
    st.write("---")

    if st.session_state.trabalho_terminado:
        st.success("✅ Fim de trabalho registado com sucesso. Pode concluir a observação no botão abaixo.")

    elif not st.session_state.chegada_registada:
        st.info("Para desbloquear as tarefas, confirme o início.")
        if st.button("📍 Chegada ao Poste"):
            registar_evento("Chegada ao Poste", altura_atual)
            st.session_state.chegada_registada = True
            st.toast("📍 Chegada Registada", icon="✅")
            st.rerun()

    elif st.session_state.menu_secundario == "Mudar Altura":
        st.subheader("📏 Qual é a nova altura?")
        st.write("Introduza a nova altura a que o trabalhador ficou após o movimento:")
        
        nova_altura = st.number_input("Nova Altura (m)", min_value=0, value=altura_atual, step=1, key="input_nova_altura")
        
        if st.button("✅ Confirmar Nova Altura"):
            st.session_state.altura_memoria = nova_altura
            st.session_state.menu_secundario = None
            st.rerun()

    elif st.session_state.menu_secundario is not None:
        acao_principal = st.session_state.menu_secundario
        st.subheader(f"👉 Detalhe para: {acao_principal}")
        
        col_op1, col_op2 = st.columns(2)
        with col_op1:
            if st.button("Cantoneira"):
                registar_evento(f"{acao_principal} (Cantoneira)", altura_atual)
                st.session_state.menu_secundario = None
                st.toast(f"✅ {acao_principal} registado", icon="✅")
                st.rerun()
            if st.button("Troço"):
                registar_evento(f"{acao_principal} (Troço)", altura_atual)
                st.session_state.menu_secundario = None
                st.toast(f"✅ {acao_principal} registado", icon="✅")
                st.rerun()
                
        with col_op2:
            if st.button("Outro"):
                registar_evento(f"{acao_principal} (Outro)", altura_atual)
                st.session_state.menu_secundario = None
                st.toast(f"✅ {acao_principal} registado", icon="✅")
                st.rerun()
                
            st.markdown('<div class="btn-cancelar">', unsafe_allow_html=True)
            if st.button("🔙 Cancelar"):
                st.session_state.menu_secundario = None
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

    else:
        col1, col2 = st.columns(2)

        with col1:
            if st.button("🔧 Apertar Parafusos"):
                registar_evento("Apertar Parafusos", altura_atual)
                st.toast("🔧 Registado", icon="✅")
                
            if st.button("🏗️ Receber/Alinhar"):
                st.session_state.menu_secundario = "Receber/Alinhar"
                st.rerun()
                
            if st.button("⬆️ Subir"):
                registar_evento("Subir", altura_atual)
                st.session_state.menu_secundario = "Mudar Altura"
                st.toast("⬆️ Subir registado", icon="✅")
                st.rerun()
                
            if st.button("🚶 Deslocamento Lat."):
                registar_evento("Deslocamento Lateral", altura_atual)
                st.toast("🚶 Registado", icon="✅")

        with col2:
            if st.button("🛑 Parado"):
                registar_evento("Parado", altura_atual)
                st.toast("🛑 Registado", icon="✅")
                
            if st.button("🔩 Fixar"):
                st.session_state.menu_secundario = "Fixar"
                st.rerun()
                
            if st.button("⬇️ Descer"):
                registar_evento("Descer", altura_atual)
                st.session_state.menu_secundario = "Mudar Altura"
                st.toast("⬇️ Descer registado", icon="✅")
                st.rerun()
                
            if st.button("🥪 Pausa Almoço"):
                registar_evento("Pausa Almoço", altura_atual)
                st.toast("🥪 Registado", icon="✅")

        col_fim1, col_fim2 = st.columns(2)
        with col_fim1:
            if st.button("📋 Outra Tarefa"):
                registar_evento("Outra Tarefa", altura_atual)
                st.toast("📋 Registado", icon="✅")
                
        with col_fim2:
            st.markdown('<div class="btn-terminar">', unsafe_allow_html=True)
            if st.button("🏁 Terminar"):
                registar_evento("Fim de trabalho", altura_atual)
                st.session_state.trabalho_terminado = True
                st.toast("🏁 Fim de trabalho registado", icon="✅")
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

    st.write("---")
    
    st.subheader("Últimos Registos desta Sessão")
    if st.session_state.historico:
        df_view = pd.DataFrame(st.session_state.historico)
        st.dataframe(df_view[["N", "Hora", "Atividade", "Local", "Altura (m)"]].head(5), use_container_width=True, hide_index=True)
    else:
        st.info("Ainda não registou nada nesta observação.")

    st.write("---")
    if st.button("⏹️ Concluir"):
        st.session_state.id_trabalhador = ""
        st.session_state.trabalho_terminado = False  
        st.session_state.pagina = 'menu'
        st.rerun()

elif st.session_state.pagina == 'ver_registos':
    st.title("📂 Escolher Registo")
    
    if os.path.exists(FILE_NAME):
        try:
            df = pd.read_csv(FILE_NAME, encoding='utf-8-sig', sep=';')
            if df.empty:
                st.info("Ainda não existem registos guardados.")
            else:
                sessoes_unicas = df['Sessão'].unique()[::-1]
                st.write("Selecione a observação que pretende descarregar:")
                for sessao in sessoes_unicas:
                    if st.button(f"🗓️ {sessao.split('] ')[-1]} ({sessao.split(']')[0][1:]})"):
                        st.session_state.sessao_selecionada = sessao
                        st.session_state.pagina = 'ver_sessao_detalhe'
                        st.rerun()
        except Exception as e:
            st.error(f"Erro ao ler o ficheiro: {e}")
    else:
        st.info("Ainda não existem registos guardados.")
        
    st.write("---")
    if st.button("⬅️ Voltar ao Menu"):
        st.session_state.pagina = 'menu'
        st.rerun()

elif st.session_state.pagina == 'ver_sessao_detalhe':
    sessao_atual = st.session_state.sessao_selecionada
    nome_limpo = sessao_atual.split('] ')[-1]
    st.subheader(f"Registo: {nome_limpo}")
    
    try:
        df = pd.read_csv(FILE_NAME, encoding='utf-8-sig', sep=';')
        df_sessao = df[df['Sessão'] == sessao_atual]
        st.dataframe(df_sessao.drop(columns=['Sessão']), use_container_width=True, hide_index=True)
        st.write("---")
        csv_sessao = df_sessao.drop(columns=['Sessão']).to_csv(index=False, sep=';', encoding='utf-8-sig')
        nome_ficheiro_seguro = sessao_atual.replace('/', '-').replace(':', 'h').replace('[', '').replace(']', '').replace(' ', '_')
        st.download_button(
            label=f"📥 Descarregar Excel ({len(df_sessao)} linhas)",
            data=csv_sessao,
            file_name=f"registo_{nome_ficheiro_seguro}.csv",
            mime="text/csv",
            use_container_width=True
        )
    except Exception as e:
        st.error(f"Erro ao processar os dados: {e}")
        
    st.write("---")
    if st.button("⬅️ Voltar à Lista"):
        st.session_state.pagina = 'ver_registos'
        st.rerun()