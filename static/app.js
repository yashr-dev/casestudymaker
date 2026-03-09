/**
 * DigiChefs Case Study Maker - Frontend Logic
 */

document.addEventListener('DOMContentLoaded', () => {
    initFormHandlers();
    initAPIKeyToggle();
    initClarifyHandlers();
    initAutoSave();
});

function initAutoSave() {
    // Load previously saved data when page loads
    loadFormData();

    // Attach listener to all text inputs and textareas
    const inputs = document.querySelectorAll('#caseStudyForm input[type="text"], #caseStudyForm input[type="url"], #caseStudyForm textarea');
    inputs.forEach(input => {
        input.addEventListener('input', saveFormData);
    });

    // Also attach to checkboxes
    const checkboxes = document.querySelectorAll('#caseStudyForm input[type="checkbox"]');
    checkboxes.forEach(cb => {
        cb.addEventListener('change', saveFormData);
    });
}

function saveFormData() {
    const formData = {
        brandName: document.getElementById('brandName')?.value || '',
        industry: document.getElementById('industry')?.value || '',
        whatWeDid: document.getElementById('whatWeDid')?.value || '',
        howWeDidIt: document.getElementById('howWeDidIt')?.value || '',
        impact: document.getElementById('impact')?.value || '',
        mediaLink: document.getElementById('mediaLink')?.value || '',
        driveLink: document.getElementById('driveLink')?.value || '',
        additionalContext: document.getElementById('additionalContext')?.value || '',
        websiteUrl: document.getElementById('websiteUrl')?.value || '',

        // Save checkbox states separately
        services: Array.from(document.querySelectorAll('.service-tag input[type="checkbox"]'))
            .filter(cb => cb.checked)
            .map(cb => cb.value),
        servicesOther: document.getElementById('servicesOther')?.value || ''
    };

    // Also save API key if entered
    const apiKey = document.getElementById('geminiApiKey');
    if (apiKey && apiKey.value) {
        formData.geminiApiKey = apiKey.value;
    }

    localStorage.setItem('caseStudyDraft', JSON.stringify(formData));
}

function loadFormData() {
    const draft = localStorage.getItem('caseStudyDraft');
    if (draft) {
        try {
            const formData = JSON.parse(draft);

            // Restore text inputs
            const textFields = ['brandName', 'industry', 'whatWeDid', 'howWeDidIt', 'impact',
                'mediaLink', 'driveLink', 'additionalContext', 'websiteUrl',
                'servicesOther', 'geminiApiKey'];

            textFields.forEach(id => {
                const el = document.getElementById(id);
                if (el && formData[id]) {
                    el.value = formData[id];
                }
            });

            // Restore checkboxes
            if (formData.services && Array.isArray(formData.services)) {
                const checkboxes = document.querySelectorAll('.service-tag input[type="checkbox"]');
                checkboxes.forEach(cb => {
                    cb.checked = formData.services.includes(cb.value);
                });
            }

        } catch (e) {
            console.error('Error loading drafted form data:', e);
        }
    }
}

