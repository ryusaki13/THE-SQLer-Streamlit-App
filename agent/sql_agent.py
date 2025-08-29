# sql_agent.py

# Importations
import os
import mysql.connector
from dotenv import load_dotenv
from mysql.connector import Error
from groq import Groq

# Import de la fonction de visualisation depuis le module visualizer.py
from visualizer import generate_visualization

# Charger les variables d'environnement
load_dotenv()

# --- Documentation des tables pour donner plus de contexte à l'IA. ---
table_documentation = {
    'chiffre_affaire':
        "Table synthétique du chiffre d'affaires. Colonnes clés: orderNumber, customerNumber, orderDate, "
        "productCode, quantityOrdered, priceEach. Contient les détails des ventes par commande, produit et client. "
        "Connexions: orders (orderNumber), customers (customerNumber), products (productCode). "
        "Utile pour les analyses de ventes et tableaux de bord commerciaux.",
    'commande_client':
        "Vue financière par client. Colonnes: customerNumber, customerName, country, chiffre_affaire_client. "
        "Montre le CA total par client. Source: customers, orders, orderdetails. "
        "Clé: customerNumber → customers.customerNumber.",
    'customers':
        "Informations clients. Colonnes: customerNumber (clé), customerName, city, state, postalCode, country, "
        "salesRepEmployeeNumber. Liée à orders via customerNumber et à employees via salesRepEmployeeNumber.",
    'employees':
        "Données employés. Colonnes: employeeNumber (clé), lastName, firstName, email, jobTitle, officeCode, reportsTo. "
        "Structure hiérarchique via reportsTo. Connectée à offices via officeCode et aux clients via employeeNumber.",
    'products':
        "Catalogue produits. Colonnes: productCode (clé), productName, productLine, productScale, productVendor, "
        "quantityInStock, buyPrice, MSRP. Organisé par gamme (productLine).",
    'orders':
        "Commandes clients. Colonnes: orderNumber (clé), orderDate, requiredDate, shippedDate, status, comments, "
        "customerNumber. Liée à customers via customerNumber.",
    'orderdetails':
        "Détails des commandes. Colonnes: orderNumber, productCode, quantityOrdered, priceEach, orderLineNumber. "
        "Connexions: orders (orderNumber), products (productCode). Essentiel pour l'analyse des ventes.",
    'payments':
        "Paiements clients. Colonnes: customerNumber, checkNumber, paymentDate, amount. "
        "Liée à customers via customerNumber. Suivi financier et trésorerie.",
    'productlines':
        "Gammes de produits. Colonnes: productLine (clé), textDescription, htmlDescription, image. "
        "Catégorisation des produits.",
    'offices':
        "Bureaux. Colonnes: officeCode (clé), city, phone, addressLine1, addressLine2, state, country, postalCode, territory. "
        "Localisation géographique des bureaux.",
    'ecoulement_stock':
        "Analyse commerciale pré-calculée. Colonnes: productName, taux_ecoulement_stock. "
        "Mesure l'efficacité de vente (% du stock vendu). **Utiliser cette table en priorité pour les questions 'taux d'écoulement'.**",
    'marge_produit':
        "Performance par gamme. Colonnes: productLine, revenu_brut_total. "
        "Analyse de rentabilité par ligne de produits.",
    'rotation_stock':
        "Rotation des produits. Colonnes: productCode, rotation. "
        "Indicateur de vitesse de vente (renouvellement du stock). **Utiliser cette table UNIQUEMENT pour la question 'taux de rotation'.**",
    'value_stock_quantity':
        "Valeur du stock. Colonnes: productLine, valeur_stock. "
        "La valeur du stock est déjà calculée au prix d'ACHAT par ligne de produits. "
        "**Utiliser cette table UNIQUEMENT pour la question 'valeur du stock au prix d'achat par ligne de produit'.**",
    'employee_ca':
        "Performance commerciale. Colonnes: SalesRepEmployeeNumber, customerNumber, chiffre_affaire_client. "
        "CA généré par employé via ses clients.",
    'recouvrement':
        "Efficacité recouvrement. Colonnes: customerNumber, montant_total_commande, montant_total_paye, Taux_recouvrement. "
        "Détection des impayés et risque client. **Utiliser cette table en priorité pour les questions 'taux de recouvrement'.**, Taux_recouvrement (par ex. 73.75 -> 73.75%)",
    'customer_orders_summary':
        "Résumé commandes clients. Colonnes: customerNumber, orderNumber, quantityOrdered, orderDate. "
        "Vue simplifiée de l'historique d'achat."
}

