document.addEventListener('DOMContentLoaded', function () {
    const canvas = document.getElementById('attendanceChart');
    if (canvas && canvas.dataset.chart) {
        const chartData = JSON.parse(canvas.dataset.chart);
        new Chart(canvas.getContext('2d'), {
            type: 'bar',
            data: chartData,
            options: {
                responsive: true,
                scales: {
                    y: { beginAtZero: true }
                }
            }
        });
    }
});
