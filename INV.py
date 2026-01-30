import streamlit as st
import pandas as pd
from pathlib import Path
from datetime import datetime
import os

from supabase import create_client, Client

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
# FUNÇÕES GERAIS
# ==================================================
def agora():
    return datetime.now().strftime("%d/%m/%Y %H:%M")

# ==================================================
# SUPABASE (SECRETS / supa.env / ENV)
# ==================================================
BASE_DIR = Path(__file__).parent
SUPA_ENV_PATH = BASE_DIR / "supa.env"

def carregar_supa_env(path: Path) -> dict:
    cfg = {}
    if not path.exists():
        return cfg
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        k, v = line.split("=", 1)
        k = k.strip()
        v = v.strip().strip('"').strip("'")
        cfg[k] = v
    return cfg

SUPA_FILE = carregar_supa_env(SUPA_ENV_PATH)

def get_secret_safe(name: str):
    try:
        return st.secrets.get(name, None)
    except Exception:
        return None

def get_env(name: str, default: str = "") -> str:
    # 1) Streamlit Cloud Secrets
    sec = get_secret_safe(name)
    if sec is not None and str(sec).strip():
        return str(sec).strip()

    # 2) supa.env (mesma pasta do script)
    if name in SUPA_FILE and str(SUPA_FILE[name]).strip():
        return str(SUPA_FILE[name]).strip()

    # 3) Variável de ambiente do SO
    return str(os.getenv(name, default)).strip()

