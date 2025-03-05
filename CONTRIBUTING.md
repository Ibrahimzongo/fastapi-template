# Guide de contribution

Merci de contribuer à FastAPI Template ! Voici comment vous pouvez contribuer efficacement.

## Configuration de l'environnement de développement

1. Forker le dépôt
2. Cloner votre fork : `git clone https://github.com/Ibrahimzongo/fastapi-template.git`
3. Installer les dépendances : `pip install -r requirements/dev.txt`
4. Exécuter les tests pour vérifier que tout fonctionne : `pytest`

## Processus de contribution

1. Créer une branche pour votre fonctionnalité : `git checkout -b feature/ma-fonctionnalite`
2. Effectuer vos modifications
3. Ajouter des tests pour votre fonctionnalité
4. S'assurer que tous les tests passent : `pytest`
5. Formater le code : `black src tests`
6. Commiter vos changements : `git commit -am 'feat: ajouter ma fonctionnalité'`
7. Pousser vers votre branche : `git push origin feature/ma-fonctionnalite`
8. Soumettre une Pull Request vers la branche `develop`

## Conventions de codage

- Suivre le style PEP 8
- Utiliser les annotations de type
- Ajouter des docstrings pour toutes les fonctions/classes
- Suivre les conventions de commit [Conventional Commits](https://www.conventionalcommits.org/)

## Tests

- Tous les nouveaux modules doivent avoir des tests unitaires
- Maintenir une couverture de code d'au moins 80%