# --- Règles spécifiques pour l'agent, basées sur l'expérience et les erreurs corrigées. ---
agent_rules = """
Règles strictes pour la génération de requêtes :
1.  Votre seule tâche est de produire une requête MySQL valide. Ne jamais rien ajouter d'autre.
2.  Pour calculer le chiffre d'affaires ('turnover', 'revenue', 'sales'), vous devez utiliser la formule `SUM(T1.quantityOrdered * T1.priceEach)`. Les tables nécessaires sont `orders` et `orderdetails`.
3.  La colonne 'priceEach' (prix unitaire de vente) est dans la table 'orderdetails'. Ne jamais la chercher dans 'products'.
4.  La colonne 'buyPrice' (prix d'achat) est dans la table 'products'.
5.  Pour lier 'orders' et 'payments', utilisez le 'customerNumber'.
6.  **RÈGLE CRITIQUE:** Pour trouver les employés responsables des clients (ex: 'nombre de clients par employé'), vous DEVEZ OBLIGATOIREMENT joindre la table `employees` (`e`) et la table `customers` (`c`) sur `e.employeeNumber = c.salesRepEmployeeNumber`. C'est la seule jointure correcte. La colonne `salesRepEmployeeNumber` est dans la table `customers`. Ne jamais l'utiliser avec l'alias `e`.
7.  Pour la 'durée moyenne de paiement', calculez `AVG(paymentDate) - AVG(orderDate)`.
8.  **RÈGLE CRITIQUE:** Lorsque vous affichez des informations sur les employés, les clients ou les produits, vous DEVEZ OBLIGATOIREMENT utiliser leur nom (`firstName`, `lastName` pour les employés, `customerName` pour les clients, `productName` pour les produits) au lieu de leur identifiant numérique (`employeeNumber`, `customerNumber`, `productCode`). Les identifiants ne doivent être utilisés que si cela est explicitement demandé par l'utilisateur.
9.  L'agent est bilingue. Utilisez ces correspondances :
    - `turnover`, `revenue`, `sales` -> Calculer `SUM(od.quantityOrdered * od.priceEach)`.
    - `customers`, `clients` -> `customers` (table)
    - `employees` -> `employees` (table)
    - `products` -> `products` (table)
    - `orders` -> `orders` (table)
    - `payments` -> `payments` (table)
    - `price`, `price per unit` -> `priceEach` (colonne)
    - `quantity` -> `quantityOrdered` (colonne)
    - `stock` -> `quantityInStock` (colonne)
    - `product line` -> `productLine` (colonne)
    - `office` -> `offices` (table)
    - `employee sales rep` -> `salesRepEmployeeNumber` (colonne)
10. Utilisez toujours des alias de table (ex: 'o' pour 'orders', 'od' pour 'orderdetails') et assurez-vous de préfixer les colonnes pour éviter les ambiguïtés (ex: `p.productCode`).
11. Limitez toujours les résultats à 10, sauf si un nombre spécifique est demandé.
12. Pour trouver les 'best customers' (meilleurs clients), utilisez la vue `commande_client` jointe à la table `customers` et triez par `chiffre_affaire_client` en ordre décroissant.
13. **SI** la question demande la 'marge en valeur' ou 'marge brute', **ALORS** vous DEVEZ utiliser uniquement la colonne `(SUM(od.quantityOrdered * od.priceEach) - SUM(od.quantityOrdered * p.buyPrice)) AS marge_brute`.
14. **SI** la question demande le 'pourcentage de marge' ou 'taux de marge', **ALORS** vous DEVEZ utiliser uniquement la colonne `(SUM(od.quantityOrdered * od.priceEach) - SUM(od.quantityOrdered * p.buyPrice)) / SUM(od.quantityOrdered * od.priceEach) AS marge_brute_pourcentage`.
15. Ne jamais inclure les deux calculs de marge dans une seule requête, sauf si cela est explicitement demandé par l'utilisateur.
16. **RÈGLE CRITIQUE:** **SI** la question demande le 'taux d'écoulement du stock', **ALORS** vous devez OBLIGATOIREMENT utiliser la table `ecoulement_stock` et sélectionner les colonnes `productName` et `taux_ecoulement_stock`. AUCUNE jointure avec la table `products` n'est nécessaire.
17. **RÈGLE CRITIQUE:** **SI** la question demande le 'taux de rotation du stock', **ALORS** vous devez OBLIGATOIREMENT utiliser la table `rotation_stock` et la colonne `rotation`.
18. **RÈGLE CRITIQUE (CORRECTION):** **SI** la question demande la 'valeur du stock' au prix d'achat, **ALORS** vous devez OBLIGATOIREMENT utiliser la table `value_stock_quantity` et effectuer un `GROUP BY productLine` en utilisant `SUM(vs.valeur_stock)`. AUCUNE jointure avec d'autres tables n'est nécessaire.
19. **RÈGLE CRITIQUE:** **SI** la question demande le 'taux de recouvrement', **ALORS** vous devez OBLIGATOIREMENT utiliser la table `recouvrement` et la joindre à la table `customers` sur `customerNumber` pour obtenir le nom du client. Vous devez aussi trier le résultat en utilisant la colonne `Taux_recouvrement`.
20. Pour les autres métriques pré-calculées, utilisez directement les tables correspondantes (`marge_produit`, `value_stock_quantity`).
21. **RÈGLE CRITIQUE:** **SI** la question demande la 'valeur du stock au prix de vente moyen' ou des termes similaires, **ALORS** vous DEVEZ OBLIGATOIREMENT :
    - Utiliser une sous-requête pour calculer `AVG(od.priceEach)` pour chaque `productCode` de la table `orderdetails`.
    - Joindre cette sous-requête avec la table `products` sur `productCode`.
    - Calculer la somme `SUM(t1.average_price * p.quantityInStock)` et regrouper par `p.productLine`.
    - NE PAS UTILISER la table `value_stock_quantity` pour cette question.
22. **RÈGLE CRITIQUE:** **SI** la question demande la 'valeur du stock au prix de vente maximal' ou des termes similaires, **ALORS** vous DEVEZ OBLIGATOIREMENT :
    - Utiliser une sous-requête pour calculer `MAX(od.priceEach)` pour chaque `productCode` de la table `orderdetails`.
    - Joindre cette sous-requête avec la table `products` sur `productCode`.
    - Calculer la somme `SUM(t1.max_price * p.quantityInStock)` et regrouper par `p.productLine`.
    - NE PAS UTILISER la table `value_stock_quantity` pour cette question.
23. **RÈGLE CRITIQUE (NOUVELLE):** **SI** la question demande la 'valeur du stock au prix de vente minimal' ou des termes similaires, **ALORS** vous DEVEZ OBLIGATOIREMENT :
    - Utiliser une sous-requête pour calculer `MIN(od.priceEach)` pour chaque `productCode` de la table `orderdetails`.
    - Joindre cette sous-requête avec la table `products` sur `productCode`.
    - Calculer la somme `SUM(t1.min_price * p.quantityInStock)` et regrouper par `p.productLine`.
    - NE PAS UTILISER la table `value_stock_quantity` pour cette question.
24. **RÈGLE CRITIQUE (NOUVELLE):** **SI** la question demande des informations sur les commandes (`orders`), les clients (`customers`) ou le chiffre d'affaires (`turnover`) par bureau (`office`), **ALORS** vous DEVEZ OBLIGATOIREMENT utiliser cette chaîne de jointures : `offices` (`o`) -> `employees` (`e`) -> `customers` (`c`) -> `orders` (`ord`). La jointure se fait sur `o.officeCode = e.officeCode`, `e.employeeNumber = c.salesRepEmployeeNumber`, et `c.customerNumber = ord.customerNumber`.
25. **RÈGLE CRITIQUE (AJOUTÉE):** Si la question demande le 'nombre total de commandes par bureau', vous DEVEZ OBLIGATOIREMENT joindre `offices`, `employees`, `customers` et `orders` en utilisant les clés de jointure suivantes : `o.officeCode = e.officeCode`, `e.employeeNumber = c.salesRepEmployeeNumber`, et `c.customerNumber = ord.customerNumber`. La colonne à compter est `ord.orderNumber`, et le regroupement se fait par `o.city` ou `o.officeCode`.
26. **RÈGLE CRITIQUE (AJOUTÉE):** Pour compter des entités (employés, clients, etc.) dans une requête qui joint la table `orders` à la table `orderdetails`, vous DEVEZ **toujours** utiliser `COUNT(DISTINCT <colonne_ID>)`. Par exemple, pour compter les employés, utilisez `COUNT(DISTINCT e.employeeNumber)`.
27. **RÈGLE CRITIQUE (AJOUTÉE):** Pour calculer le 'montant moyen des commandes' (`average order amount`), vous DEVEZ d'abord calculer la somme totale pour chaque commande. Pour ce faire, utilisez une sous-requête (ou CTE) qui calcule `SUM(od.quantityOrdered * od.priceEach)` groupé par `od.orderNumber` et `c.customerNumber`, puis effectuez une moyenne (`AVG()`) sur ces totaux dans la requête principale.
28. **RÈGLE CRITIQUE (NOUVELLE):** **SI** la question demande 'qui sont les managers', **ALORS** vous DEVEZ OBLIGATOIREMENT utiliser la clause `WHERE reportsTo IS NULL` sur la table `employees` et ne faire AUCUNE jointure inutile.
29. **RÈGLE CRITIQUE (AJOUTÉE):** Lorsque vous calculez des agrégats basés sur des résultats de sous-requêtes, **VOUS NE DEVEZ JAMAIS** utiliser une fonction d'agrégation dans une autre. Par exemple, `SUM(AVG(...))` est incorrect. Calculez d'abord la moyenne dans une sous-requête, puis utilisez ce résultat dans la requête principale.
30. **RÈGLE CRITIQUE (AJOUTÉE):** **Pour compter le nombre de commandes ou obtenir des informations sur les commandes par ville, vous DEVEZ OBLIGATOIREMENT joindre la table `orders` (`o`) et la table `customers` (`c`) sur `c.customerNumber = o.customerNumber`, et grouper par `c.city`. La colonne `city` est dans la table `customers`.**
31. **RÈGLE CRITIQUE (NOUVELLE):** **Pour identifier les clients dont le montant total des commandes dépasse leur limite de crédit, vous DEVEZ OBLIGATOIREMENT calculer la somme des commandes par client dans une clause `GROUP BY`, puis utiliser une clause `HAVING` pour comparer ce total à la colonne `c.creditLimit`. N'utilisez JAMAIS de fonction d'agrégation dans une clause `WHERE`.**
32. **RÈGLE CRITIQUE (NOUVELLE):** Lorsque vous utilisez une clause `GROUP BY`, toutes les colonnes non agrégées figurant dans votre clause `SELECT` doivent également être incluses dans la clause `GROUP BY` pour se conformer au mode SQL `ONLY_FULL_GROUP_BY`. Pour la question des clients et de leur limite de crédit, cela signifie que `c.customerName`, `c.country`, et `c.creditLimit` DOIVENT TOUS être dans le `GROUP BY`.
33. **RÈGLE CRITIQUE (NOUVELLE):** **Pour identifier les clients dont les commandes impayées dépassent leur limite de crédit, vous DEVEZ OBLIGATOIREMENT :**
    - Joindre les tables `customers` (`c`), `orders` (`o`), `orderdetails` (`od`) et `payments` (`p`). Utilisez `LEFT JOIN` pour `payments` car certains clients peuvent ne pas avoir de paiements.
    - Regrouper les résultats par `c.customerNumber` (et les autres colonnes non agrégées dans le `SELECT` comme `c.customerName`, `c.country`, `c.creditLimit`).
    - Calculer le solde dû (`SUM(od.quantityOrdered * od.priceEach) - IFNULL(SUM(p.amount), 0)`) et l'utiliser dans la clause `HAVING` pour le comparer à `c.creditLimit`. Utilisez `IFNULL` pour gérer les clients sans paiement.
34. **RÈGLE CRITIQUE (CORRIGÉE) :** **SI** la question demande la 'marge moyenne par ligne de produit', **ALORS** vous DEVEZ OBLIGATOIREMENT utiliser la table `marge_produit`. La requête doit simplement sélectionner `productLine` et la moyenne (`AVG`) de la colonne `revenu_brut` (qui représente la marge de chaque produit). Vous devez ensuite regrouper les résultats par `productLine`.
35. **SI** la question demande les 'quantités commandées par bureau', 'total des commandes par bureau' ou d'autres métriques liées à la quantité et au bureau, vous DEVEZ OBLIGATOIREMENT utiliser la chaîne de jointures complète `offices` -> `employees` -> `customers` -> `orders` -> `orderdetails` et utiliser `SUM(od.quantityOrdered)`.
"""

