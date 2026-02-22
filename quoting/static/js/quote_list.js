function quotePipeline() {
    return {
        stats: { drafts: 0, revenue: 0 },
        loading: false,
        
        init() {
            window.addEventListener('update-stats', (e) => {
                this.stats = e.detail;
            });
        },

        async createNewQuote() {
            this.loading = true;
            try {
                const response = await fetch("/quoting/api/quotes/", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                        "X-CSRFToken": window.CSRF_TOKEN
                    },
                    body: JSON.stringify({
                        customer_display_name: "New Draft Quote",
                        status: "draft"
                    })
                });

                if (!response.ok) throw new Error("Failed to create quote");
                
                const data = await response.json();
                // Redirect to the workspace for the new quote
                window.location.href = `/quotes/${data.id}/`;
                
            } catch (err) {
                alert(err.message);
                this.loading = false;
            }
        },

        getCookie(name) {
            let cookieValue = null;
            if (document.cookie && document.cookie !== '') {
                const cookies = document.cookie.split(';');
                for (let i = 0; i < cookies.length; i++) {
                    const cookie = cookies[i].trim();
                    if (cookie.substring(0, name.length + 1) === (name + '=')) {
                        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                        break;
                    }
                }
            }
            return cookieValue;
        }
    }
}