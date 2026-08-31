import os
import re

import requests


SYSTEM_PROMPT = (
    "Tu es l’assistant IA d’ESIACBOOK. "
    "Tu peux répondre à toute question de l’utilisateur, pas uniquement aux questions sur ESIACBOOK. "
    "Réponds en français sauf si l’utilisateur demande une autre langue. "
    "Sois clair, précis, pédagogique et honnête sur tes limites. "
    "Pour les questions sur ESIACBOOK, utilise uniquement les fonctionnalités réellement disponibles : profils, cours, abonnements, validation de compte, mot de passe, ressources et rôles. "
    "Ne prétends jamais avoir exécuté une action et ne demande jamais de mot de passe, clé API ou autre secret. "
    "Pour un sujet sensible ou incertain, recommande une source fiable ou un professionnel."
)


def normalize_question(question):
    if question is None:
        return ""
    return re.sub(r"\s+", " ", str(question)).strip().lower()


def fallback_answer(question):
    q = normalize_question(question)

    if not q:
        return "Pose-moi une question sur ton profil, un cours, un abonnement, la validation, ou le mot de passe."

    if any(token in q for token in ["mot de passe", "password", "changer mon mot", "mdp"]):
        return "Pour changer ton mot de passe, ouvre le menu utilisateur, puis « Changer mon mot de passe ». Tu dois renseigner ton ancien mot de passe et le nouveau mot de passe valide."

    if any(token in q for token in ["profil", "information", "modifier mes infos", "mettre à jour"]):
        return "Tu peux mettre à jour tes informations depuis le menu utilisateur, puis « Mettre à jour mes informations »."

    if any(token in q for token in ["cours", "ressource", "document", "fichier"]):
        return "Les cours et ressources sont publiés par les professeurs. En tant qu’étudiant, tu peux les consulter dans le tableau de bord et suivre les professeurs dont tu veux voir les ressources."

    if any(token in q for token in ["abonnement", "suivre", "professeur", "abonné"]):
        return "Pour suivre un professeur, va dans la liste des professeurs et clique sur « Suivre ». Tu recevras ensuite leurs nouvelles ressources dans ton dashboard."

    if any(token in q for token in ["validation", "vérification", "compte professeur", "non valid"]):
        return "Un compte professeur doit être validé par un administrateur avant d’avoir les droits complets de publication et de gestion des abonnés."

    if any(token in q for token in ["bonjour", "salut", "bonsoir", "merci"]):
        return "Bonjour ! Je peux t’aider à naviguer dans ESIACBOOK : profil, cours, abonnements, mot de passe et validation du compte."

    return (
        "Je peux répondre aux questions générales et t’aider sur ESIACBOOK. "
        "Le service IA complet n’est pas configuré pour le moment. "
        "Configure OPENAI_API_KEY côté serveur pour obtenir des réponses détaillées sur tous les sujets."
    )


def ask_ai(question, user=None, history=None):
    api_key = os.getenv("OPENAI_API_KEY", "").strip()

    if api_key:
        try:
            messages = [{"role": "system", "content": SYSTEM_PROMPT}]
            for message in (history or [])[-10:]:
                if not isinstance(message, dict):
                    continue
                if message.get("role") in ("user", "assistant") and message.get("content"):
                    messages.append({
                        "role": message["role"],
                        "content": str(message["content"])[:4000],
                    })
            messages.append({"role": "user", "content": question})
            payload = {
                "model": os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                "messages": messages,
                "temperature": 0.4,
                "max_tokens": 800,
            }
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            }
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=20,
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"].strip()
        except Exception:
            return fallback_answer(question)

    return fallback_answer(question)