# --- Configuration de la base de données ---
import os
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv
import streamlit as st

load_dotenv()

@st.cache_resource
def get_db_connection():
    if "STREAMLIT_SERVER_PORT" in os.environ:
        secrets = st.secrets
    else:
        secrets = os.environ

    try:
        connection = mysql.connector.connect(
            host=secrets["DB_HOST"],
            user=secrets["DB_USER"],
            password=secrets["DB_PASSWORD"],
            port=secrets["DB_PORT"],
            database=secrets["DB_DATABASE"]
        )
        if connection.is_connected():
            return connection
    except Error as e:
        st.error(f"Erreur lors de la connexion à MySQL: {e}")
        return None
    

# --- Configuration de l'agent LLM (Groq) ---
def setup_groq_client():
    """Initialise et renvoie le client Groq."""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY non trouvée dans les variables d'environnement.")
    return Groq(api_key=api_key)

# --- Fonction pour récupérer le schéma de la base de données ---
def get_database_schema(connection):
    """
    Récupère le schéma des tables et colonnes de la base de données.
    """
    schema_string = ""
    try:
        cursor = connection.cursor()
        cursor.execute("SHOW TABLES")
        tables = [table[0] for table in cursor.fetchall()]

        for table_name in tables:
            schema_string += f"Table: {table_name}\n"
            cursor.execute(f"SHOW COLUMNS FROM `{table_name}`")
            columns = cursor.fetchall()
            for column in columns:
                schema_string += f"  - {column[0]} ({column[1]})\n"
            schema_string += "\n"

        cursor.close()
    except Error as e:
        print(f"Erreur lors de la récupération du schéma: {e}")
        return ""

    return schema_string


