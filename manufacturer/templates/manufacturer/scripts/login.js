
// Mobile menu toggle
        const mobileMenuToggle = document.getElementById('mobile-menu-toggle');
        const mobileNav = document.getElementById('mobile-nav');

        mobileMenuToggle.addEventListener('click', () => {
            mobileNav.classList.toggle('active');
        });

        // Close mobile menu when clicking outside
        document.addEventListener('click', (event) => {
            const isClickInsideMenu = mobileNav.contains(event.target);
            const isClickOnToggle = mobileMenuToggle.contains(event.target);
            
            if (!isClickInsideMenu && !isClickOnToggle && mobileNav.classList.contains('active')) {
                mobileNav.classList.remove('active');
            }
        });

        // Form input styling
        document.addEventListener('DOMContentLoaded', function() {
            const formInputs = document.querySelectorAll('input, textarea, select');
            formInputs.forEach(input => {
                if (input.type !== 'checkbox') {
                    input.classList.add('w-full', 'px-4', 'py-3', 'border', 'border-gray-300', 'rounded-lg', 'focus:ring-blue-500', 'focus:border-blue-500', 'form-input');
                }
            });
            
            // Style form paragraphs for better appearance
            const formParagraphs = document.querySelectorAll('form p');
            formParagraphs.forEach(p => {
                p.classList.add('mb-4');
                const label = p.querySelector('label');
                if (label) {
                    label.classList.add('block', 'text-sm', 'font-medium', 'text-gray-700', 'mb-2');
                }
            });
        });

        // Smooth scrolling for anchor links
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {
            anchor.addEventListener('click', function (e) {
                e.preventDefault();
                
                const href = this.getAttribute('href');
                if (href !== '#') {
                    const target = document.querySelector(href);
                    if (target) {
                        target.scrollIntoView({
                            behavior: 'smooth'
                        });
                    }
                }
            });
        });