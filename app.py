import streamlit as st
import pandas as pd
import os
from dotenv import load_dotenv
import streamlit.components.v1 as components

# Fonctions de l'agent SQL
from agent.sql_agent import (
    get_db_connection,
    setup_groq_client,
    get_database_schema,
    generate_sql_query,
    execute_sql_query,
    generate_visualization
)

# --- CSS ---
# --- CSS ---
custom_css = """
<style>
/* Dark mode global */
.stApp.dark-mode { background-color: #0E1117 !important; color: #FAFAFA !important; }
.stApp.dark-mode, .stApp.dark-mode * { color: #FAFAFA !important; }
.stApp.dark-mode h1, .stApp.dark-mode h2, .stApp.dark-mode h3, .stApp.dark-mode strong { color: #FFFFFF !important; }
.stApp.dark-mode pre, .stApp.dark-mode .stCodeBlock { background-color: #1E1E1E !important; color: #FAFAFA !important; border-radius: 6px; padding: 0.5rem; }
.stApp.dark-mode input, .stApp.dark-mode textarea { background-color: #1E1E1E !important; color: #FFFFFF !important; border: 1px solid #444 !important; }
.stApp.dark-mode [data-testid="stDataFrame"] { background-color: #1E1E1E !important; border-radius: 6px; }
.stApp.dark-mode [data-testid="stDataFrame"] * { color: #FAFAFA !important; }
.stApp.dark-mode .stAlert { border-radius: 8px; font-weight: 500; color: #FFFFFF !important; }
.stApp.dark-mode input::placeholder, .stApp.dark-mode textarea::placeholder { color: #BBBBBB !important; opacity: 1 !important; }
.stApp.dark-mode [data-testid="stChatInput"] { background-color: #0E1117 !important; border-top: 1px solid #2E2E2E !important; }
.stApp.dark-mode [data-testid="stChatInput"] textarea { background-color: #1E1E1E !important; color: #FFFFFF !important; border: 1px solid #444 !important; }
.stApp.dark-mode [data-testid="stChatInput"] textarea::placeholder { color: #BBBBBB !important; opacity: 1 !important; }

/* Styles des boutons */
.stButton>button {
    background-color: #0068c9 !important;
    color: white !important;
    border-radius: 4px !important;
    padding: 6px 12px !important;
    font-size: 14px !important;
}
.stButton>button:hover {
    background-color: #0050a0 !important;
}

/* Styles pour les infos de contact */
.author-banner {
    font-size: 14px;
    color: #1f77b4;
    text-align: right;
}
.author-banner a {
    color: #1f77b4;
    text-decoration: none;
    margin-left: 8px;
}
.author-banner a:hover {
    text-decoration: underline;
}

/* Ajuste la taille des icônes Font Awesome */
.fa-icon-size {
    font-size: 20px !important;
    line-height: 1.5;
}
</style>
"""

# --- Initialisation ---
load_dotenv()

@st.cache_resource
def init_connections():
    return get_db_connection(), setup_groq_client()

def init_state():
    if "connection" not in st.session_state or "groq_client" not in st.session_state:
        st.session_state.connection, st.session_state.groq_client = init_connections()
    if "db_schema" not in st.session_state:
        st.session_state.db_schema = get_database_schema(st.session_state.connection)
    if "sql" not in st.session_state: st.session_state.sql = ""
    if "results" not in st.session_state: st.session_state.results = None
    if "chart" not in st.session_state: st.session_state.chart = None
    if "last_question" not in st.session_state: st.session_state.last_question = None
    if "page" not in st.session_state: st.session_state.page = "agent"

init_state()
st.set_page_config(page_title="THE SQLer", layout="wide")
st.markdown(custom_css, unsafe_allow_html=True)

# --- Header fixe avec boutons alignés et infos à droite ---
# --- Header fixe avec boutons alignés et infos à droite ---
col_left, col_right = st.columns([1, 9])

with col_left:
    btn1_col, btn2_col = st.columns(2)
    with btn1_col:
        # Bouton SQL avec l'icône de base de données
        if st.button(":material/home:", key="btn_agent_top"):
            st.session_state.page = "agent"
    with btn2_col:
        # Bouton SMR avec l'icône de la page d'accueil
        if st.button(":material/database:", key="btn_schema_top"):
            st.session_state.page = "info_base"

with col_right:
    st.markdown(
        """
        <div style="text-align: right; font-size: 14px; color: #1f77b4;">
            Développé par 🛠️ Ange-Paul THE 🚀|| 
            <a href="mailto:Theangepaul@gmail.com" style="color: #1f77b4; text-decoration: none;">Theangepaul@gmail.com</a> ||
            <a href="https://github.com/ryusaki13" target="_blank" style="color: #1f77b4; text-decoration: none;">GitHub</a>  
            
        </div>
        """,
        unsafe_allow_html=True
    )