# --- Logique de l'agent ---
def generate_sql_query(user_question, db_schema, groq_client):
    """
    Génère une requête SQL à partir d'une question utilisateur et du schéma de la BDD.
    """
    # Crée une chaîne de caractères à partir de la documentation des tables
    table_docs_str = "\n".join([
        f"Table '{table_name}': {doc}" for table_name, doc in table_documentation.items()
    ])

    system_prompt = f"""
    Your task is to act as an expert MySQL query generator.
    Your output MUST BE the raw, executable MySQL query ONLY. I repeat: ONLY the SQL query.
    DO NOT include any text, explanations, comments, or markdown formatting.
    
    Database Schema:
    {db_schema}

    Table Documentation:
    {table_docs_str}

    Strict Rules for Query Generation:
    {agent_rules}

    Example of the expected output format:
    ---
    Question: What is the total turnover?
    SQL Query: SELECT SUM(od.quantityOrdered * od.priceEach) AS total_turnover FROM orderdetails AS od;
    ---

    Now, for this new question, provide ONLY the SQL query:
    Question: {user_question}
    SQL Query:
    """
    
    try:
        chat_completion = groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
            ],
            model="llama3-8b-8192",
            temperature=0,
            max_tokens=500
        )
        return chat_completion.choices[0].message.content.strip()
    except Exception as e:
        print(f"Erreur lors de la génération de la requête SQL: {e}")
        return None


