import streamlit as st
import pandas as pd
from pathlib import Path
from datetime import datetime

# ==================================================
# CONFIG
# ==================================================
st.set_page_config(page_title="Inventário", layout="wide")

st.markdown("""
<style>
.main .block-container { max-width: 520px; }
h1,h2,h3 { text-align:center; }
.stButton>button { height:55px; font-size:18px; border-radius:10px; }
div[data-baseweb="input"] input,
div[data-baseweb="select"] div,
textarea,
.stNumberInput input {
    font-size: 16px !important;
    min-height: 48px !important;
}

/* Centralizar texto dentro dos SELECTBOX (Local e Código) */
div[data-baseweb="select"] > div { text-align: center !important; }
div[data-baseweb="select"] span {
    display: inline-block !important;
    width: 100% !important;
    text-align: center !important;
}
</style>
""", unsafe_allow_html=True)

st.title("📦 Inventário Supermercado")

# ==================================================
# CAMINHOS
# ==================================================
BASE_DIR = Path(__file__).parent
DB_DIR = BASE_DIR / "db"
DB_DIR.mkdir(exist_ok=True)

ARQ_CONTAGENS = DB_DIR / "contagens.csv"
ARQ_USUARIOS = DB_DIR / "usuarios.csv"
CAMINHO_PRODUTOS = Path(r"C:\Users\aline.lima\Desktop\INVENTARIO\Produtos.xlsx")

# ==================================================
# FUNÇÕES
# ==================================================
def agora():
    return datetime.now().strftime("%d/%m/%Y %H:%M")

def salvar_append(path: Path, linha: dict):
    if path.exists():
        df = pd.read_csv(path, dtype=str).fillna("")
    else:
        df = pd.DataFrame()
    df = pd.concat([df, pd.DataFrame([linha])], ignore_index=True)
    df.to_csv(path, index=False, encoding="utf-8-sig")

def salvar_csv(path: Path, df: pd.DataFrame):
    df.to_csv(path, index=False, encoding="utf-8-sig")

# ==================================================
# USUÁRIOS PADRÃO (CRIA AUTOMATICAMENTE)
# ==================================================
def init_users():
    if ARQ_USUARIOS.exists():
        return

    users = [
        {"usuario":"aline","senha":"123","perfil":"admin"},
        {"usuario":"guilherme","senha":"123","perfil":"admin"},
        {"usuario":"erick","senha":"123","perfil":"padrao"},
        {"usuario":"jaciane","senha":"123","perfil":"padrao"},
        {"usuario":"gilmar","senha":"123","perfil":"padrao"},
        {"usuario":"rafael","senha":"123","perfil":"padrao"},
        {"usuario":"caio","senha":"123","perfil":"padrao"},
        {"usuario":"fernando","senha":"123","perfil":"padrao"},
        {"usuario":"andre","senha":"123","perfil":"padrao"},
        {"usuario":"eduardo","senha":"123","perfil":"padrao"},
        {"usuario":"cleber","senha":"123","perfil":"padrao"},
        {"usuario":"daniel","senha":"123","perfil":"padrao"},
        {"usuario":"lucas","senha":"123","perfil":"padrao"},
        {"usuario":"junior","senha":"123","perfil":"padrao"},
        {"usuario":"vera","senha":"123","perfil":"padrao"},
        {"usuario":"vitor","senha":"123","perfil":"padrao"},
        {"usuario":"cibele","senha":"123","perfil":"padrao"},
    ]
    salvar_csv(ARQ_USUARIOS, pd.DataFrame(users))

def carregar_usuarios() -> pd.DataFrame:
    init_users()
    dfu = pd.read_csv(ARQ_USUARIOS, dtype=str).fillna("")
    for c in ["usuario", "senha", "perfil"]:
        if c not in dfu.columns:
            dfu[c] = ""
    dfu["usuario"] = dfu["usuario"].astype(str).str.strip().str.lower()
    dfu["senha"] = dfu["senha"].astype(str).str.strip()
    dfu["perfil"] = dfu["perfil"].astype(str).str.strip().str.lower()
    return dfu[["usuario", "senha", "perfil"]]

def autenticar(dfu: pd.DataFrame, usuario: str, senha: str):
    u = str(usuario).strip().lower()
    s = str(senha).strip()
    hit = dfu[dfu["usuario"] == u]
    if hit.empty:
        return False, None
    if hit.iloc[0]["senha"] != s:
        return False, None
    return True, hit.iloc[0]["perfil"]

def usuario_existe(dfu: pd.DataFrame, usuario: str) -> bool:
    u = str(usuario).strip().lower()
    return not dfu[dfu["usuario"] == u].empty

