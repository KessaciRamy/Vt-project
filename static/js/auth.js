const API_URL = "http://127.0.0.1:5000"; // Adaptez le port si nécessaire

document.addEventListener("DOMContentLoaded", () => {
    const loginForm = document.getElementById("loginForm");

    if (loginForm) {
        loginForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            const compte = document.getElementById("compte").value;
            const password = document.getElementById("password").value;
            const alertBox = document.getElementById("alertBox");

            try {
                const response = await fetch(`${API_URL}/auth/login`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ compte, password })
                });

                const data = await response.json();

                if (response.ok) {
                    // Stockage du Token et du Role
                    localStorage.setItem("token", data.access_token);
                    localStorage.setItem("user_type", data.user_type);

                    // Redirection basée sur le rôle
                    if (data.user_type === "veilleur") {
                        window.location.href = "/veilleur"; // Il faudra créer cette route Flask qui rend le template
                    } else if (data.user_type === "analyste") {
                        window.location.href = "/analyste";
                    } else if (data.user_type === "decideur") {
                        window.location.href = "/decideur";
                    } else {
                        alertBox.textContent = "Type d'utilisateur inconnu.";
                        alertBox.classList.remove("d-none");
                    }
                } else {
                    alertBox.textContent = data.error || "Erreur de connexion";
                    alertBox.classList.remove("d-none");
                }
            } catch (error) {
                console.error(error);
                alertBox.textContent = "Erreur serveur";
                alertBox.classList.remove("d-none");
            }
        });
    }
});

// Fonction utilitaire pour les appels API authentifiés (à utiliser dans les autres pages)
async function authFetch(url, options = {}) {
    const token = localStorage.getItem("token");
    if (!token) {
        window.location.href = "/"; // Retour login
        return;
    }

    const headers = options.headers || {};
    headers["Authorization"] = `Bearer ${token}`;
    options.headers = headers;

    const response = await fetch(url, options);
    if (response.status === 401) {
        alert("Session expirée");
        window.location.href = "/";
    }
    return response;
}