def execute_sql_query(connection, query):
    """Exécute une requête SQL et renvoie les résultats."""
    results = None
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute(query)
        results = cursor.fetchall()
        cursor.close()
    except Error as e:
        print(f"Erreur lors de l'exécution de la requête: {e}")
    
    return results


def format_results_markdown(results):
    """
    Formate les résultats d'une requête SQL en un tableau Markdown.
    """
    if not results:
        return "**Aucun résultat trouvé.**"
    
    column_names = list(results[0].keys())
    header = " | ".join(column_names)
    divider = " | ".join(["---"] * len(column_names))
    
    table_rows = [header, divider]
    for row in results:
        table_rows.append(" | ".join([str(row[col]) for col in column_names]))
    
    return "\n".join(table_rows)

def generate_example_questions(db_schema, groq_client):
    """
    Génère dynamiquement des questions d'exemple en français basées sur le schéma de la BDD.
    """
    system_prompt = f"""
    Vous êtes un expert en analyse de données et en SQL. Votre tâche est de générer 4 questions d'analyse de données que l'on pourrait poser à une base de données MySQL. Les questions doivent être diverses, pertinentes et basées sur le schéma de la base de données fourni ci-dessous.
    Chaque question doit être formulée en français comme si elle provenait d'un utilisateur final non technique.
    Le résultat doit être une liste de 4 questions numérotées, SANS aucun autre texte, explication ou formatage.

    Schéma de la base de données :
    {db_schema}

    Exemple de sortie attendue :
    1. Quelle est notre chiffre d'affaires total pour l'année dernière ?
    2. Quels sont nos 5 produits les plus vendus ?
    3. Où sont situés nos employés ?
    4. Y a-t-il des clients dont le solde est impayé ?
    
    Maintenant, générez 4 questions basées sur le schéma de la base de données ClassicModels :
    """
    
    try:
        chat_completion = groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
            ],
            model="llama3-8b-8192",
            temperature=0.8,
            max_tokens=500
        )
        
        # Le résultat est une chaîne de caractères, nous la divisons en une liste de questions
        generated_text = chat_completion.choices[0].message.content.strip()
        questions = [q.strip() for q in generated_text.split('\n') if q.strip()]
        return questions
        
    except Exception as e:
        print(f"Erreur lors de la génération des questions d'exemple: {e}")
        return [
            "Quel est le chiffre d'affaire en 2004 ?",
            "Qui sont nos meilleurs clients ?",
            "Où sont localisés nos meilleurs clients ?",
            "Dans quels mois de l'année fait-on plus de chiffre d'affaire ?"
        ]