function initClarifyHandlers() {
    const clarifyBtn = document.getElementById('clarifyBtn');
    const clarificationSection = document.getElementById('clarificationSection');
    const clarificationQuestions = document.getElementById('clarificationQuestions');
    const applyClarificationsBtn = document.getElementById('applyClarificationsBtn');
    const clarificationAnswers = document.getElementById('clarificationAnswers');
    const additionalContext = document.getElementById('additionalContext');

    clarifyBtn.addEventListener('click', async () => {
        // Collect current form data
        const payload = {
            brand_name: document.getElementById('brandName').value.trim(),
            industry: document.getElementById('industry').value,
            services_used: getSelectedServices() || document.getElementById('servicesOther').value.trim(),
            what_we_did: document.getElementById('whatWeDid').value.trim(),
            how_we_did_it: document.getElementById('howWeDidIt').value.trim(),
            impact: document.getElementById('impact').value.trim(),
            media_link: document.getElementById('mediaLink').value.trim(),
            drive_link: document.getElementById('driveLink').value.trim(),
            additional_context: additionalContext.value.trim(),
            website_url: document.getElementById('websiteUrl').value.trim(),
            gemini_api_key: document.getElementById('geminiApiKey').value.trim()
        };

        if (!payload.drive_link && (!payload.brand_name || !payload.what_we_did || !payload.impact)) {
            showError('Please provide EITHER a Google Doc Link OR fill out Brand Name, What We Did, and Impact first.');
            return;
        }

        // UI State
        const btnText = clarifyBtn.querySelector('.btn-text');
        const btnSpinner = clarifyBtn.querySelector('.btn-spinner');
        clarifyBtn.disabled = true;
        btnText.textContent = 'Thinking...';
        btnSpinner.style.display = 'inline-block';
        clarificationSection.style.display = 'none';

        try {
            const response = await fetch('/clarify', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            const data = await response.json();

            if (data.success) {
                // Render questions
                clarificationQuestions.innerHTML = '';
                data.questions.forEach((q, i) => {
                    const p = document.createElement('p');
                    p.style.fontWeight = '500';
                    p.style.marginBottom = '0.5rem';
                    p.textContent = `${i + 1}. ${q}`;
                    clarificationQuestions.appendChild(p);
                });
                clarificationSection.style.display = 'block';
                clarificationAnswers.value = ''; // Reset answers
                clarificationAnswers.focus();
            } else {
                alert(`Error: ${data.error}`);
            }
        } catch (error) {
            alert(`Error: ${error.message}`);
        } finally {
            clarifyBtn.disabled = false;
            btnText.textContent = 'Ask AI for Suggestions';
            btnSpinner.style.display = 'none';
        }
    });

    applyClarificationsBtn.addEventListener('click', () => {
        const answers = clarificationAnswers.value.trim();
        let userClarifications = "";

        if (answers) {
            // Keep clarifications separate for the backend to feed into the prompt
            userClarifications = answers;
        }
        clarificationSection.style.display = 'none';

        // Trigger main generation, passing the clarifications along natively
        // We temporarily attach it to the form so handleGenerate can pick it up
        document.getElementById('caseStudyForm').dataset.clarifications = userClarifications;
        document.getElementById('caseStudyForm').dispatchEvent(new Event('submit', { cancelable: true, bubbles: true }));
    });
}

function initFormHandlers() {
    const form = document.getElementById('caseStudyForm');
    form.addEventListener('submit', handleGenerate);
}


function initAPIKeyToggle() {
    const section = document.getElementById('apiKeySection');
    const header = section.querySelector('.collapsible-header');

    header.addEventListener('click', () => {
        section.classList.toggle('open');
    });
}


function getSelectedServices() {
    const checkboxes = document.querySelectorAll('.service-tag input[type="checkbox"]:checked');
    return Array.from(checkboxes).map(cb => cb.value).join(', ');
}


async function handleGenerate(e) {
    e.preventDefault();

    const btn = document.getElementById('generateBtn');
    const progressSection = document.getElementById('progressSection');
    const resultSection = document.getElementById('resultSection');

    // Collect form data
    const data = {
        brand_name: document.getElementById('brandName').value.trim(),
        industry: document.getElementById('industry').value.trim(),
        services_used: getSelectedServices() || document.getElementById('servicesOther').value.trim(),
        what_we_did: document.getElementById('whatWeDid').value.trim(),
        how_we_did_it: document.getElementById('howWeDidIt').value.trim(),
        impact: document.getElementById('impact').value.trim(),
        media_link: document.getElementById('mediaLink').value.trim(),
        drive_link: document.getElementById('driveLink').value.trim(),
        additional_context: document.getElementById('additionalContext').value.trim(),
        user_clarifications: document.getElementById('caseStudyForm').dataset.clarifications || "",
        website_url: document.getElementById('websiteUrl').value.trim(),
        gemini_api_key: document.getElementById('geminiApiKey').value.trim()
    };

    // Validation
    if (!data.drive_link && (!data.brand_name || !data.what_we_did || !data.impact)) {
        showError('Please provide EITHER a Google Doc Link OR fill in Brand Name, What We Did, and Impact.');
        return;
    }

    btn.classList.add('loading');
    btn.disabled = true;
    resultSection.classList.remove('visible');
    resultSection.innerHTML = '';
    progressSection.classList.add('visible');

    // Clean up temporary dataset
    document.getElementById('caseStudyForm').dataset.clarifications = "";

    updateProgress(1, 'Deep Mehta is analyzing and writing...');

    try {
        const response = await fetch('/generate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });

        const result = await response.json();

        if (!response.ok) {
            throw new Error(result.error || 'Something went wrong');
        }

        updateProgress(2, 'Content generated! Building slides...');

        // Small delay for UX
        await sleep(800);

        if (result.slides_url) {
            updateProgress(3, 'Google Slides ready!');
            await sleep(500);
        }

        showResult(result);

    } catch (error) {
        showError(error.message);
    } finally {
        btn.classList.remove('loading');
        btn.disabled = false;
        progressSection.classList.remove('visible');
    }
}


function buildImpactString() {
    const parts = [];

    for (let i = 1; i <= 3; i++) {
        const value = document.getElementById(`kpiValue${i}`).value.trim();
        const label = document.getElementById(`kpiLabel${i}`).value.trim();
        const timeframe = document.getElementById(`kpiTimeframe${i}`)?.value.trim();

        if (value && label) {
            let kpi = `${value} ${label}`;
            if (timeframe) kpi += ` (${timeframe})`;
            parts.push(kpi);
        }
    }

    const additionalImpact = document.getElementById('additionalImpact')?.value.trim();
    if (additionalImpact) {
        parts.push(additionalImpact);
    }

    return parts.join('\n');
}


function updateProgress(step, message) {
    const steps = document.querySelectorAll('.progress-step');
    const messageEl = document.querySelector('.progress-message');

    steps.forEach((stepEl, i) => {
        stepEl.classList.remove('active', 'complete');
        if (i + 1 < step) stepEl.classList.add('complete');
        if (i + 1 === step) stepEl.classList.add('active');
    });

    if (messageEl) messageEl.textContent = message;
}


function showResult(result) {
    const section = document.getElementById('resultSection');

    let html = '<div class="result-card">';
    html += '<span class="success-icon">🎉</span>';
    html += '<h3>Case Study Generated!</h3>';

    if (result.slides_url) {
        html += `<p>Your Google Slides presentation is ready.</p>`;
        html += `<a href="${result.slides_url}" target="_blank" class="slides-link">
            <span>📊</span> Open in Google Slides
        </a>`;
    } else if (result.slides_error) {
        html += `<p>Content generated successfully, but we couldn't create the Google Slides.</p>`;
        html += `<div class="slides-warning">
            <strong>⚠️ Google Slides Setup Needed</strong>
            ${result.slides_error}<br><br>
            To enable automatic Slides creation:<br>
            1. Download OAuth credentials from Google Cloud Console<br>
            2. Save as <code>credentials.json</code> in the project folder<br>
            3. Visit <code>/auth/google</code> to authorize
        </div>`;
    } else {
        html += `<p>Content generated successfully! Review it below.</p>`;
    }

    // Content preview
    if (result.content) {
        html += `<div class="content-preview">
            <button class="preview-toggle" onclick="togglePreview()">
                <span>📝</span> View Generated Content
            </button>
            <div id="previewContent" class="preview-content">
                <pre>${formatContentPreview(result.content)}</pre>
            </div>
        </div>`;
    }

    html += '</div>';

    section.innerHTML = html;
    section.classList.add('visible');

    // Scroll to result
    section.scrollIntoView({ behavior: 'smooth', block: 'start' });
}


function showError(message) {
    const section = document.getElementById('resultSection');

    section.innerHTML = `
        <div class="error-card">
            <span class="error-icon">❌</span>
            <h3>Generation Failed</h3>
            <p>${message}</p>
            <button class="retry-btn" onclick="document.getElementById('resultSection').classList.remove('visible')">
                ↻ Try Again
            </button>
        </div>
    `;

    section.classList.add('visible');
    section.scrollIntoView({ behavior: 'smooth', block: 'start' });
}


function togglePreview() {
    const content = document.getElementById('previewContent');
    content.classList.toggle('visible');
}


function formatContentPreview(content) {
    const sections = [
        ['📌 Case Study Title', content.case_study_title],
        ['🏢 Brand', `${content.brand_name} (${content.industry})`],
        ['🔧 Services', content.services_used],
        ['📊 KPI Highlights', `• ${content.kpi_1_number} ${content.kpi_1_label}\n• ${content.kpi_2_number} ${content.kpi_2_label}\n• ${content.kpi_3_number} ${content.kpi_3_label}`],
        ['📁 Media Assets', content.media_link],
        ['ℹ️ About the Brand', content.about_brand],
        ['⚡ Challenge', content.challenge],
        ['🔍 Core Insight', content.core_insight],
        ['🎯 Strategy', content.strategy],
        ['🚀 Delivery & Solution', content.delivery_solution],
        ['📋 Key Actions', content.delivery_steps],
        ['🛠️ Tools Used', content.tools_used],
        ['📈 Impact & Results', content.impact_metrics],
        ['💬 Client Testimonial', content.client_testimonial],
        ['💡 Learnings', content.learnings],
        ['⏭️ Next Steps', content.next_steps],
        ['📣 CTA', content.cta]
    ];

    return sections
        .filter(([, val]) => val)
        .map(([label, val]) => `${label}\n${'-'.repeat(40)}\n${val}`)
        .join('\n\n');
}


function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}