# --- Pages ---
if st.session_state.page == "agent":
    st.title("THE SQLer - Agent IA Expert en SQL")
    #st.subheader("Requêtez autrement")
    st.info("""
    Bienvenue dans **THE SQLer** 🧠
       
    \n Votre agent intelligent qui prend vos questions en langage naturel, 
    \n les convertit en requêtes SQL, les exécute et vous affiche automatiquement les résultats ainsi que des visualisations adaptées.

    \n**THE SQLer🧠, Requêtez autrement......**       

    """)

    col1, col2 = st.columns([1, 1])
    with col1:
        st.markdown("**Requête SQL**")
        sql_content_placeholder = st.empty()
    with col2:
        st.markdown("**Résultats**")
        results_content_placeholder = st.empty()

    st.markdown("---")
    st.markdown("**Graphique**")
    chart_content_placeholder = st.empty()

    user_question = st.chat_input("Posez votre question ici...")
    if user_question:
        if user_question != st.session_state.last_question:
            st.session_state.last_question = user_question
            sql_query = generate_sql_query(user_question, st.session_state.db_schema, st.session_state.groq_client)
            st.session_state.sql = sql_query
            sql_content_placeholder.code(sql_query, language="sql")
            results = execute_sql_query(st.session_state.connection, sql_query)
            st.session_state.results = results
            if results:
                df = pd.DataFrame(results)
                results_content_placeholder.dataframe(df, use_container_width=True)
            else:
                results_content_placeholder.warning("La requête est valide mais n'a retourné aucun résultat.")
            with st.spinner("Génération du graphique..."):
                try:
                    chart_path = generate_visualization(user_question, results, st.session_state.groq_client)
                    st.session_state.chart = chart_path
                    if chart_path and os.path.exists(chart_path):
                        chart_content_placeholder.image(chart_path, use_container_width=True)
                    else:
                        chart_content_placeholder.info("Aucun graphique disponible")
                except Exception as e:
                    chart_content_placeholder.error(f"Impossible de générer le graphique : {e}")

elif st.session_state.page == "info_base":
    st.title("Schéma relationnel - Base Classicmodels")
    st.markdown("""
    Voici le schéma relationnel de la base de données **Classicmodels**. 
    Il permet de visualiser les tables et les relations entre elles.
    """)
    st.image("C:\\Master USPN\\Cours M1 Big Data\\Projets Portfolio\\Mon agent SQL\\schema_relationnel.jpg",
             caption="Schéma relationnel Classicmodels", use_container_width=True)
    
    st.markdown("""
Nous travaillons sur la célèbre base de données SQL "**Classicmodels**" qui a été enrichie avec de nouvelles tables et vues.
Voici les tables et vues disponibles ainsi qu'une brève description de leur contenu :

---

### Tables et Vues Principales

**`chiffre_affaire`**
Cette table synthétique regroupe les informations clés sur le chiffre d'affaires généré. Elle permet de suivre, pour chaque commande, quels produits ont été vendus, à quels clients, à quelle date, et à quel prix. Elle se base sur une jointure des tables `orders`, `orderdetails`, `customers` et `products`.

**`commande_client`**
Cette table regroupe les informations financières liées aux clients, en mettant l'accent sur le chiffre d'affaires généré par chacun d'eux. Elle permet d'obtenir une vue consolidée des revenus par client pour identifier les plus rentables.

**`customers`**
Cette table contient toutes les informations sur les clients de l'entreprise (nom, ville, pays). Elle est essentielle pour identifier nos acheteurs et où ils se trouvent.

**`employees`**
La table `employees` stocke les données des employés avec leurs informations personnelles et professionnelles (poste, bureau, hiérarchie). Elle est centrale pour la gestion des équipes.

**`products`**
La table `products` contient le catalogue complet des produits vendus, avec leurs caractéristiques techniques et commerciales (stock, prix). Elle est essentielle pour la gestion des stocks et l'analyse des gammes de produits.

**`orders`**
La table `orders` enregistre toutes les commandes clients, leurs dates clés et leur état. Elle est cruciale pour le suivi logistique et l'analyse des délais de livraison.

**`orderdetails`**
Cette table contient le détail ligne par ligne des produits commandés. Elle fait le lien entre les tables `orders` et `products` et est essentielle pour analyser les ventes par produit et les totaux des commandes.

**`payments`**
La table `payments` enregistre tous les paiements effectués par les clients. Elle permet de suivre l'historique financier de chaque client et la trésorerie de l'entreprise.

**`productlines`**
La table `productlines` décrit les différentes gammes de produits. Elle sert de référence pour catégoriser les produits et fournir des informations marketing.

**`offices`**
La table `offices` recense tous les bureaux de l'entreprise à travers le monde, avec leurs coordonnées. Elle permet d'analyser l'organisation par région.

**`ecoulement_stock`**
Cette table analytique mesure l'efficacité commerciale des produits via le taux d'écoulement du stock. Elle est cruciale pour la gestion des approvisionnements.

**`marge_produit`**
Cette vue analytique agrège les produits par gamme pour fournir une analyse des performances commerciales par ligne de produits, permettant d'identifier les plus rentables.

**`rotation_stock`**
Cette table calcule et stocke le taux de rotation des produits, un indicateur clé pour identifier les produits à forte rotation et ceux qui stagnent en stock.

**`value_stock_quantity`**
Cette table fournit une évaluation de la valeur monétaire du stock par produit. Elle permet d'identifier les articles qui représentent le plus d'investissement en stock.

**`employee_ca`**
Cette table mesure la performance commerciale des employés en agrégeant le chiffre d'affaires généré par leurs clients respectifs. Elle permet d'identifier les employés les plus performants.

**`recouvrement`**
Cette table analyse l'efficacité du recouvrement des paiements clients. Elle révèle les clients avec des impayés potentiels et aide à gérer le risque.

**`customer_orders_summary`**
Cette table agrège les données de commandes par client, montrant le volume total de produits et l'historique des commandes. Cette vue simplifiée permet une analyse rapide des achats par client.
""")