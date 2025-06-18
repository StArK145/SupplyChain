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

// AI Suggestions Modal
const aiSuggestionsBtn = document.getElementById('ai-suggestions-btn');
const aiModal = document.getElementById('ai-suggestions-modal');
const closeAiModal = document.getElementById('close-ai-modal');
const aiContent = document.getElementById('ai-suggestions-content');

if (aiSuggestionsBtn && aiModal && closeAiModal && aiContent) {
    // Open modal and fetch AI suggestions
    aiSuggestionsBtn.addEventListener('click', async (e) => {
        e.preventDefault();
        e.stopPropagation();
        
        // Show modal and loading state
        aiModal.classList.remove('hidden');
        aiContent.innerHTML = `
            <div class="text-center py-4">
                <i class="fas fa-spinner fa-spin text-teal-500 text-2xl"></i>
                <p class="mt-2">Analyzing market trends...</p>
            </div>
        `;

        try {
            const response = await fetch('/supplier/ai-suggestions/', {
                headers: {
                    'Accept': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });
            
            const data = await response.json();
            
            if (!response.ok || data.status === 'error') {
                throw new Error(data.error || data.message || 'Failed to get suggestions');
            }
            
            // Build suggestions HTML
            let html = `
                <div class="w-full max-w-4xl bg-teal-50 border border-teal-200 rounded-lg p-4">
                    <h3 class="font-bold text-lg mb-3 text-primary">Market Analysis Results</h3>
                    <p class="text-teal-800 mb-4">${data.message}</p>
            `;
            
            if (data.top_categories && data.top_categories.length > 0) {
                html += `<h4 class="font-bold text-lg mb-3 text-primary">Top High-Demand Product Categories:</h4>`;
                
                data.top_categories.forEach((category, index) => {
                    html += `
                        <div class="mb-4">
                            <p class="font-semibold">${index + 1}. ${category.name}</p>
                            <p class="text-sm text-gray-600 mb-2">Requested ${category.request_count} times recently</p>
                            <p class="text-sm font-medium mb-1">Top Products:</p>
                            <ul class="list-disc list-inside ml-4">
                                ${category.top_products.map(p => `<li>${p}</li>`).join('')}
                            </ul>
                        </div>
                    `;
                });
            } else {
                html += `<p class="text-gray-600">No category data available</p>`;
            }
            
            html += `</div>`;
            aiContent.innerHTML = html;
            
        } catch (error) {
            console.error('Error:', error);
            aiContent.innerHTML = `
                <div class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
                    <strong>Error:</strong> ${error.message}
                    <p class="mt-2">Please try again later or contact support.</p>
                </div>
            `;
        }
    });

    // Close modal handlers
    closeAiModal.addEventListener('click', () => {
        aiModal.classList.add('hidden');
    });

    aiModal.addEventListener('click', (e) => {
        if (e.target === aiModal) {
            aiModal.classList.add('hidden');
        }
    });

    // Prevent closing when clicking inside modal content
    document.querySelector('#ai-suggestions-modal > div').addEventListener('click', (e) => {
        e.stopPropagation();
    });
}