def atualizar_senha(dfu: pd.DataFrame, usuario_alvo: str, nova_senha: str) -> pd.DataFrame:
    u = str(usuario_alvo).strip().lower()
    dfu.loc[dfu["usuario"] == u, "senha"] = str(nova_senha).strip()
    salvar_csv(ARQ_USUARIOS, dfu)
    return dfu

def criar_usuario(dfu: pd.DataFrame, usuario_novo: str, senha_nova: str, perfil: str) -> pd.DataFrame:
    u = str(usuario_novo).strip().lower()
    s = str(senha_nova).strip()
    p = str(perfil).strip().lower()
    dfu = pd.concat([dfu, pd.DataFrame([{"usuario": u, "senha": s, "perfil": p}])], ignore_index=True)
    salvar_csv(ARQ_USUARIOS, dfu)
    return dfu

# ==================================================
# LOGIN
# ==================================================
if "logado" not in st.session_state:
    st.session_state.logado = False
if "user" not in st.session_state:
    st.session_state.user = ""
if "perfil" not in st.session_state:
    st.session_state.perfil = ""

dfu = carregar_usuarios()

if not st.session_state.logado:
    st.subheader("🔐 Login")
    u = st.text_input("Usuário").strip().lower()
    s = st.text_input("Senha", type="password").strip()

    if st.button("Entrar", use_container_width=True):
        ok, perfil = autenticar(dfu, u, s)
        if ok:
            st.session_state.logado = True
            st.session_state.user = u
            st.session_state.perfil = perfil
            st.rerun()
        else:
            st.error("Usuário ou senha inválidos.")
    st.stop()

top1, top2 = st.columns([3, 1])
with top1:
    st.success(f"Logado como: {st.session_state.user} ({st.session_state.perfil})")
with top2:
    if st.button("Sair", use_container_width=True):
        st.session_state.logado = False
        st.session_state.user = ""
        st.session_state.perfil = ""
        st.rerun()

# ==================================================
# PRODUTOS
# ==================================================
def carregar_produtos():
    if not CAMINHO_PRODUTOS.exists():
        return pd.DataFrame(columns=["Codigo", "Descricao"])

    df = pd.read_excel(CAMINHO_PRODUTOS, dtype=str).fillna("")
    ren = {}
    for c in df.columns:
        cl = str(c).strip().lower()
        if cl in ["codigo", "código"]:
            ren[c] = "Codigo"
        elif cl in ["descricao", "descrição"]:
            ren[c] = "Descricao"
    df = df.rename(columns=ren)

    if "Codigo" not in df.columns and len(df.columns) >= 1:
        df = df.rename(columns={df.columns[0]: "Codigo"})
    if "Descricao" not in df.columns and len(df.columns) >= 2:
        df = df.rename(columns={df.columns[1]: "Descricao"})

    df["Codigo"] = df["Codigo"].astype(str).str.strip()
    df["Descricao"] = df["Descricao"].astype(str).str.strip()
    df = df[df["Codigo"] != ""].drop_duplicates(subset=["Codigo"])
    return df[["Codigo", "Descricao"]]

df_prod = carregar_produtos()

# ==================================================
# TABS
# ==================================================
tabs = ["🧾 Contagem"]
if st.session_state.perfil == "admin":
    tabs += ["📊 Contagens", "👤 Admin"]

tabs_objs = st.tabs(tabs)

tab_contagem = tabs_objs[0]
tab_contagens = tabs_objs[1] if st.session_state.perfil == "admin" else None
tab_admin = tabs_objs[2] if st.session_state.perfil == "admin" else None

