# CI/CD avec GitHub Actions

Ce projet utilise GitHub Actions pour l'intégration continue (CI) et le déploiement continu (CD). Cette documentation explique les workflows configurés et comment les utiliser efficacement.

## Structure du pipeline CI/CD

Le pipeline CI/CD est composé de plusieurs workflows GitHub Actions :

1. **Tests** (`.github/workflows/tests.yml`)
   - Exécution des tests unitaires et d'intégration
   - Vérification de la couverture du code
   - Vérification du formatage et du style

2. **Analyse de sécurité** (`.github/workflows/security.yml`)
   - Analyse des dépendances vulnérables
   - Détection de secrets exposés
   - Analyse statique du code

3. **Qualité du code** (`.github/workflows/code-quality.yml`)
   - Analyse SonarCloud
   - Validation du schéma OpenAPI

4. **Déploiement** (`.github/workflows/deploy.yml`)
   - Construction et push des images Docker
   - Déploiement en staging
   - Déploiement en production

5. **Gestion des dépendances** (`.github/dependabot.yml`)
   - Mises à jour automatiques des dépendances Python
   - Mises à jour des images Docker
   - Mises à jour des actions GitHub

## Déclencheurs des workflows

- **Tests, Sécurité et Qualité du code** : déclenchés sur les push vers `main` et `develop`, ainsi que sur toutes les pull requests vers ces branches
- **Déploiement en staging** : déclenché sur les push vers `main`
- **Déploiement en production** : déclenché sur les tags commençant par `v` (ex: `v1.0.0`)
- **Analyses de sécurité planifiées** : exécutées hebdomadairement (chaque dimanche)
- **Analyse de qualité de code planifiée** : exécutée chaque lundi matin

## Secrets nécessaires

Pour que les workflows fonctionnent correctement, vous devez configurer les secrets suivants dans votre repository GitHub :

### Pour Docker Hub
- `DOCKERHUB_USERNAME` : Votre nom d'utilisateur Docker Hub
- `DOCKERHUB_TOKEN` : Votre token d'accès Docker Hub

### Pour le déploiement en staging
- `STAGING_HOST` : Adresse IP ou nom d'hôte du serveur de staging
- `STAGING_USER` : Utilisateur SSH pour se connecter au serveur de staging
- `STAGING_SSH_KEY` : Clé SSH privée pour l'authentification

### Pour le déploiement en production
- `PRODUCTION_HOST` : Adresse IP ou nom d'hôte du serveur de production
- `PRODUCTION_USER` : Utilisateur SSH pour se connecter au serveur de production
- `PRODUCTION_SSH_KEY` : Clé SSH privée pour l'authentification

### Pour SonarCloud
- `SONAR_TOKEN` : Token d'accès SonarCloud

## Environnements GitHub

Le projet utilise les environnements GitHub pour contrôler les déploiements :

- **staging** : Environnement de pré-production pour tester les fonctionnalités
- **production** : Environnement de production

Vous pouvez configurer des règles de protection spécifiques pour chaque environnement, comme exiger des approbations manuelles avant les déploiements en production.

## Gestion des versions et déploiement

### Processus de versioning

1. Le développement se fait sur des branches de fonctionnalités
2. Les pull requests sont fusionnées dans `develop`
3. Quand une version est prête pour le staging, `develop` est fusionné dans `main`
4. Pour déployer en production, créez un tag avec le format `vX.Y.Z` (suivant le [Semantic Versioning](https://semver.org/))

### Création d'une nouvelle version

```bash
# Assurez-vous d'être sur main et à jour
git checkout main
git pull

# Créez un tag pour la nouvelle version
git tag -a v1.0.0 -m "Version 1.0.0"

# Poussez le tag pour déclencher le déploiement en production
git push origin v1.0.0
```

## Personnalisation des workflows

### Modification des tests

Le workflow de tests utilise pytest avec les configurations suivantes :
- Tests unitaires et d'intégration dans le répertoire `tests/`
- Rapport de couverture avec un seuil minimal de 80%
- Vérification du formatage avec Black, Flake8 et isort

Pour modifier la configuration des tests, éditez le fichier `.github/workflows/tests.yml`.

### Modification des déploiements

Le workflow de déploiement utilise Docker pour construire et déployer l'application. Pour personnaliser le déploiement :

1. Modifiez les scripts de déploiement dans `.github/workflows/deploy.yml`
2. Ajustez les commandes SSH exécutées sur les serveurs cibles
3. Configurez les environnements GitHub appropriés

## Bonnes pratiques

1. **Ne jamais commiter de secrets** dans le code source
2. **Utiliser les pull requests** pour toutes les modifications
3. **Examiner les rapports de tests et de sécurité** avant de fusionner
4. **Suivre le Semantic Versioning** pour les numéros de version
5. **Documenter les modifications** dans les messages de commit et les descriptions de PR