def translate_questions(questions_list, target_language, groq_client):
    """
    Traduit une liste de questions d'une langue source à une langue cible.
    """
    # Crée un prompt pour l'agent, lui demandant de traduire une liste de questions.
    # On lui donne une liste en entrée et on attend une liste en sortie.
    system_prompt = f"""
    Vous êtes un traducteur de texte expert. Votre tâche est de traduire une liste de questions d'analyse de données du français vers l'anglais. Le résultat doit être une liste numérotée de questions traduites. Ne pas inclure de texte d'introduction ou de conclusion, seulement les questions.

    Questions à traduire :
    {questions_list}

    Traduction en anglais :
    """
    
    try:
        chat_completion = groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
            ],
            model="llama3-8b-8192",
            temperature=0.2, # Une température basse pour une traduction fidèle
            max_tokens=500
        )
        
        # Le résultat est une chaîne de caractères, nous la divisons en une liste de questions
        generated_text = chat_completion.choices[0].message.content.strip()
        translated_questions = [q.strip() for q in generated_text.split('\n') if q.strip()]
        return translated_questions
        
    except Exception as e:
        print(f"Erreur lors de la traduction des questions: {e}")
        # En cas d'erreur, renvoyer une traduction par défaut
        return [
            "What is the turnover in 2004?",
            "Who are our best customers?",
            "Where are our best customers located?",
            "In which months of the year do we make more turnover?"
        ]

