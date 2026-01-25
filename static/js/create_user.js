document.addEventListener('DOMContentLoaded', () => {
    const createForm = document.getElementById('create-form');
    if(createForm) {
        createForm.addEventListener('submit', async(e) => {
            e.preventDefault();
            const compte = document.getElementById('compte').value;
            const password = document.getElementById('password').value;
            const typeSelector = document.getElementById('typeSelector');
            const user_type = typeSelector.value;
            const alertBox = document.getElementById("alertBox");

            try {
                const response = await fetch('/users/create', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ compte, password, user_type}) 
                });
                if(response.ok) {
                    window.location.replace('/login')
                }
                else {
                    const data = await response.json();
                    alertBox.textContent = data.error || "Erreur de connexion";
                    alertBox.classList.remove("d-none");
                } 
            } catch (error) {
                console.error(error);
                alertBox.textContent = "Erreur serveur";
                alertBox.classList.remove("d-none");
            }
        })
    }
})