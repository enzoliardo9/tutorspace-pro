import streamlit as st
from groq import Groq
import PyPDF2
from fpdf import FPDF
import base64
import requests
from io import BytesIO

# --- CONFIGURAZIONE DELLA PAGINA E UI PREMIUM ---
st.set_page_config(page_title="TutorSpace OS", page_icon="🪐", layout="wide")

# CSS Custom Avanzato (Con Fix per il Tema Scuro/Testo Bianco)
custom_css = """
<style>
    /* 1. Animazione Globale di Entrata (Fade In & Slide Up) */
    @keyframes fadeInSlideUp {
        from { opacity: 0; transform: translateY(30px); }
        to { opacity: 1; transform: translateY(0); }
    }
    .block-container {
        animation: fadeInSlideUp 0.8s cubic-bezier(0.16, 1, 0.3, 1) forwards;
    }

    /* 2. Titolo a Gradiente Animato (Effetto Premium SaaS) */
    @keyframes gradientText {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    .animated-title {
        background: linear-gradient(-45deg, #2A629A, #00C9FF, #1B426E, #2A629A);
        background-size: 300%;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        animation: gradientText 6s ease infinite;
        font-weight: 800;
        font-size: 3rem;
        margin-bottom: 0.5rem;
        letter-spacing: -1px;
    }

    /* 3. Animazione Entrata Messaggi Chat (Slide In Left) */
    @keyframes slideInChat {
        from { opacity: 0; transform: translateX(-20px) scale(0.95); }
        to { opacity: 1; transform: translateX(0) scale(1); }
    }
    .stChatMessage {
        border-radius: 12px !important;
        padding: 15px !important;
        margin-bottom: 15px !important;
        background-color: #ffffff !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        border: 1px solid #e2e8f0;
        animation: slideInChat 0.4s ease-out forwards;
    }
    
    /* FIX TESTO BIANCO: Forziamo il colore del testo a grigio scuro dentro la chat */
    .stChatMessage p, .stChatMessage span, .stChatMessage li, .stChatMessage h1, .stChatMessage h2, .stChatMessage h3, .stChatMessage div {
        color: #1E293B !important; 
    }

    /* 4. Effetto Bottoni Pulsanti (Pulse Glow) */
    @keyframes pulseGlow {
        0% { box-shadow: 0 0 0 0 rgba(42, 98, 154, 0.4); }
        70% { box-shadow: 0 0 0 10px rgba(42, 98, 154, 0); }
        100% { box-shadow: 0 0 0 0 rgba(42, 98, 154, 0); }
    }
    .stButton>button {
        background-color: #2A629A !important;
        color: white !important;
        border-radius: 8px !important;
        border: none !important;
        font-weight: 600 !important;
        padding: 0.6rem 1.2rem !important;
        transition: all 0.3s ease !important;
    }
    .stButton>button:hover {
        background-color: #1B426E !important;
        transform: translateY(-3px) !important;
        animation: pulseGlow 1.5s infinite;
    }

    /* 5. Animazione Hover sulle Schede in alto (Tabs) */
    .stTabs [data-baseweb="tab-list"] button {
        transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
    }
    .stTabs [data-baseweb="tab-list"] button:hover {
        transform: translateY(-3px);
        color: #2A629A;
    }

    /* 6. Animazione Cambio Pagina (Transizione tra Schede) */
    @keyframes tabFadeIn {
        from { opacity: 0; transform: translateY(15px) scale(0.99); }
        to { opacity: 1; transform: translateY(0) scale(1); }
    }
    div[data-baseweb="tab-panel"] {
        animation: tabFadeIn 0.5s cubic-bezier(0.16, 1, 0.3, 1) forwards;
    }
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# --- RECUPERO CHIAVE API ---
try:
    api_key = st.secrets["GROQ_API_KEY"]
except KeyError:
    st.error("🛑 Errore: Chiave API mancante. Configura GROQ_API_KEY nei Secrets.")
    st.stop()

client = Groq(api_key=api_key)

# --- INIZIALIZZAZIONE MEMORIA MULTI-AGENTE ---
if "testo_pdf" not in st.session_state:
    st.session_state.testo_pdf = ""
if "codice_mappa" not in st.session_state:
    st.session_state.codice_mappa = ""

if "chat_home" not in st.session_state:
    st.session_state.chat_home = [{"role": "assistant", "content": "Ciao! Sono il tuo **Assistente Guida**. Usa le schede in alto per esplorare la piattaforma."}]
if "chat_doc" not in st.session_state:
    st.session_state.chat_doc = [{"role": "assistant", "content": "Sono l'**Analista Documentale AI**. Carica un PDF e fammi qualsiasi domanda."}]
if "chat_plan" not in st.session_state:
    st.session_state.chat_plan = [{"role": "assistant", "content": "Sono il tuo **Pianificatore Didattico AI**. Ti creerò una tabella di marcia implacabile."}]
if "chat_feynman" not in st.session_state:
    st.session_state.chat_feynman = [{"role": "assistant", "content": "Sono il **Professore Divulgatore**. Quale concetto ti sembra incomprensibile? Te lo spiegherò usando il Metodo Feynman: in modo semplice, chiaro e con esempi della vita quotidiana!"}]

# ==========================================
# MOTORE DELLE CHAT
# ==========================================
def gestisci_chat(lista_messaggi, istruzioni_sistema, nome_agente, icona_agente):
    chat_container = st.container(height=400, border=False)
    with chat_container:
        for m in lista_messaggi:
            avatar = "👤" if m["role"] == "user" else icona_agente
            st.chat_message(m["role"], avatar=avatar).markdown(m["content"])

    if domanda := st.chat_input(f"Scrivi al {nome_agente}..."):
        lista_messaggi.append({"role": "user", "content": domanda})
        with chat_container:
            st.chat_message("user", avatar="👤").markdown(domanda)
            
            messaggi_ia = [{"role": "system", "content": istruzioni_sistema}]
            messaggi_ia.extend([{"role": m["role"], "content": m["content"]} for m in lista_messaggi])
            
            with st.chat_message("assistant", avatar=icona_agente):
                casella = st.empty()
                testo_risposta = ""
                try:
                    stream = client.chat.completions.create(messages=messaggi_ia, model="llama-3.3-70b-versatile", stream=True)
                    for blocco in stream:
                        if blocco.choices[0].delta.content:
                            testo_risposta += blocco.choices[0].delta.content
                            casella.markdown(testo_risposta)
                    lista_messaggi.append({"role": "assistant", "content": testo_risposta})
                except Exception as e:
                    st.error(f"Errore di rete: {e}")

# ==========================================
# INTESTAZIONE GLOBALE (Con Titolo Animato CSS)
# ==========================================
st.markdown('<div class="animated-title">🪐 TutorSpace OS</div>', unsafe_allow_html=True)

if st.session_state.testo_pdf != "":
    st.success("📄 **Documento Attivo in memoria.** Le intelligenze artificiali stanno lavorando sui tuoi appunti.")
    if st.button("🗑️ Rimuovi Documento"):
        st.session_state.testo_pdf = ""
        st.session_state.codice_mappa = ""
        st.rerun()

st.write("---")

# ==========================================
# LA NAVIGAZIONE A SCHEDE (INDESTRUTTIBILE)
# ==========================================
tab_home, tab_analista, tab_piano, tab_feynman, tab_mappe = st.tabs([
    "🏠 Home", 
    "📄 Analista", 
    "🗓️ Pianificatore", 
    "💡 Metodo Feynman", 
    "🗺️ Mappe Visive"
])

# --- CONTENUTO SCHEDA HOME ---
with tab_home:
    st.subheader("Benvenuto nella tua Suite di Apprendimento")
    st.markdown("Naviga usando le schede qui sopra. Ogni scheda contiene un'Intelligenza Artificiale specializzata.")
    
    istruzioni = "Sei l'assistente di benvenuto di TutorSpace OS. Sii professionale, come il concierge di un software di lusso."
    gestisci_chat(st.session_state.chat_home, istruzioni, "Assistente", "🤖")

# --- CONTENUTO SCHEDA ANALISTA ---
with tab_analista:
    st.subheader("📄 Analista Documentale")
    if st.session_state.testo_pdf == "":
        file_caricato = st.file_uploader("Trascina qui il tuo PDF per iniziare:", type=["pdf"])
        if file_caricato and st.button("Acquisisci Documento", type="primary"):
            with st.spinner("Indicizzazione del documento in corso..."):
                lettore = PyPDF2.PdfReader(file_caricato)
                st.session_state.testo_pdf = "".join([p.extract_text() + "\n" for p in lettore.pages])
                st.session_state.chat_doc.append({"role": "assistant", "content": "✅ Ho indicizzato il documento. Cosa vuoi sapere?"})
                st.rerun()

    istruzioni = f"Rispondi in modo preciso, basandoti SOLO su questo testo: {st.session_state.testo_pdf}."
    gestisci_chat(st.session_state.chat_doc, istruzioni, "Analista", "🧐")

# --- CONTENUTO SCHEDA PIANIFICATORE ---
with tab_piano:
    st.subheader("🗓️ Pianificatore Strategico")
    st.markdown("Ottimizza il tuo tempo. L'IA creerà tabelle di marcia realistiche basate sul tuo carico di studio.")
    istruzioni = f"Crea tabelle di marcia in Markdown basate su questo materiale: {st.session_state.testo_pdf[:10000]}"
    gestisci_chat(st.session_state.chat_plan, istruzioni, "Pianificatore", "📅")

# --- CONTENUTO SCHEDA FEYNMAN ---
with tab_feynman:
    st.subheader("💡 Divulgatore (Metodo Feynman)")
    st.markdown("Chiedi all'IA di spiegarti un concetto difficile e lei te lo spiegherà come se fossi un principiante, usando analogie efficaci.")
    
    istruzioni = "Sei un divulgatore geniale. Spiega i concetti richiesti usando il Metodo Feynman: linguaggio semplicissimo, zero termini tecnici incomprensibili, e inserisci SEMPRE un'analogia o metafora della vita quotidiana ben evidenziata."
    if st.session_state.testo_pdf:
        istruzioni += f"\nUsa come base di verità questo testo caricato: {st.session_state.testo_pdf[:10000]}"
        
    gestisci_chat(st.session_state.chat_feynman, istruzioni, "Prof. Divulgatore", "💡")

# --- CONTENUTO SCHEDA MAPPE VISIVE ---
with tab_mappe:
    st.subheader("🗺️ Generatore di Mappe Visive")
    st.markdown("Trasforma istantaneamente ore di studio in un diagramma di flusso visivo.")
    
    if st.button("✨ Genera Mappa dai miei Appunti", type="primary"):
        if st.session_state.testo_pdf:
            with st.spinner("Strutturazione dei macro-concetti in corso..."):
                istruzioni_mappa = f"""Estrai i concetti chiave da questo testo e crea un diagramma 'Mermaid'.
                REGOLE TASSATIVE:
                1. Usa SOLO: graph TD
                2. NIENTE parentesi, apici o virgolette nei nomi dei nodi.
                3. RIASSUMI: Usa MASSIMO 15-20 nodi.
                4. Restituisci SOLO il codice puro senza la parola 'mermaid' e senza backticks (```).
                Testo: {st.session_state.testo_pdf[:10000]}"""
                
                try:
                    risp = client.chat.completions.create(messages=[{"role": "user", "content": istruzioni_mappa}], model="llama-3.3-70b-versatile")
                    codice_pulito = risp.choices[0].message.content.replace("```mermaid", "").replace("```", "").strip()
                    st.session_state.codice_mappa = codice_pulito
                except Exception as e:
                    st.error(f"Errore di generazione: {e}")
        else:
            st.warning("⚠️ Carica un PDF nella sezione 'Analista' per abilitare questa funzione.")

    if st.session_state.codice_mappa != "":
        st.markdown("### Anteprima Interattiva:")
        st.markdown(f"```mermaid\n{st.session_state.codice_mappa}\n```")
        st.divider()
        
        with st.spinner("Elaborazione esportazione PDF..."):
            img_url = ""
            try:
                graphbytes = st.session_state.codice_mappa.encode("utf8")
                base64_string = base64.b64encode(graphbytes).decode("ascii")
                img_url = f"[https://mermaid.ink/img/](https://mermaid.ink/img/){base64_string}?bgColor=white".strip()
                
                response = requests.get(img_url)
                
                if response.status_code == 200:
                    img_stream = BytesIO(response.content)
                    img_stream.name = "mappa.png" 
                    
                    pdf = FPDF(orientation="L") 
                    pdf.add_page()
                    pdf.set_font('helvetica', 'B', 16)
                    pdf.cell(0, 10, 'TutorSpace OS - Visual Architecture', ln=True, align='C')
                    
                    pdf.image(img_stream, x=15, y=25, w=260)
                    
                    st.download_button(
                        label="📥 SCARICA HIGH-RES PDF",
                        data=bytes(pdf.output()),
                        file_name="TutorSpace_Mappa.pdf",
                        mime="application/pdf",
                        type="primary",
                        use_container_width=True
                    )
                else:
                    st.error(f"⚠️ Render grafico rifiutato (Errore {response.status_code}).")
                    st.markdown(f"**Soluzione alternativa:** [🔗 Clicca qui per scaricare l'immagine sorgente]({img_url})")
            
            except Exception as e:
                st.error(f"Il motore PDF locale ha riscontrato un'interruzione di sicurezza.")
                if img_url:
                    st.info("💡 L'asset grafico è comunque pronto. Utilizza il link diretto:")
                    st.markdown(f"👉 **[SCARICA IMMAGINE MAPPA]({img_url})**")
