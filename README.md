# FastAPI Template

![Tests](https://github.com/yourusername/fastapi-template/workflows/Tests/badge.svg)
![Security Analysis](https://github.com/yourusername/fastapi-template/workflows/Security%20Analysis/badge.svg)
![Deploy](https://github.com/yourusername/fastapi-template/workflows/Deploy/badge.svg)

Un template moderne, prêt pour la production, pour les projets FastAPI avec authentification, CRUD, mise en cache, limitation de débit, et bien plus.

## ✨ Fonctionnalités

- **🚀 FastAPI Framework**: Haute performance, facile à apprendre, rapide à coder
- **🔒 JWT Authentication**: Authentification sécurisée avec tokens de rafraîchissement
- **👮 RBAC**: Contrôle d'accès basé sur les rôles
- **🐘 PostgreSQL & MySQL**: Support pour plusieurs bases de données
- **🧩 SQLAlchemy ORM**: ORM de base de données avec la dernière syntaxe SQLAlchemy 2.0
- **📈 Alembic Migrations**: Versionnement et migrations de base de données
- **✅ Pydantic Validation**: Validation de schéma avec Pydantic v2
- **📚 OpenAPI Documentation**: Documentation API auto-générée
- **⚡ Redis Caching**: Mise en cache haute performance
- **🛡️ Rate Limiting**: Protection contre les abus
- **🐳 Docker**: Conteneurisation pour le développement et la production
- **🔄 CI/CD**: Workflows GitHub Actions pour les tests et le déploiement
- **📝 Logging**: Logging JSON structuré
- **🧪 Testing**: Configuration pytest avec rapports de couverture
- **💎 Code Quality**: Configuration Black, Flake8, mypy, isort
- **🔐 Security**: Analyse de sécurité et bonnes pratiques

## 🚀 Démarrage Rapide

### Prérequis

- Docker et Docker Compose
- Python 3.11 ou supérieur (pour le développement local)
- Git

### Installation

1. **Cloner le dépôt et initialiser le projet**:
```bash
git clone https://github.com/Ibrahimzongo/fastapi-template.git mon-projet
cd mon-projet
python init_project.py  # Script d'initialisation automatique
```

2. **Créer un fichier `.env`**:
```bash
cp .env.example .env
# Éditer .env avec votre configuration
```

3. **Démarrer l'environnement de développement**:
```bash
docker-compose up --build
```

4. **Accéder à l'API à** http://localhost:8000

5. **Accéder à la documentation de l'API à** http://localhost:8000/docs

### Développement Local (sans Docker)

Pour le développement local sans Docker:

```bash
# Créer un environnement virtuel
python -m venv venv
source venv/bin/activate  # Sur Windows: venv\Scripts\activate

# Installer les dépendances
pip install -r requirements/dev.txt

# Définir les variables d'environnement
export DATABASE_TYPE=postgresql
export DATABASE_HOST=localhost
export DATABASE_PORT=5432
export DATABASE_USER=postgres
export DATABASE_PASSWORD=password123
export DATABASE_NAME=fastapi_db
export SECRET_KEY=your-secret-key

# Exécuter l'application
uvicorn src.main:app --reload
```

## 📦 Structure du Projet

```
fastapi-template/
├── .github/                   # Workflows GitHub Actions
├── alembic/                   # Migrations de base de données
├── docker/                    # Configurations Docker
│   ├── dev/                   # Config Docker de développement
│   └── prod/                  # Config Docker de production
├── src/                       # Code source de l'application
│   ├── api/                   # Routes et endpoints API
│   ├── core/                  # Configurations de base
│   ├── db/                    # Modèles et repositories de base de données
│   ├── models/                # Modèles SQLAlchemy
│   └── schemas/               # Schémas Pydantic
├── tests/                     # Suite de tests
├── scripts/                   # Scripts utilitaires
└── docs/                      # Documentation
```

## 🔄 Migrations de Base de Données

Pour gérer les migrations de base de données:

```bash
# Initialiser la base de données
python scripts/migrate.py init

# Créer une nouvelle migration
python scripts/migrate.py create --message "description"

# Appliquer les migrations
python scripts/migrate.py migrate

# Annuler les migrations
python scripts/migrate.py rollback
```

## 🛠️ Utilisation avec Make

Le projet inclut un Makefile pour faciliter les tâches courantes:

```bash
# Afficher l'aide
make help

# Construire les conteneurs
make build

# Démarrer les conteneurs
make up

# Arrêter les conteneurs
make down

# Afficher les logs
make logs

# Exécuter les tests
make test

# Formater le code
make fmt

# Linter le code
make lint
```

## 🔒 Authentification

L'API utilise des tokens JWT pour l'authentification avec un mécanisme de token de rafraîchissement.

```bash
# Enregistrer un nouvel utilisateur
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "username": "username",
    "password": "password123",
    "full_name": "User Name"
  }'

# Connexion
curl -X POST http://localhost:8000/api/v1/auth/login \
  -d "username=username&password=password123"

# Accéder à un endpoint protégé
curl -X GET http://localhost:8000/api/v1/posts/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"

# Rafraîchir le token
curl -X POST http://localhost:8000/api/v1/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{"refresh_token": "YOUR_REFRESH_TOKEN"}'
```

## 🚢 Déploiement

### Préparation du Déploiement

1. **Configuration des Secrets GitHub**:
   
   Configurez les secrets suivants dans votre dépôt GitHub:
   
   - `DOCKERHUB_USERNAME`: Votre nom d'utilisateur Docker Hub
   - `DOCKERHUB_TOKEN`: Votre token Docker Hub
   - `STAGING_HOST`: Hôte de staging
   - `STAGING_USER`: Utilisateur SSH de staging
   - `STAGING_SSH_KEY`: Clé SSH de staging
   - `PRODUCTION_HOST`: Hôte de production
   - `PRODUCTION_USER`: Utilisateur SSH de production
   - `PRODUCTION_SSH_KEY`: Clé SSH de production

2. **Déploiement en Production**:
   
   Pour déployer en production, créez un tag et poussez-le:
   
   ```bash
   git tag v1.0.0
   git push origin v1.0.0
   ```

## 🔧 Environnements

Le template supporte trois environnements:

- **Development**: Pour le développement local
- **Staging**: Pour les tests avant production
- **Production**: Pour l'environnement de production

## 📚 Documentation

La documentation complète est disponible dans le dossier [docs/](docs/):

- [Documentation de l'API](docs/api.md)
- [Documentation d'authentification](docs/auth.md)
- [Documentation de mise en cache](docs/caching.md)
- [Documentation CI/CD](docs/ci-cd.md)
- [Documentation de déploiement](docs/deployment.md)

## 🤝 Contribution

1. Forker le dépôt
2. Créer une branche de fonctionnalité: `git checkout -b feature/ma-fonctionnalité`
3. Commiter vos changements: `git commit -am 'Ajouter ma fonctionnalité'`
4. Pousser vers la branche: `git push origin feature/ma-fonctionnalité`
5. Soumettre une pull request

## 📄 Licence

Ce projet est sous licence MIT - voir le fichier [LICENSE](LICENSE) pour plus de détails.