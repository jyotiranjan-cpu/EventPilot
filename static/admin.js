// --- Navigation Logic ---
function showSection(sectionId, element) {
    // 1. Hide all sections
    const sections = document.querySelectorAll('.content-section');
    sections.forEach(sec => sec.classList.remove('active'));

    // 2. Show target section
    const target = document.getElementById('section-' + sectionId);
    if (target) {
        target.classList.add('active');
        
        // Update Title
        const title = sectionId.charAt(0).toUpperCase() + sectionId.slice(1);
        document.getElementById('page-title').innerText = title === 'Dashboard' ? 'Dashboard Overview' : 'Manage ' + title;
    }

    // 3. Update Sidebar Active State
    if (element) {
        const navItems = document.querySelectorAll('.nav-item');
        navItems.forEach(item => item.classList.remove('active'));
        element.classList.add('active');
    }
}

// --- Chart.js Initialization ---
document.addEventListener("DOMContentLoaded", function () {
    const ctx = document.getElementById('bookingChart');
    if (ctx) {
        new Chart(ctx, {
            type: 'line',
            data: {
                labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
                datasets: [{
                    label: 'Bookings',
                    data: [5, 12, 19, 10, 25, 30],
                    borderColor: '#FF6B00',
                    backgroundColor: 'rgba(255, 107, 0, 0.1)',
                    fill: true,
                    tension: 0.4
                }]
            },
            options: { responsive: true, plugins: { legend: {display: false} } }
        });
    }
});