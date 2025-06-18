// Mobile menu toggle
        const mobileMenuToggle = document.getElementById('mobile-menu-toggle');
        const mobileNav = document.getElementById('mobile-nav');
    
        if (mobileMenuToggle && mobileNav) {
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
        }
    
        document.addEventListener('DOMContentLoaded', function() {
            // Price button functionality
            document.querySelectorAll('.toggle-price-btn').forEach(btn => {
                btn.addEventListener('click', function(e) {
                    e.preventDefault();
                    const displayDiv = this.closest('.dashboard-card').querySelector('.price-display');
                    const commodity = this.dataset.commodity;
                    
                    if (displayDiv.style.display === 'none' || displayDiv.style.display === '') {
                        displayDiv.textContent = 'Loading price...';
                        displayDiv.style.display = 'block';
                        this.innerHTML = '<i class="fas fa-times mr-2"></i> Hide Price';
                        
                        fetch(`/manufacturer/commodity-price/?commodity=${encodeURIComponent(commodity)}`)
                            .then(response => response.json())
                            .then(data => {
                                if (data.price) {
                                    displayDiv.textContent = `Current Price: ${data.price}`;
                                    displayDiv.classList.remove('hidden');
                                } else if (data.error) {
                                    displayDiv.textContent = `Error: ${data.error}`;
                                    displayDiv.classList.remove('hidden');
                                } else {
                                    displayDiv.textContent = 'Price not available';
                                    displayDiv.classList.remove('hidden');
                                }
                            })
                            .catch(() => {
                                displayDiv.textContent = 'Failed to fetch price';
                                displayDiv.classList.remove('hidden');
                            });
                    } else {
                        displayDiv.style.display = 'none';
                        this.innerHTML = '<i class="fas fa-chart-line mr-2"></i> Show Live Price';
                    }
                });
            });
    
            // Analytics button functionality - SIMPLIFIED VERSION
            document.querySelectorAll('.toggle-analytics-btn').forEach(btn => {
                btn.addEventListener('click', function(e) {
                    e.preventDefault();
                    const analyticsDiv = this.closest('.dashboard-card').querySelector('.analytics-display');
                    const loadingElement = analyticsDiv.querySelector('.analytics-loading');
                    const dataContentElement = analyticsDiv.querySelector('.analytics-data-content');
                    const commodity = this.dataset.commodity;
                    const category = this.dataset.category;
                    
                    if (analyticsDiv.style.display === 'none' || analyticsDiv.style.display === '') {
                        analyticsDiv.style.display = 'block';
                        loadingElement.style.display = 'block';
                        dataContentElement.style.display = 'none';
                        this.innerHTML = '<i class="fas fa-times mr-2"></i> Hide Analytics';
                        
                        fetch(`/manufacturer/commodity-analytics/?commodity=${encodeURIComponent(commodity)}&category=${encodeURIComponent(category)}`)
                            .then(response => response.json())
                            .then(data => {
                                loadingElement.style.display = 'none';
                                dataContentElement.style.display = 'block';
                                
                                if (data.analytics) {
                                    // Display the raw analytics data exactly as it comes from the API
                                    dataContentElement.innerHTML = `
                                        <div class="p-4 whitespace-pre-wrap bg-gray-50 rounded">
                                            ${data.analytics}
                                        </div>
                                    `;
                                } else if (data.error) {
                                    dataContentElement.innerHTML = `
                                        <div class="p-4 text-red-600">
                                            <i class="fas fa-exclamation-circle mr-2"></i> Error: ${data.error}
                                        </div>
                                    `;
                                } else {
                                    dataContentElement.innerHTML = `
                                        <div class="p-4 text-gray-600">
                                            <i class="fas fa-info-circle mr-2"></i> Analytics not available for this commodity.
                                        </div>
                                    `;
                                }
                            })
                            .catch(() => {
                                loadingElement.style.display = 'none';
                                dataContentElement.style.display = 'block';
                                dataContentElement.innerHTML = `
                                    <div class="p-4 text-red-600">
                                        <i class="fas fa-exclamation-circle mr-2"></i> Failed to fetch analytics data. Please try again later.
                                    </div>
                                `;
                            });
                    } else {
                        analyticsDiv.style.display = 'none';
                        this.innerHTML = '<i class="fas fa-chart-bar mr-2"></i> Get Analytics';
                    }
                });
            });
        });