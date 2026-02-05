function confirmDelete(userId, username) {
        document.getElementById('deleteUsername').textContent = username;
        document.getElementById('confirmDeleteBtn').href = `/admin-dashboard/delete-user/${userId}/`;
        new bootstrap.Modal(document.getElementById('deleteModal')).show();
    }


const ctx = document.getElementById('progressChart').getContext('2d');
const progressChart = new Chart(ctx, {
    type: 'line',
    data: {
      labels: ['Week 1', 'Week 2', 'Week 3', 'Week 4'],
      datasets: [{
        label: 'Average Rating',
        data: [3.2, 3.8, 4.1, 4.4],
        borderColor: 'maroon',
        backgroundColor: 'rgba(128, 0, 0, 0.1)',
        fill: true,
        tension: 0.4
      }]
    },
    options: {
      animation: {
        duration: 2000,
        easing: 'easeOutQuart'
      },
      scales: {
        y: {
          beginAtZero: true,
          max: 5
        }
      },
      plugins: {
        legend: {
          display: true
        }
      }
    }
  });


const ctxBar = document.getElementById('barChart').getContext('2d');
const barChart = new Chart(ctxBar, {
    type: 'bar',
    data: {
      labels: ['Students', 'Teachers', 'Evaluations', 'Subjects'],
      datasets: [{
        label: 'Totals',
        data: [{{ total_students }}, {{ total_teachers }}, {{ total_evaluations }}, {{ total_subjects }}],
        backgroundColor: [
          'rgba(0, 123, 255, 0.7)',   // blue
          'rgba(128, 0, 0, 1)',     // maroon solid
          'rgba(255, 193, 7, 0.7)',   // yellow
          'rgba(23, 162, 184, 0.7)'   // cyan
        ],
        borderColor: [
          'rgba(0, 123, 255, 1)',
          'rgba(128, 0, 0, 1)',     // maroon solid
          'rgba(255, 193, 7, 1)',
          'rgba(23, 162, 184, 1)'
        ],
        borderWidth: 2
      }]
    },
    options: {
      animation: {
        duration: 2000,
        easing: 'easeInOutBounce'
      },
      scales: {
        y: {
          beginAtZero: true,
          max: 5
        }
      },
      plugins: {
        legend: {
          display: false
        }
      }
    }
  });
  setInterval(() => {
    barChart.data.datasets[0].data = barChart.data.datasets[0].data.map(value => {
      // Randomly add or subtract up to 1
      let change = (Math.random() > 0.5 ? 1 : -0.5) * Math.random();
      let newValue = value + change;
      // Keep values between 0 and 5
      return Math.max(0, Math.min(5, newValue));
    });
    barChart.update();
  }, 2000);

  const links = document.querySelectorAll('.sidebar-item a[data-section]');
  const sections = document.querySelectorAll('.page-section');

  links.forEach(link => {
    link.addEventListener('click', function (e) {
      e.preventDefault();

      const target = this.dataset.section;

      sections.forEach(section => {
        section.classList.remove('active-section');
      });

      document.getElementById(target).classList.add('active-section');
    });
  });
