// --- FONCTION DE DECONNEXION GLOBALE ---
function logout() {
    localStorage.removeItem("token");
    localStorage.removeItem("user_type");
    window.location.href = "/";
}

document.addEventListener("DOMContentLoaded", () => {
    const path = window.location.pathname;

    // ============================================
    // LOGIQUE VEILLEUR
    // ============================================
    if (path.includes("veilleur")) {
        const form = document.getElementById("scrapForm");
        if (form) {
            form.addEventListener("submit", async (e) => {
                e.preventDefault();
                const btn = document.getElementById("scrapBtn");
                const spinner = document.getElementById("btnSpinner");
                const output = document.getElementById("jsonOutput");
                const resArea = document.getElementById("resultArea");

                btn.disabled = true;
                spinner.classList.remove("d-none");
                resArea.classList.add("d-none");

                const body = {
                    databases: document.getElementById("databases").value.split(',').map(s => s.trim()),
                    releases: parseInt(document.getElementById("limit_releases").value),
                    posts: parseInt(document.getElementById("limit_posts").value),
                    cves: parseInt(document.getElementById("limit_cves").value)
                };

                try {
                    const response = await authFetch("/veilleur/scrap", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify(body)
                    });
                    const data = await response.json();
                    output.textContent = JSON.stringify(data, null, 2);
                    resArea.classList.remove("d-none");
                } catch (err) {
                    alert("Erreur technique lors du scraping");
                } finally {
                    btn.disabled = false;
                    spinner.classList.add("d-none");
                }
            });
        }
    }

    // ============================================
    // LOGIQUE ANALYSTE
    // ============================================
    if (path.includes("analyste")) {
        const btn = document.getElementById("processBtn");
        if (btn) {
            btn.addEventListener("click", async () => {
                const status = document.getElementById("statusMsg");
                btn.disabled = true;
                btn.textContent = "Traitement en cours...";
                status.textContent = "Appel API Analyste...";

                try {
                    const response = await authFetch("/analyste/process", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({ input_file: "collected_data.json" })
                    });
                    const data = await response.json();

                    if (response.ok) {
                        status.className = "card-footer text-success fw-bold";
                        status.textContent = "Succès !";
                        document.getElementById("procStats").textContent = JSON.stringify(data.processing, null, 2);
                        document.getElementById("dbStats").textContent = JSON.stringify(data.insertion, null, 2);
                        document.getElementById("reportSection").classList.remove("d-none");
                    } else {
                        status.className = "card-footer text-danger";
                        status.textContent = "Erreur: " + (data.error || "Inconnue");
                    }
                } catch (e) {
                    status.textContent = "Erreur réseau";
                } finally {
                    btn.disabled = false;
                    btn.textContent = "Relancer le Traitement";
                }
            });
        }
    }

    // ============================================
    // LOGIQUE DECIDEUR (DASHBOARD + NOTIFS)
    // ============================================
    if (path.includes("decideur")) {
        let cveChartInstance = null;
        let keywordChartInstance = null;

        // Init Dashboard
        loadDatabases();
        
        // Init Notifications
        initNotifications();

        // 1. Gestion des Notifications
        function initNotifications() {
            const notifBtn = document.getElementById("notifDropdown");
            
            // Charger compteur initial
            fetchNotifications(true);

            // Charger liste au clic
            if(notifBtn) {
                notifBtn.addEventListener('show.bs.dropdown', () => {
                    fetchNotifications(false);
                });
            }
        }

        async function fetchNotifications(onlyCount = false) {
            const notifList = document.getElementById("notifList");
            const notifBadge = document.getElementById("notifBadge");

            try {
                const response = await authFetch("/notifications/notifications"); // Vérifie le slash final selon ton backend
                if(!response.ok) return; // Fail silently pour le badge

                const notifications = await response.json();

                // Update Badge
                if (notifications.length > 0) {
                    notifBadge.textContent = notifications.length;
                    notifBadge.classList.remove("d-none");
                } else {
                    notifBadge.classList.add("d-none");
                }

                if (onlyCount) return;

                // Update Liste
                notifList.innerHTML = "";
                if (notifications.length === 0) {
                    notifList.innerHTML = '<li><span class="dropdown-item-text text-muted">Aucune notification</span></li>';
                    return;
                }

                notifications.forEach(notif => {
                    const date = notif.created_at ? new Date(notif.created_at).toLocaleDateString() : "";
                    const colorClass = (notif.level === "critical") ? "text-danger" : "text-primary";
                    
                    const li = document.createElement("li");
                    li.innerHTML = `
                        <a class="dropdown-item" href="#">
                            <div class="d-flex justify-content-between w-100">
                                <strong class="${colorClass}">${notif.title || "Info"}</strong>
                                <small class="text-muted" style="font-size:0.75rem">${date}</small>
                            </div>
                            <p class="mb-0 text-wrap text-muted" style="font-size: 0.85rem;">${notif.message}</p>
                        </a>
                        <li><hr class="dropdown-divider"></li>
                    `;
                    notifList.appendChild(li);
                });

            } catch (error) {
                console.error("Erreur notif", error);
                if(!onlyCount) notifList.innerHTML = '<li><span class="dropdown-item-text text-danger">Erreur API</span></li>';
            }
        }

        // 2. Gestion des Graphiques
        async function loadDatabases() {
            try {
                const response = await authFetch("/data_api/databases");
                const dbs = await response.json();
                const select = document.getElementById("dbSelector");
                
                select.innerHTML = '<option value="" disabled selected>Choisir une technologie...</option>';
                dbs.forEach(db => {
                    const option = document.createElement("option");
                    option.value = db.id;
                    option.textContent = db.name;
                    select.appendChild(option);
                });

                select.addEventListener("change", (e) => loadDashboardData(e.target.value, e.target.options[e.target.selectedIndex].text));
            } catch (error) {
                console.error("Erreur chargement DBs", error);
            }
        }

        async function loadDashboardData(dbId, dbName) {
            document.getElementById("dbTitle").textContent = "Rapport : " + dbName;

            const [cvesRes, releasesRes, keywordsRes] = await Promise.all([
                authFetch(`/data_api/databases/${dbId}/vulnerabilities`),
                authFetch(`/data_api/databases/${dbId}/releases`),
                authFetch(`/data_api/databases/${dbId}/keywords`)
            ]);

            const cves = await cvesRes.json();
            const releases = await releasesRes.json();
            const keywords = await keywordsRes.json();

            updateKPI(cves, releases);
            updateCVEChart(cves);
            updateReleaseList(releases);
            updateKeywordChart(keywords);
        }

        function updateKPI(cves, releases) {
            const kpiContainer = document.getElementById("kpiRow");
            const criticalCount = cves.filter(c => c.is_critical || (c.cvss_score && c.cvss_score >= 9.0)).length;
            
            kpiContainer.innerHTML = `
                <div class="col-4"><div class="p-3 border bg-light rounded"><h3>${releases.length}</h3><small>Versions</small></div></div>
                <div class="col-4"><div class="p-3 border bg-light rounded"><h3>${cves.length}</h3><small>Vulnérabilités</small></div></div>
                <div class="col-4"><div class="p-3 border ${criticalCount > 0 ? 'bg-danger text-white' : 'bg-success text-white'} rounded"><h3>${criticalCount}</h3><small>Critiques</small></div></div>
            `;
        }

        function updateReleaseList(releases) {
            const list = document.getElementById("releaseList");
            list.innerHTML = "";
            releases.slice(0, 10).forEach(rel => {
                const li = document.createElement("li");
                li.className = "list-group-item d-flex justify-content-between align-items-center";
                li.innerHTML = `<div><strong>${rel.title || rel.version}</strong><br><small class="text-muted">${rel.release_date || ''}</small></div>
                                ${rel.has_breaking_changes ? '<span class="badge bg-warning text-dark">Breaking</span>' : ''}`;
                list.appendChild(li);
            });
        }

        function updateCVEChart(cves) {
            let low=0, medium=0, high=0, critical=0;
            cves.forEach(c => {
                const s = c.cvss_score || 0;
                if(s >= 9.0) critical++; else if(s >= 7.0) high++; else if(s >= 4.0) medium++; else low++;
            });

            const ctx = document.getElementById('cveChart').getContext('2d');
            if(cveChartInstance) cveChartInstance.destroy();
            cveChartInstance = new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: ['Critique', 'Elevée', 'Moyenne', 'Faible'],
                    datasets: [{ data: [critical, high, medium, low], backgroundColor: ['#dc3545', '#fd7e14', '#ffc107', '#28a745'] }]
                }
            });
        }

        function updateKeywordChart(keywords) {
            const topKw = keywords.slice(0, 5);
            const ctx = document.getElementById('keywordChart').getContext('2d');
            if(keywordChartInstance) keywordChartInstance.destroy();
            keywordChartInstance = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: topKw.map(k => k.keyword),
                    datasets: [{ label: 'Occurrences', data: topKw.map(k => k.occurrences), backgroundColor: '#0d6efd' }]
                },
                options: { scales: { y: { beginAtZero: true } } }
            });
        }
    }
});