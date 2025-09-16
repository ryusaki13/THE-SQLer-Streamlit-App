# THE SQLer : Agent IA pour des requêtes SQL et visualisations  

## Résumé du projet  
**THE SQLer** est une application web interactive construite avec **Streamlit** qui permet aux utilisateurs de dialoguer avec une base de données **MySQL** en langage naturel.  
Au lieu d'écrire des requêtes SQL complexes, l'utilisateur pose une question en français ou en anglais, et l'agent IA génère,
exécute et affiche les résultats sous forme de tableau et de visualisation de données.

Ce projet s’inscrit dans la continuité de notre précédent travail, où nous avions analysé la base de données MySQL Classicmodels en écrivant des requêtes SQL manuelles, en calculant des KPIs pertinents, puis en construisant un dashboard interactif avec Power BI pour la visualisation.
Avec **THE SQLer**, nous franchissons une nouvelle étape : l’application intègre désormais la génération automatique de requêtes et de visualisations en langage naturel, réunissant en une seule interface tout le processus d’analyse, de la question utilisateur à l’affichage des résultats. - <a href ="https://github.com/ryusaki13/Classic-Models-Analysis-SQL-DataViz-/tree/main">Précédent_projet</a>

Ce projet a pour ambition de démocratiser l'accès aux données, en rendant l'analyse plus simple et intuitive pour les non-experts.
Il met également en lumière le rôle de l’IA comme levier de productivité, permettant aux professionnels de la donnée de décupler leur efficacité, 
d’optimiser leurs analyses et de gagner un temps précieux dans leurs missions quotidiennes.

---

## Objectif du projet  
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

## Outils et techniques  

### Base de données  
- **MySQL** : Célèbre base de données Classicmodels  - <a href ="https://github.com/ryusaki13/Classic-Models-Analysis-SQL-DataViz-/blob/main/Classic%20models%20tables.sql">Base_Classicmodels</a>
- **mysql-connector-python**

### Backend & IA 
- L’application a été développée entièrement dans un environnement virtuel Python (Isolation, gestion des dépendances, réproductibilité)
- **Groq Cloud** : Plateforme avec modèles LLM **OpenSource** - <a href ="https://console.groq.com/home">Console_GROQ</a> 
- **llama-3.1-8b-instant** : utilisé pour générer les requêtes SQL et les visualisations.
- **Railway** : déploiement en production de la base de données pour une utilisation accessible hors local - <a href ="https://railway.com/dashboard">Console_Railway</a>
 
### Frontend & UI  
- **Streamlit**

---

## Potentielles améliorations 

- Visualisations interactives : utiliser **Plotly** ou **Altair** pour ajouter zoom, filtres et infobulles.

- Refonte de l’UI : rendre l’interface Streamlit plus ergonomique et moderne.

- Multi-bases de données : étendre la compatibilité à **PostgreSQL**, **SQL Server**, etc.

- Gestion des erreurs : fournir des messages clairs et des solutions de repli en cas d’échec.

- Personnalisation utilisateur : sauvegarde des requêtes fréquentes et génération de rapports automatisés.

- Mémoire longue : mettre en place un historique de discussions pour que l’IA se souvienne des questions précédentes et facilite les analyses itératives.

- Sécurité renforcée : ajout d’un contrôle des accès et gestion des permissions utilisateurs.

## Démo THE SQLer
https://github.com/user-attachments/assets/b5f82378-ca4e-40fc-9212-67496d6091c9
