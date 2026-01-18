/**
 * Canvas Presets Module
 * Provides comprehensive canvas size presets for all social media platforms
 * and design use cases with a visual selector UI.
 */
const DesignPresets = {
    currentCategory: 'popular',
    selectedPreset: null,
    
    // Preset categories with icons
    categories: [
        { id: 'popular', name: 'Popular', icon: 'star' },
        { id: 'instagram', name: 'Instagram', icon: 'photo_camera' },
        { id: 'facebook', name: 'Facebook', icon: 'thumb_up' },
        { id: 'twitter', name: 'Twitter/X', icon: 'tag' },
        { id: 'youtube', name: 'YouTube', icon: 'play_circle' },
        { id: 'linkedin', name: 'LinkedIn', icon: 'business_center' },
        { id: 'tiktok', name: 'TikTok', icon: 'music_note' },
        { id: 'pinterest', name: 'Pinterest', icon: 'push_pin' },
        { id: 'whatsapp', name: 'WhatsApp', icon: 'chat' },
        { id: 'business', name: 'Business', icon: 'badge' },
        { id: 'presentation', name: 'Slides', icon: 'slideshow' },
        { id: 'print', name: 'Print', icon: 'print' },
        { id: 'nepal', name: 'Nepal Festivals', icon: 'celebration' },
        { id: 'custom', name: 'Custom', icon: 'crop_free' }
    ],
    
    // Comprehensive presets database
    presets: {
        popular: [
            { id: 'instagram_post_square', name: 'Instagram Post', width: 1080, height: 1080, icon: 'photo_camera' },
            { id: 'instagram_story', name: 'Instagram Story', width: 1080, height: 1920, icon: 'phone_iphone' },
            { id: 'facebook_post', name: 'Facebook Post', width: 1200, height: 630, icon: 'thumb_up' },
            { id: 'youtube_thumbnail', name: 'YouTube Thumbnail', width: 1280, height: 720, icon: 'play_circle' },
            { id: 'twitter_post', name: 'Twitter/X Post', width: 1200, height: 675, icon: 'tag' },
            { id: 'presentation_16_9', name: 'Presentation 16:9', width: 1920, height: 1080, icon: 'slideshow' },
            { id: 'nepali_festival_square', name: 'Festival Greeting', width: 1080, height: 1080, icon: 'celebration' },
            { id: 'whatsapp_status', name: 'WhatsApp Status', width: 1080, height: 1920, icon: 'chat' }
        ],
        instagram: [
            { id: 'instagram_post_square', name: 'Post (Square)', width: 1080, height: 1080, desc: 'Standard feed post' },
            { id: 'instagram_post_portrait', name: 'Post (Portrait)', width: 1080, height: 1350, desc: '4:5 takes more space' },
            { id: 'instagram_post_landscape', name: 'Post (Landscape)', width: 1080, height: 566, desc: '1.91:1 horizontal' },
            { id: 'instagram_story', name: 'Story / Reel', width: 1080, height: 1920, desc: '9:16 full screen' },
            { id: 'instagram_reel_cover', name: 'Reel Cover', width: 1080, height: 1920, desc: 'Video thumbnail' },
            { id: 'instagram_carousel', name: 'Carousel Slide', width: 1080, height: 1080, desc: 'Multi-image post' },
            { id: 'instagram_profile', name: 'Profile Photo', width: 320, height: 320, desc: 'Profile picture' },
            { id: 'instagram_ad_square', name: 'Ad (Square)', width: 1080, height: 1080, desc: 'Sponsored content' }
        ],
        facebook: [
            { id: 'facebook_post', name: 'Post', width: 1200, height: 630, desc: 'Standard post' },
            { id: 'facebook_post_square', name: 'Post (Square)', width: 1080, height: 1080, desc: 'Mobile optimized' },
            { id: 'facebook_cover', name: 'Cover Photo', width: 820, height: 312, desc: 'Profile banner' },
            { id: 'facebook_cover_mobile', name: 'Cover (Mobile-Safe)', width: 851, height: 315, desc: 'Works on all devices' },
            { id: 'facebook_event_cover', name: 'Event Cover', width: 1920, height: 1005, desc: 'Event banner' },
            { id: 'facebook_group_cover', name: 'Group Cover', width: 1640, height: 856, desc: 'Group banner' },
            { id: 'facebook_ad', name: 'Ad', width: 1200, height: 628, desc: 'Sponsored content' },
            { id: 'facebook_story', name: 'Story', width: 1080, height: 1920, desc: 'Full screen story' },
            { id: 'facebook_profile', name: 'Profile Photo', width: 320, height: 320, desc: 'Profile picture' }
        ],
        twitter: [
            { id: 'twitter_post', name: 'Post (16:9)', width: 1200, height: 675, desc: 'Standard tweet image' },
            { id: 'twitter_post_square', name: 'Post (Square)', width: 1080, height: 1080, desc: 'Square format' },
            { id: 'twitter_header', name: 'Header Banner', width: 1500, height: 500, desc: 'Profile header' },
            { id: 'twitter_card', name: 'Card Image', width: 1200, height: 628, desc: 'Link preview' },
            { id: 'twitter_profile', name: 'Profile Photo', width: 400, height: 400, desc: 'Profile picture' }
        ],
        youtube: [
            { id: 'youtube_thumbnail', name: 'Thumbnail', width: 1280, height: 720, desc: 'Video thumbnail' },
            { id: 'youtube_channel_art', name: 'Channel Banner', width: 2560, height: 1440, desc: 'Channel header' },
            { id: 'youtube_channel_icon', name: 'Channel Icon', width: 800, height: 800, desc: 'Channel profile' },
            { id: 'youtube_end_screen', name: 'End Screen', width: 1920, height: 1080, desc: 'Outro template' }
        ],
        linkedin: [
            { id: 'linkedin_post', name: 'Post', width: 1200, height: 628, desc: 'Feed post' },
            { id: 'linkedin_post_square', name: 'Post (Square)', width: 1080, height: 1080, desc: 'Square format' },
            { id: 'linkedin_banner', name: 'Profile Banner', width: 1584, height: 396, desc: 'Personal background' },
            { id: 'linkedin_company_cover', name: 'Company Cover', width: 1128, height: 191, desc: 'Company page' },
            { id: 'linkedin_article_cover', name: 'Article Cover', width: 1280, height: 720, desc: 'Blog header' },
            { id: 'linkedin_profile', name: 'Profile Photo', width: 400, height: 400, desc: 'Professional headshot' }
        ],
        tiktok: [
            { id: 'tiktok_video', name: 'Video', width: 1080, height: 1920, desc: 'Full screen 9:16' },
            { id: 'tiktok_profile', name: 'Profile Photo', width: 200, height: 200, desc: 'Profile picture' }
        ],
        pinterest: [
            { id: 'pinterest_pin', name: 'Pin (2:3)', width: 1000, height: 1500, desc: 'Standard pin' },
            { id: 'pinterest_pin_long', name: 'Pin (Long)', width: 1000, height: 2100, desc: 'Infographic' },
            { id: 'pinterest_square', name: 'Pin (Square)', width: 1000, height: 1000, desc: 'Square format' },
            { id: 'pinterest_board_cover', name: 'Board Cover', width: 600, height: 600, desc: 'Board thumbnail' },
            { id: 'pinterest_profile', name: 'Profile Photo', width: 330, height: 330, desc: 'Profile picture' }
        ],
        whatsapp: [
            { id: 'whatsapp_status', name: 'Status', width: 1080, height: 1920, desc: 'Full screen story' },
            { id: 'whatsapp_profile', name: 'Profile Photo', width: 500, height: 500, desc: 'Profile picture' }
        ],
        business: [
            { id: 'business_card_standard', name: 'Business Card', width: 1050, height: 600, desc: '3.5 x 2 inches' },
            { id: 'business_card_square', name: 'Business Card (Square)', width: 600, height: 600, desc: 'Modern square' },
            { id: 'letterhead_a4', name: 'Letterhead (A4)', width: 2480, height: 3508, desc: 'A4 document' },
            { id: 'letterhead_letter', name: 'Letterhead (Letter)', width: 2550, height: 3300, desc: 'US Letter' },
            { id: 'invoice_a4', name: 'Invoice (A4)', width: 2480, height: 3508, desc: 'Invoice template' }
        ],
        presentation: [
            { id: 'presentation_16_9', name: 'Widescreen (16:9)', width: 1920, height: 1080, desc: 'Modern standard' },
            { id: 'presentation_4_3', name: 'Standard (4:3)', width: 1600, height: 1200, desc: 'Classic format' },
            { id: 'presentation_a4', name: 'A4 Landscape', width: 1587, height: 1123, desc: 'Document-style' }
        ],
        print: [
            { id: 'poster_a3_portrait', name: 'Poster A3', width: 3508, height: 4961, desc: '297×420mm' },
            { id: 'poster_a3_landscape', name: 'Poster A3 (Landscape)', width: 4961, height: 3508, desc: 'Horizontal' },
            { id: 'flyer_a5', name: 'Flyer A5', width: 1748, height: 2480, desc: '148×210mm' },
            { id: 'flyer_a6', name: 'Flyer A6', width: 1240, height: 1748, desc: 'Small handout' },
            { id: 'brochure_trifold', name: 'Trifold Brochure', width: 3300, height: 2550, desc: 'US Letter' }
        ],
        nepal: [
            { id: 'nepali_festival_square', name: 'Festival Greeting', width: 1080, height: 1080, desc: 'Dashain, Tihar, etc.' },
            { id: 'nepali_festival_story', name: 'Festival Story', width: 1080, height: 1920, desc: 'Vertical greeting' },
            { id: 'nepali_business_post', name: 'Business Promo', width: 1080, height: 1080, desc: 'Local shops' }
        ],
        custom: []
    },
    
    init() {
        this.createPresetModal();
        this.bindEvents();
        this.loadTemplateList();
    },
    
    createPresetModal() {
        // Check if modal already exists
        if (document.getElementById('modal-presets')) return;
        
        const modal = document.createElement('div');
        modal.id = 'modal-presets';
        modal.className = 'modal hidden';
        modal.innerHTML = `
            <div class="modal-content modal-lg">
                <div class="modal-header">
                    <h2>Choose Canvas Size</h2>
                    <button class="btn-close-modal" id="btn-close-presets">
                        <span class="material-symbols-outlined">close</span>
                    </button>
                </div>
                <div class="modal-body preset-modal-body">
                    <div class="preset-sidebar">
                        <div class="preset-categories" id="preset-categories">
                            ${this.categories.map(cat => `
                                <button class="preset-category-btn ${cat.id === 'popular' ? 'active' : ''}" data-category="${cat.id}">
                                    <span class="material-symbols-outlined">${cat.icon}</span>
                                    <span class="category-name">${cat.name}</span>
                                </button>
                            `).join('')}
                        </div>
                    </div>
                    <div class="preset-main">
                        <div class="preset-search">
                            <span class="material-symbols-outlined">search</span>
                            <input type="text" id="preset-search-input" placeholder="Search presets...">
                        </div>
                        <div class="preset-grid" id="preset-grid">
                            <!-- Presets loaded dynamically -->
                        </div>
                        <div class="preset-custom" id="preset-custom-section">
                            <div class="custom-size-form">
                                <h3>Custom Size</h3>
                                <div class="custom-size-inputs">
                                    <div class="input-group">
                                        <label>Width</label>
                                        <input type="number" id="custom-width" value="1080" min="100" max="10000">
                                        <span class="unit">px</span>
                                    </div>
                                    <span class="size-separator">×</span>
                                    <div class="input-group">
                                        <label>Height</label>
                                        <input type="number" id="custom-height" value="1080" min="100" max="10000">
                                        <span class="unit">px</span>
                                    </div>
                                </div>
                                <div class="aspect-ratio-presets">
                                    <button class="aspect-btn" data-ratio="1:1">1:1</button>
                                    <button class="aspect-btn" data-ratio="4:5">4:5</button>
                                    <button class="aspect-btn" data-ratio="9:16">9:16</button>
                                    <button class="aspect-btn" data-ratio="16:9">16:9</button>
                                    <button class="aspect-btn" data-ratio="3:1">3:1</button>
                                </div>
                                <button class="btn-primary" id="btn-apply-custom">
                                    <span class="material-symbols-outlined">check</span>
                                    Apply Custom Size
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
    },
    
    bindEvents() {
        // Open preset modal from canvas properties
        const canvasWidthInput = document.getElementById('canvas-width');
        const canvasHeightInput = document.getElementById('canvas-height');
        
        // Add preset button to canvas properties
        const canvasProps = document.getElementById('canvas-properties');
        if (canvasProps) {
            const presetButton = document.createElement('button');
            presetButton.id = 'btn-open-presets';
            presetButton.className = 'btn-secondary-full';
            presetButton.innerHTML = `
                <span class="material-symbols-outlined">aspect_ratio</span>
                Choose Size Preset
            `;
            
            const firstGroup = canvasProps.querySelector('.property-group');
            if (firstGroup) {
                firstGroup.appendChild(presetButton);
            }
            
            presetButton.addEventListener('click', () => this.openModal());
        }
        
        // Close modal
        document.getElementById('btn-close-presets')?.addEventListener('click', () => this.closeModal());
        
        // Click outside to close
        document.getElementById('modal-presets')?.addEventListener('click', (e) => {
            if (e.target.id === 'modal-presets') this.closeModal();
        });
        
        // Category selection
        document.getElementById('preset-categories')?.addEventListener('click', (e) => {
            const btn = e.target.closest('.preset-category-btn');
            if (btn) {
                this.selectCategory(btn.dataset.category);
            }
        });
        
        // Preset selection
        document.getElementById('preset-grid')?.addEventListener('click', (e) => {
            const card = e.target.closest('.preset-card');
            if (card) {
                this.selectPreset(card.dataset.presetId);
            }
        });
        
        // Search
        document.getElementById('preset-search-input')?.addEventListener('input', (e) => {
            this.searchPresets(e.target.value);
        });
        
        // Custom size inputs
        document.getElementById('btn-apply-custom')?.addEventListener('click', () => {
            this.applyCustomSize();
        });
        
        // Aspect ratio buttons
        document.querySelectorAll('.aspect-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                this.setAspectRatio(btn.dataset.ratio);
            });
        });
        
        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.closeModal();
            }
        });
    },
    
    openModal() {
        const modal = document.getElementById('modal-presets');
        if (modal) {
            modal.classList.remove('hidden');
            this.renderPresets('popular');
        }
    },
    
    closeModal() {
        const modal = document.getElementById('modal-presets');
        if (modal) {
            modal.classList.add('hidden');
        }
    },
    
    selectCategory(categoryId) {
        this.currentCategory = categoryId;
        
        // Update active state
        document.querySelectorAll('.preset-category-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.category === categoryId);
        });
        
        // Show/hide custom section
        const customSection = document.getElementById('preset-custom-section');
        const presetGrid = document.getElementById('preset-grid');
        
        if (categoryId === 'custom') {
            customSection?.classList.add('visible');
            presetGrid?.classList.add('hidden');
        } else {
            customSection?.classList.remove('visible');
            presetGrid?.classList.remove('hidden');
            this.renderPresets(categoryId);
        }
    },
    
    renderPresets(categoryId) {
        const grid = document.getElementById('preset-grid');
        if (!grid) return;
        
        const presets = this.presets[categoryId] || [];
        
        if (presets.length === 0) {
            grid.innerHTML = `
                <div class="no-presets">
                    <span class="material-symbols-outlined">image_not_supported</span>
                    <p>No presets in this category</p>
                </div>
            `;
            return;
        }
        
        grid.innerHTML = presets.map(preset => `
            <div class="preset-card" data-preset-id="${preset.id}" data-width="${preset.width}" data-height="${preset.height}">
                <div class="preset-preview" style="aspect-ratio: ${preset.width}/${preset.height}">
                    <div class="preset-dimensions">${preset.width}×${preset.height}</div>
                </div>
                <div class="preset-info">
                    <div class="preset-name">${preset.name}</div>
                    ${preset.desc ? `<div class="preset-desc">${preset.desc}</div>` : ''}
                </div>
            </div>
        `).join('');
    },
    
    selectPreset(presetId) {
        // Find preset
        let preset = null;
        for (const category of Object.values(this.presets)) {
            preset = category.find(p => p.id === presetId);
            if (preset) break;
        }
        
        if (!preset) return;
        
        // Apply to canvas
        this.applyPreset(preset.width, preset.height, preset.name);
        this.closeModal();
    },
    
    applyPreset(width, height, name = 'Custom') {
        if (typeof DesignCanvas !== 'undefined') {
            DesignCanvas.setCanvasSize(width, height);
        }
        
        // Update input fields
        const widthInput = document.getElementById('canvas-width');
        const heightInput = document.getElementById('canvas-height');
        if (widthInput) widthInput.value = width;
        if (heightInput) heightInput.value = height;
        
        // Show notification
        this.showNotification(`Canvas set to ${name} (${width}×${height})`);
    },
    
    applyCustomSize() {
        const width = parseInt(document.getElementById('custom-width')?.value || 1080);
        const height = parseInt(document.getElementById('custom-height')?.value || 1080);
        
        if (width < 100 || width > 10000 || height < 100 || height > 10000) {
            this.showNotification('Size must be between 100 and 10000 pixels', 'error');
            return;
        }
        
        this.applyPreset(width, height, 'Custom');
        this.closeModal();
    },
    
    setAspectRatio(ratio) {
        const [w, h] = ratio.split(':').map(Number);
        const baseWidth = parseInt(document.getElementById('custom-width')?.value || 1080);
        const newHeight = Math.round(baseWidth * h / w);
        
        const heightInput = document.getElementById('custom-height');
        if (heightInput) heightInput.value = newHeight;
        
        // Highlight active ratio button
        document.querySelectorAll('.aspect-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.ratio === ratio);
        });
    },
    
    searchPresets(query) {
        query = query.toLowerCase().trim();
        
        if (!query) {
            this.renderPresets(this.currentCategory);
            return;
        }
        
        // Search across all categories
        const results = [];
        for (const [category, presets] of Object.entries(this.presets)) {
            for (const preset of presets) {
                if (preset.name.toLowerCase().includes(query) ||
                    preset.desc?.toLowerCase().includes(query) ||
                    preset.id.toLowerCase().includes(query)) {
                    results.push(preset);
                }
            }
        }
        
        // Remove duplicates
        const uniqueResults = [...new Map(results.map(p => [p.id, p])).values()];
        
        const grid = document.getElementById('preset-grid');
        if (!grid) return;
        
        if (uniqueResults.length === 0) {
            grid.innerHTML = `
                <div class="no-presets">
                    <span class="material-symbols-outlined">search_off</span>
                    <p>No presets matching "${query}"</p>
                </div>
            `;
            return;
        }
        
        grid.innerHTML = uniqueResults.map(preset => `
            <div class="preset-card" data-preset-id="${preset.id}" data-width="${preset.width}" data-height="${preset.height}">
                <div class="preset-preview" style="aspect-ratio: ${preset.width}/${preset.height}">
                    <div class="preset-dimensions">${preset.width}×${preset.height}</div>
                </div>
                <div class="preset-info">
                    <div class="preset-name">${preset.name}</div>
                    ${preset.desc ? `<div class="preset-desc">${preset.desc}</div>` : ''}
                </div>
            </div>
        `).join('');
    },
    
    loadTemplateList() {
        // Load templates into the sidebar template list
        const templateList = document.getElementById('template-list');
        if (!templateList) return;
        
        const festivalTemplates = [
            { id: 'saraswoti_puja', name: 'Saraswoti Puja', color: '#FFD700' },
            { id: 'dashain', name: 'Dashain', color: '#DC143C' },
            { id: 'tihar', name: 'Tihar/Deepawali', color: '#FF6B00' },
            { id: 'holi', name: 'Holi', color: '#FF1493' },
            { id: 'nepali_new_year', name: 'Nepali New Year', color: '#1E3A8A' },
            { id: 'teej', name: 'Teej', color: '#DC143C' }
        ];
        
        const businessTemplates = [
            { id: 'dairy_business', name: 'Dairy Shop', color: '#2E8B57' },
            { id: 'sweets_shop', name: 'Sweets Shop', color: '#FF6B35' }
        ];
        
        templateList.innerHTML = `
            <div class="template-section">
                <div class="template-section-title">Festival Greetings</div>
                ${festivalTemplates.map(t => `
                    <button class="template-item" data-template="${t.id}">
                        <span class="template-color" style="background: ${t.color}"></span>
                        <span class="template-name">${t.name}</span>
                    </button>
                `).join('')}
            </div>
            <div class="template-section">
                <div class="template-section-title">Business Promo</div>
                ${businessTemplates.map(t => `
                    <button class="template-item" data-template="${t.id}">
                        <span class="template-color" style="background: ${t.color}"></span>
                        <span class="template-name">${t.name}</span>
                    </button>
                `).join('')}
            </div>
        `;
        
        // Add template click handlers
        templateList.addEventListener('click', (e) => {
            const btn = e.target.closest('.template-item');
            if (btn) {
                this.applyTemplate(btn.dataset.template);
            }
        });
    },
    
    async applyTemplate(templateId) {
        // Send to AI chat to generate the design
        if (typeof DesignChat !== 'undefined') {
            const prompts = {
                'saraswoti_puja': 'Create a beautiful Saraswoti Puja greeting design with yellow and white colors. Include the greeting "सरस्वती पूजाको शुभकामना" and space for a brand logo.',
                'dashain': 'Create a Dashain festival greeting with tika (red) and jamara (green) colors. Include "विजया दशमीको शुभकामना" and space for brand logo.',
                'tihar': 'Create a Tihar/Deepawali greeting with diyo lights theme on dark background. Include "तिहारको शुभकामना" with gold and orange colors.',
                'holi': 'Create a colorful Holi greeting with splash effects. Include "फागु पूर्णिमाको शुभकामना" with pink, blue, and yellow colors.',
                'nepali_new_year': 'Create a Nepali New Year 2082 greeting with traditional red and blue colors. Include "नयाँ वर्षको शुभकामना".',
                'teej': 'Create a Teej festival greeting for women with red and green colors. Include "तीजको शुभकामना" with bangles motif.',
                'dairy_business': 'Create a dairy shop promotion design with fresh green colors. Include space for product prices, contact number, and brand logo.',
                'sweets_shop': 'Create a sweets shop promotion with warm orange colors. Include space for menu items, prices, contact info, and "Festival Special" banner.'
            };
            
            const prompt = prompts[templateId];
            if (prompt) {
                // Set canvas to square for festivals
                this.applyPreset(1080, 1080, 'Festival Greeting');
                
                // Send to chat
                const inputField = document.getElementById('design-input');
                if (inputField) {
                    inputField.value = prompt;
                    // Trigger send
                    document.getElementById('btn-send-design')?.click();
                }
            }
        }
    },
    
    showNotification(message, type = 'success') {
        // Simple notification
        const notification = document.createElement('div');
        notification.className = `preset-notification ${type}`;
        notification.innerHTML = `
            <span class="material-symbols-outlined">${type === 'success' ? 'check_circle' : 'error'}</span>
            <span>${message}</span>
        `;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.classList.add('fade-out');
            setTimeout(() => notification.remove(), 300);
        }, 2500);
    },
    
    // Get preset by ID
    getPreset(presetId) {
        for (const category of Object.values(this.presets)) {
            const preset = category.find(p => p.id === presetId);
            if (preset) return preset;
        }
        return null;
    },
    
    // Get all popular presets
    getPopularPresets() {
        return this.presets.popular;
    },
    
    // Get presets by category
    getPresetsByCategory(category) {
        return this.presets[category] || [];
    }
};

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    DesignPresets.init();
});
