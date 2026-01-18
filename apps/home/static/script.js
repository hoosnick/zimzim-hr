// Minimalist glassmorphism interactions for ZIM-ZIM

document.addEventListener('DOMContentLoaded', function () {
    // Smooth card entrance animations
    const cards = document.querySelectorAll('.card');
    const supportSection = document.querySelector('.support-section');

    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
            }
        });
    }, observerOptions);

    // Animate cards with stagger
    cards.forEach((card, index) => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(30px)';
        card.style.transition = `all 0.8s cubic-bezier(0.165, 0.84, 0.44, 1) ${index * 0.15}s`;
        observer.observe(card);
    });

    // Animate support section
    if (supportSection) {
        supportSection.style.opacity = '0';
        supportSection.style.transform = 'translateY(30px)';
        supportSection.style.transition = 'all 0.8s cubic-bezier(0.165, 0.84, 0.44, 1) 0.45s';
        observer.observe(supportSection);
    }

    // Card hover effect - track mouse position for gradient
    cards.forEach(card => {
        card.addEventListener('mousemove', (e) => {
            const rect = card.getBoundingClientRect();
            const x = ((e.clientX - rect.left) / rect.width) * 100;
            const y = ((e.clientY - rect.top) / rect.height) * 100;

            card.style.setProperty('--mouse-x', `${x}%`);
            card.style.setProperty('--mouse-y', `${y}%`);
        });

        card.addEventListener('mouseleave', () => {
            card.style.setProperty('--mouse-x', '50%');
            card.style.setProperty('--mouse-y', '50%');
        });
    });

    // Card click handlers
    cards.forEach(card => {
        card.addEventListener('click', function (e) {
            // Don't trigger if clicking on the link itself
            if (e.target.classList.contains('card-link') || e.target.closest('.card-link')) {
                return;
            }

            const url = this.dataset.url;
            const type = this.dataset.type;

            if (url) {
                if (type === 'download') {
                    // Trigger download for Excel manifest
                    const link = document.createElement('a');
                    link.href = url;
                    link.download = 'manifest.xml';
                    document.body.appendChild(link);
                    link.click();
                    document.body.removeChild(link);
                } else {
                    // Open in new tab for regular links
                    window.open(url, '_blank');
                }
            }
        });
    });

    // Smooth link clicks - prevent card hover during navigation
    document.querySelectorAll('.card-link').forEach(link => {
        link.addEventListener('click', function (e) {
            e.stopPropagation();

            // Add subtle click feedback
            this.style.transform = 'scale(0.98)';
            setTimeout(() => {
                this.style.transform = 'scale(1)';
            }, 150);
        });
    });

    // Support button subtle animation
    const supportBtn = document.querySelector('.support-contact');
    if (supportBtn) {
        supportBtn.addEventListener('mouseenter', function () {
            this.style.transition = 'all 0.3s cubic-bezier(0.165, 0.84, 0.44, 1)';
        });
    }

    // Minimalist console signature
    console.log(
        '%c ZIM-ZIM ',
        'background: linear-gradient(135deg, #1a1a1a 0%, #dc2626 100%); color: white; padding: 8px 16px; border-radius: 4px; font-weight: 300; font-size: 14px;'
    );
    console.log(
        '%c HR Boshqaruv Tizimi • @hoosnick ',
        'color: #718096; font-size: 11px; font-weight: 300;'
    );
});

// Parallax effect on scroll (subtle)
let ticking = false;

window.addEventListener('scroll', () => {
    if (!ticking) {
        window.requestAnimationFrame(() => {
            const scrolled = window.pageYOffset;
            const header = document.querySelector('.header');

            if (header && scrolled < 500) {
                header.style.transform = `translateY(${scrolled * 0.3}px)`;
                header.style.opacity = 1 - (scrolled / 500);
            }

            ticking = false;
        });

        ticking = true;
    }
});