# --- Fonction principale ---
def main():
    """
    Fonction principale de l'agent SQL.
    """
    # 1. Initialisation
    connection = get_db_connection()
    if not connection:
        return
    
    groq_client = setup_groq_client()

    # 2. Récupération du schéma de la BDD
    db_schema = get_database_schema(connection)
    if not db_schema:
        print("Impossible de récupérer le schéma de la base de données. Abandon.")
        connection.close()
        return

    # 3. Génération dynamique des questions d'exemple
    french_questions = generate_example_questions(db_schema, groq_client)
    english_questions = translate_questions("\n".join(french_questions), "en", groq_client)
    
    french_questions_str = "\n".join([f"- {q}" for q in french_questions])
    english_questions_str = "\n".join([f"- {q}" for q in english_questions])

    # 4. Affichage du message de bienvenue et des exemples
    welcome_message = f"""
Salut ! Je suis THE SQLer, un agent IA expert en SQL et DataViz. Je suis là pour vous aider à requêter la base de données ClassicModels en langage naturel.

Exemples de questions:
{french_questions_str}

Example questions:
{english_questions_str}
    
Comment puis-je vous aider aujourd'hui ?
"""
    print(welcome_message)
    
    # 5. Boucle principale de l'agent
    while True:
        user_question = input("\nVotre question (ou 'quitter' pour arrêter) : ")
        if user_question.lower() == 'quitter':
            break

        # 6. Génération de la requête SQL
        sql_query = generate_sql_query(user_question, db_schema, groq_client)
        
        if sql_query:
            print(f"\nRequête SQL générée :\n```sql\n{sql_query}\n```")
            
            # 7. Exécution de la requête
            query_results = execute_sql_query(connection, sql_query)
            
            # 8. Affichage des résultats en Markdown
            if query_results:
                markdown_output = format_results_markdown(query_results)
                print("\nRésultats de la base de données :\n")
                print(markdown_output)

                # 9. Appel du module de visualisation
                chart_path = generate_visualization(user_question, query_results, groq_client)
                if chart_path:
                    print(f"\nUn graphique a été créé pour ces résultats. Fichier : {chart_path}")
                else:
                    print("\nImpossible de créer un graphique avec ces données.")
            else:
                print("\n**La requête n'a renvoyé aucun résultat ou une erreur est survenue.**")

    # 10. Fermeture de la connexion
    if connection.is_connected():
        connection.close()


if __name__ == "__main__":
    main()
