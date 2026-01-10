console.log("Ralph CRM Loaded");

const app = {
    init: function () {
        console.log("App initializing...");
        // Navigation Logic (placeholder)
        document.querySelectorAll('.nav-item').forEach(item => {
            item.addEventListener('click', (e) => {
                e.preventDefault();
                const viewId = item.dataset.view;
                this.navigate(viewId);
            });
        });
    },

    navigate: function (viewId) {
        console.log("Navigating to", viewId);
        document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
        document.getElementById(`view-${viewId}`).classList.add('active');

        document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
        document.querySelector(`.nav-item[data-view="${viewId}"]`).classList.add('active');
    }
};

document.addEventListener('DOMContentLoaded', () => {
    app.init();
});
