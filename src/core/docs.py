from typing import Dict

from core.config import settings

description = """
# 🚀 FastAPI Template API

Cette API fournit une base solide pour démarrer vos projets FastAPI avec :

## Fonctionnalités

### 🔐 Authentification & Autorisation
* JWT Authentication
* Gestion des rôles (Admin, Manager, User)
* Refresh tokens
* Sessions sécurisées

### 📝 Gestion de Posts
* CRUD complet
* Système de tags
* Pagination
* Filtrage

### 🛠 Caractéristiques Techniques
* Support MySQL et PostgreSQL
* Logging structuré
* Tests automatisés
* Documentation interactive
* Monitoring avec Prometheus

## Notes
* Toutes les dates sont en UTC
* Les réponses sont paginées par défaut (limite = 10)
* Les tokens JWT expirent après 30 minutes
* Les refresh tokens sont valides 7 jours
"""

tags_metadata = [
    {
        "name": "auth",
        "description": """
        Gestion de l'authentification et des autorisations.
        
        Opérations :
        * Login avec username/password
        * Refresh de token
        * Déconnexion
        * Inscription de nouveaux utilisateurs
        """
    },
    {
        "name": "posts",
        "description": """
        Gestion des posts et des tags associés.
        
        Fonctionnalités :
        * Création, lecture, mise à jour et suppression de posts
        * Gestion des tags
        * Filtrage par auteur, tag, statut
        * Pagination des résultats
        """
    }
]

responses: Dict[str, Dict] = {
    "400": {
        "description": "Requête invalide",
        "content": {
            "application/json": {
                "example": {"detail": "Invalid request parameters"}
            }
        }
    },
    "401": {
        "description": "Non authentifié",
        "content": {
            "application/json": {
                "example": {"detail": "Could not validate credentials"}
            }
        }
    },
    "403": {
        "description": "Non autorisé",
        "content": {
            "application/json": {
                "example": {"detail": "Not enough permissions"}
            }
        }
    },
    "404": {
        "description": "Ressource non trouvée",
        "content": {
            "application/json": {
                "example": {"detail": "Resource not found"}
            }
        }
    },
    "422": {
        "description": "Erreur de validation",
        "content": {
            "application/json": {
                "example": {
                    "detail": [
                        {
                            "loc": ["body", "field_name"],
                            "msg": "field required",
                            "type": "value_error.missing"
                        }
                    ]
                }
            }
        }
    },
    "429": {
        "description": "Trop de requêtes",
        "content": {
            "application/json": {
                "example": {"detail": "Too many requests"}
            }
        }
    },
    "500": {
        "description": "Erreur serveur",
        "content": {
            "application/json": {
                "example": {"detail": "Internal server error"}
            }
        }
    }
}