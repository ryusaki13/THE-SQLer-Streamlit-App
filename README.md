# THE SQLer : Agent IA pour des requêtes SQL et visualisations  

## 📝 Résumé du projet  
**THE SQLer** est une application web interactive construite avec **Streamlit** qui permet aux utilisateurs de dialoguer avec une base de données **MySQL** en langage naturel.  
Au lieu d'écrire des requêtes SQL complexes, l'utilisateur pose une question en français ou en anglais, et un l'agent IA génère,
exécute et affiche les résultats sous forme de tableau et de visualisation de données.  

  Ce projet a pour ambition de démocratiser l'accès aux données, en rendant l'analyse plus simple et intuitive pour les non-experts.
Il met également en lumière le rôle de l’IA comme levier de productivité, permettant aux professionnels de la donnée de décupler leur efficacité, 
d’optimiser leurs analyses et de gagner un temps précieux dans leurs missions quotidiennes.

---

## 🎯 Objectif du projet  
L'objectif principal est de créer un outil de **Business Intelligence (BI) conversationnel**, en s'appuyant sur les capacités de la génération de langage par IA.  

Le projet vise à :  
- **Simplifier l'accès aux données** : permettre à n'importe quel utilisateur de poser des questions à une base de données sans connaissance du langage SQL.  
- **Fournir des analyses instantanées** : générer et visualiser les résultats rapidement pour une prise de décision agile.  
- **Améliorer l'expérience utilisateur** : rendre l'interaction avec la base de données plus fluide et intuitive.  

---

## Fonctionnalités de l’application

L’application THE SQLer propose plusieurs fonctionnalités clés pour faciliter l’analyse de données en langage naturel :

1. Dialogue en langage naturel : poser une question directement dans l’interface Streamlit, sans écrire une seule ligne de SQL.

2. Génération automatique de requêtes SQL : un agent IA (**llama-3.1-8b-instant** de Groq) convertit la question en une requête SQL optimisée et sécurisée.

3. Exécution et affichage des résultats : les données sont extraites de la base MySQL et affichées sous forme de tableau lisible.

4. Visualisations dynamiques : un second agent IA génère automatiquement le code pour afficher un graphique pertinent via matplotlib.

- Export des résultats : toutes les sorties (tableaux, résultats de requêtes, visualisations) peuvent être téléchargées au format CSV ou copiées pour un usage ultérieur.
- Interface intuitive : toutes les données et graphiques sont accessibles directement depuis l’application Streamlit.

---

## 🛠️ Outils et technologies  

### Base de données  
- **MySQL** : Célèbre base de données Mysql Classicmodels  - <a href ="https://github.com/ryusaki13/Classic-Models-Analysis-SQL-DataViz-/blob/main/Classic%20models%20tables.sql">Console_GROQ</a>
- **mysql-connector-python**

### Backend & IA 
- L’application a été développée entièrement dans un environnement virtuel Python (Isolation, gestion des dépendances, réproductibilité)
- **Groq Cloud** : Plateforme avec modèles LLM **OpenSource** - <a href ="https://console.groq.com/home">Console_GROQ</a> 
- **llama-3.1-8b-instant** : utilisé pour générer les requêtes SQL et les visualisations.
  
### Frontend & UI  
- **Streamlit**

---

## 🚧 Défis, limites et solutions  

### 🔹 Lenteur au démarrage  
- **Problème** : le temps de chargement initial était élevé, car la connexion à la base et la récupération du schéma se faisaient à chaque rechargement.  
- ✅ **Solution** : utilisation du cache Streamlit (`@st.cache_resource` et `@st.cache_data`).  

### 🔹 Risques de sécurité (SQL Injection)  
- **Problème** : exécuter des requêtes générées par l'IA est risqué.  
- ✅ **Solution** : règles strictes dans le prompt de l'IA pour limiter les requêtes et empêcher les actions non désirées.  

### 🔹 Complexité de certaines requêtes  
- **Problème** : certains calculs métiers (taux de rotatio