SUPABASE_URL = get_env("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = get_env("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
    st.error(
        "Faltam SUPABASE_URL e/ou SUPABASE_SERVICE_ROLE_KEY.\n\n"
        "✅ Streamlit Cloud: Settings → Secrets\n"
        "✅ Local: crie 'supa.env' na mesma pasta do app"
    )
    st.stop()

sb: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

# ==================================================
# SUPABASE - QUERIES
# ==================================================
def sb_select_usuarios() -> pd.DataFrame:
    resp = sb.table("usuarios").select("usuario,senha,perfil").execute()
    data = resp.data or []
    df = pd.DataFrame(data)
    if df.empty:
        return pd.DataFrame(columns=["usuario", "senha", "perfil"])
    df["usuario"] = df["usuario"].astype(str).str.strip().str.lower()
    df["senha"] = df["senha"].astype(str).str.strip()
    df["perfil"] = df["perfil"].astype(str).str.strip().str.lower()
    return df[["usuario", "senha", "perfil"]]

def sb_upsert_usuario(usuario: str, senha: str, perfil: str):
    sb.table("usuarios").upsert(
        {"usuario": usuario.strip().lower(), "senha": senha.strip(), "perfil": perfil.strip().lower()},
        on_conflict="usuario"
    ).execute()

def sb_update_senha(usuario_alvo: str, nova_senha: str):
    sb.table("usuarios").update(
        {"senha": str(nova_senha).strip()}
    ).eq("usuario", str(usuario_alvo).strip().lower()).execute()

def sb_usuario_existe(usuario: str) -> bool:
    u = str(usuario).strip().lower()
    resp = sb.table("usuarios").select("usuario").eq("usuario", u).limit(1).execute()
    return bool(resp.data)

def sb_insert_contagem(linha: dict):
    sb.table("contagens").insert(linha).execute()

def sb_select_contagens() -> pd.DataFrame:
    resp = sb.table("contagens").select("*").order("id", desc=True).execute()
    data = resp.data or []
    df = pd.DataFrame(data)
    if df.empty:
        return pd.DataFrame()
    cols_pref = ["datahora","usuario","tipocontagem","local","etiqueta","codigo","descricao","qtdfisica"]
    cols = [c for c in cols_pref if c in df.columns] + [c for c in df.columns if c not in cols_pref]
    return df[cols]

# ✅ ALTERAÇÃO PEDIDA: puxar produtos do Supabase e usar a descrição automaticamente
@st.cache_data(ttl=120)
def sb_select_produtos() -> pd.DataFrame:
    # Tabela: public.Produtos | Colunas: Codigo, Descricao
    resp = sb.table("Produtos").select("Codigo,Descricao").order("Codigo").execute()
    data = resp.data or []
    df = pd.DataFrame(data)
    if df.empty:
        return pd.DataFrame(columns=["Codigo", "Descricao"])

    df["Codigo"] = df["Codigo"].astype(str).str.strip()
    df["Descricao"] = df["Descricao"].astype(str).str.strip()
    df = df[df["Codigo"] != ""].drop_duplicates(subset=["Codigo"])
    return df[["Codigo", "Descricao"]]

# ==================================================
# SEED DE USUÁRIOS (SÓ SE TABELA VAZIA)
# ==================================================
def init_users():
    dfu = sb_select_usuarios()
    if not dfu.empty:
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
    for u in users:
        sb_upsert_usuario(u["usuario"], u["senha"], u["perfil"])

# ==================================================
# LOGIN
# ==================================================
def autenticar(dfu: pd.DataFrame, usuario: str, senha: str):
    u = str(usuario).strip().lower()
    s = str(senha).strip()
    hit = dfu[dfu["usuario"] == u]
    if hit.empty:
        return False, None
    if hit.iloc[0]["senha"] != s:
        return False, None
    return True, hit.iloc[0]["perfil"]

if "logado" not in st.session_state:
    st.session_state.logado = False
if "user" not in st.session_state:
    st.session_state.user = ""
if "perfil" not in st.session_state:
    st.session_state.perfil = ""

# garante seed antes de buscar
init_users()
dfu = sb_select_usuarios()

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
# PRODUTOS (AGORA VEM DO SUPABASE)
# ==================================================
df_prod = sb_select_produtos()

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

    user_atual = st.session_state.user.strip().lower()
    somente_linha = user_atual in ["vitor", "junior", "lucas"]

    if somente_linha:
        locais = [SELECIONE, "Linha"]
    else:
        locais = [SELECIONE, "BU2", "BU4", "Linha"]

    st.subheader("🧾 Lançar contagem")

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
        if df_prod.empty:
            st.warning("Catálogo (Supabase) vazio. Use 'Digitar manualmente' para código e descrição.")
            codigo = st.text_input("Código (manual)", key="codigo_manual").strip()
            descricao = st.text_input("Descrição (manual)", key="descricao_manual").strip()
        else:
            opcoes_cod = [SELECIONE] + df_prod["Codigo"].tolist()
            codigo_sel = st.selectbox("Código", opcoes_cod, key="codigo_sel")

            if codigo_sel != SELECIONE:
                hit = df_prod[df_prod["Codigo"] == codigo_sel]
                if not hit.empty:
                    codigo = codigo_sel
                    descricao = hit["Descricao"].iloc[0]

            st.text_input("Descrição", value=descricao, disabled=True)

    else:
        # ✅ ALTERAÇÃO PEDIDA: digitou o código, busca a descrição no Supabase automaticamente
        codigo = st.text_input("Código (manual)", key="codigo_manual").strip()

        desc_auto = ""
        if codigo and not df_prod.empty:
            hit = df_prod[df_prod["Codigo"] == codigo]
            if not hit.empty:
                desc_auto = hit["Descricao"].iloc[0]

        if desc_auto:
            descricao = st.text_input("Descrição", value=desc_auto, disabled=True, key="descricao_auto_manual")
        else:
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
            sb_insert_contagem(
                {
                    "datahora": agora(),
                    "usuario": st.session_state.user,
                    "tipocontagem": tipo_contagem,
                    "local": local,
                    "etiqueta": etiqueta,
                    "codigo": codigo,
                    "descricao": descricao,
                    "qtdfisica": int(qtd),
                }
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

        df_c = sb_select_contagens()
        if df_c.empty:
            st.info("Nenhuma contagem registrada ainda.")
        else:
            st.dataframe(df_c, use_container_width=True, height=520)

            st.download_button(
                "⬇️ Baixar CSV",
                df_c.to_csv(index=False, encoding="utf-8-sig"),
                "contagens.csv",
                "text/csv",
                use_container_width=True
            )

# ==================================================
# TAB - ADMIN (SÓ ADMIN)
# ==================================================
if st.session_state.perfil == "admin":
    with tab_admin:
        st.subheader("👤 Administração de usuários")

        dfu = sb_select_usuarios()

        st.markdown("### 🔑 Trocar senha de usuário")
        usuarios_lista = sorted(dfu["usuario"].tolist()) if not dfu.empty else []
        alvo = st.selectbox("Usuário", usuarios_lista, key="alvo_senha")
        nova = st.text_input("Nova senha", type="password", key="nova_senha")

        if st.button("Atualizar senha", use_container_width=True, key="btn_atualiza"):
            if not nova.strip():
                st.warning("Informe a nova senha.")
            else:
                sb_update_senha(alvo, nova)
                st.success(f"Senha atualizada para: {alvo}")

        st.markdown("---")
        st.markdown("### ➕ Criar novo usuário")
        novo_user = st.text_input("Novo usuário (sem espaço)", key="novo_user").strip().lower()
        nova_senha2 = st.text_input("Senha inicial", type="password", key="nova_senha2")
        perfil_novo = st.selectbox("Perfil", ["padrao", "admin"], key="perfil_novo")

        if st.button("Criar usuário", use_container_width=True, key="btn_cria"):
            if not novo_user or " " in novo_user:
                st.warning("Informe um usuário válido (sem espaços).")
            elif sb_usuario_existe(novo_user):
                st.warning("Esse usuário já existe.")
            elif not nova_senha2.strip():
                st.warning("Informe a senha inicial.")
            else:
                sb_upsert_usuario(novo_user, nova_senha2, perfil_novo)
                st.success("Usuário criado ✅")