# ==================================================
# TAB - CONTAGEM
# ==================================================
with tab_contagem:
    SELECIONE = "(SELECIONE)"

    # ==================================================
    # AJUSTE PEDIDO (SEM MEXER NO RESTO):
    # vitor, junior e lucas -> local somente "Linha"
    # demais -> opções normais
    # ==================================================
    user_atual = st.session_state.user.strip().lower()
    somente_linha = user_atual in ["vitor", "junior", "lucas"]

    if somente_linha:
        locais = [SELECIONE, "Linha"]
    else:
        locais = [SELECIONE, "BU2", "BU4", "Linha"]

    st.subheader("🧾 Lançar contagem")

    # ---------------------------
    # LIMPAR CAMPOS APÓS SALVAR
    # ---------------------------
    if "limpar_campos" not in st.session_state:
        st.session_state["limpar_campos"] = False

    if st.session_state["limpar_campos"]:
        st.session_state["tipo_contagem"] = SELECIONE
        st.session_state["local"] = SELECIONE
        st.session_state["codigo_sel"] = SELECIONE
        st.session_state["qtd"] = 1
        st.session_state["etiqueta"] = ""
        st.session_state["codigo_manual"] = ""
        st.session_state["descricao_manual"] = ""
        st.session_state["limpar_campos"] = False

    tipo_contagem = st.selectbox(
        "Tipo de contagem",
        [SELECIONE, "1ª contagem", "2ª contagem", "3ª contagem"],
        key="tipo_contagem"
    )

    local = st.selectbox("Local", locais, key="local")

    modo = st.radio(
        "Modo de lançamento",
        ["Selecionar da lista", "Digitar manualmente"],
        horizontal=True,
        key="modo_lanc"
    )

    etiqueta = st.text_input("Número da etiqueta", key="etiqueta").strip()

    codigo = ""
    descricao = ""

    if modo == "Selecionar da lista":
        opcoes_cod = [SELECIONE] + df_prod["Codigo"].tolist()
        codigo_sel = st.selectbox("Código", opcoes_cod, key="codigo_sel")

        if codigo_sel != SELECIONE and not df_prod.empty:
            hit = df_prod[df_prod["Codigo"] == codigo_sel]
            if not hit.empty:
                codigo = codigo_sel
                descricao = hit["Descricao"].iloc[0]

        st.text_input("Descrição", value=descricao, disabled=True)

    else:
        codigo = st.text_input("Código (manual)", key="codigo_manual").strip()
        descricao = st.text_input("Descrição (manual)", key="descricao_manual").strip()

    qtd = st.number_input("Quantidade física", min_value=1, step=1, key="qtd")

    if st.button("✅ Salvar contagem", use_container_width=True):
        if tipo_contagem == SELECIONE:
            st.warning("Selecione o TIPO DE CONTAGEM.")
        elif local == SELECIONE:
            st.warning("Selecione o LOCAL.")
        elif not etiqueta:
            st.warning("Informe o NÚMERO DA ETIQUETA.")
        elif not codigo:
            st.warning("Informe o CÓDIGO.")
        elif not descricao:
            st.warning("Informe a DESCRIÇÃO.")
        else:
            salvar_append(
                ARQ_CONTAGENS,
                {
                    "DataHora": agora(),
                    "Usuario": st.session_state.user,
                    "TipoContagem": tipo_contagem,
                    "Local": local,
                    "Etiqueta": etiqueta,
                    "Codigo": codigo,
                    "Descricao": descricao,
                    "QtdFisica": str(int(qtd)),
                },
            )
            st.session_state["limpar_campos"] = True
            st.success("Contagem salva ✅")
            st.rerun()

# ==================================================
# TAB - CONTAGENS (SÓ ADMIN)
# ==================================================
if st.session_state.perfil == "admin":
    with tab_contagens:
        st.subheader("📊 Contagens (somente admin)")

        if ARQ_CONTAGENS.exists():
            df_c = pd.read_csv(ARQ_CONTAGENS, dtype=str).fillna("")
            st.dataframe(df_c, use_container_width=True, height=520)

            st.download_button(
                "⬇️ Baixar CSV",
                df_c.to_csv(index=False, encoding="utf-8-sig"),
                "contagens.csv",
                "text/csv",
                use_container_width=True
            )
        else:
            st.info("Nenhuma contagem registrada ainda.")

# ==================================================
# TAB - ADMIN (SÓ ADMIN)
# ==================================================
if st.session_state.perfil == "admin":
    with tab_admin:
        st.subheader("👤 Administração de usuários")

        dfu = carregar_usuarios()

        st.markdown("### 🔑 Trocar senha de usuário")
        usuarios_lista = sorted(dfu["usuario"].tolist())
        alvo = st.selectbox("Usuário", usuarios_lista, key="alvo_senha")
        nova = st.text_input("Nova senha", type="password", key="nova_senha")

        if st.button("Atualizar senha", use_container_width=True, key="btn_atualiza"):
            if not nova.strip():
                st.warning("Informe a nova senha.")
            else:
                dfu = atualizar_senha(dfu, alvo, nova)
                st.success(f"Senha atualizada para: {alvo}")

        st.markdown("---")
        st.markdown("### ➕ Criar novo usuário")
        novo_user = st.text_input("Novo usuário (sem espaço)", key="novo_user").strip().lower()
        nova_senha2 = st.text_input("Senha inicial", type="password", key="nova_senha2")
        perfil_novo = st.selectbox("Perfil", ["padrao", "admin"], key="perfil_novo")

        if st.button("Criar usuário", use_container_width=True, key="btn_cria"):
            if not novo_user or " " in novo_user:
                st.warning("Informe um usuário válido (sem espaços).")
            elif usuario_existe(dfu, novo_user):
                st.warning("Esse usuário já existe.")
            elif not nova_senha2.strip():
                st.warning("Informe a senha inicial.")
            else:
                dfu = criar_usuario(dfu, novo_user, nova_senha2, perfil_novo)
                st.success("Usuário criado ✅")


