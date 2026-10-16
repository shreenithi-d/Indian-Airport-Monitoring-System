// Admin Dashboard & Analytics Charts using Chart.js
document.addEventListener('DOMContentLoaded', function () {
  const categoryChartCanvas = document.getElementById('airportCategoriesChart');
  const flightStatusChartCanvas = document.getElementById('flightStatusChart');
  const bookingStatusChartCanvas = document.getElementById('bookingStatusChart');
  const topRoutesChartCanvas = document.getElementById('topRoutesChart');

  if (categoryChartCanvas || flightStatusChartCanvas || bookingStatusChartCanvas || topRoutesChartCanvas) {
    fetch('/api/analytics/charts')
      .then(res => res.json())
      .then(data => {
        // 1. Airport Categories Doughnut Chart
        if (categoryChartCanvas && data.categories) {
          new Chart(categoryChartCanvas, {
            type: 'doughnut',
            data: {
              labels: data.categories.labels,
              datasets: [{
                data: data.categories.data,
                backgroundColor: ['#1769FF', '#16A673', '#F5A623', '#64748B', '#8B5CF6'],
                borderWidth: 2,
                borderColor: '#FFFFFF'
              }]
            },
            options: {
              responsive: true,
              plugins: {
                legend: { position: 'bottom' }
              }
            }
          });
        }

        // 2. Flight Status Breakdown Bar Chart
        if (flightStatusChartCanvas && data.flight_statuses) {
          new Chart(flightStatusChartCanvas, {
            type: 'bar',
            data: {
              labels: data.flight_statuses.labels,
              datasets: [{
                label: 'Flights Count',
                data: data.flight_statuses.data,
                backgroundColor: '#39A0FF',
                borderRadius: 6
              }]
            },
            options: {
              responsive: true,
              scales: {
                y: { beginAtZero: true, ticks: { precision: 0 } }
              },
              plugins: {
                legend: { display: false }
              }
            }
          });
        }

        // 3. Booking Status Chart
        if (bookingStatusChartCanvas && data.booking_statuses) {
          new Chart(bookingStatusChartCanvas, {
            type: 'pie',
            data: {
              labels: data.booking_statuses.labels,
              datasets: [{
                data: data.booking_statuses.data,
                backgroundColor: ['#16A673', '#E5484D', '#3B82F6']
              }]
            },
            options: {
              responsive: true,
              plugins: {
                legend: { position: 'bottom' }
              }
            }
          });
        }

        // 4. Top Routes Chart
        if (topRoutesChartCanvas && data.top_routes) {
          new Chart(topRoutesChartCanvas, {
            type: 'bar',
            data: {
              labels: data.top_routes.labels,
              datasets: [{
                label: 'Bookings',
                data: data.top_routes.data,
                backgroundColor: '#1769FF',
                borderRadius: 4
              }]
            },
            options: {
              indexAxis: 'y',
              responsive: true,
              plugins: {
                legend: { display: false }
              }
            }
          });
        }
      })
      .catch(err => console.error("Could not load analytics charts:", err));
  }
});
