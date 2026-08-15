/**
 * SEMCAT / RoSE AMR Evaluator - Frontend Application Script
 */

document.addEventListener('DOMContentLoaded', () => {
    // Initialize Lucide Icons
    lucide.createIcons();

    // Elements
    const refInput = document.getElementById('refInput');
    const hypInput = document.getElementById('hypInput');
    const nIterSlider = document.getElementById('nIterSlider');
    const tauSlider = document.getElementById('tauSlider');
    const nIterValue = document.getElementById('nIterValue');
    const tauValue = document.getElementById('tauValue');
    const btnEvaluate = document.getElementById('btnEvaluate');
    
    const resultsSection = document.getElementById('resultsSection');
    const scoreDisplay = document.getElementById('scoreDisplay');
    const scorePercent = document.getElementById('scorePercent');
    const gaugeProgress = document.getElementById('gaugeProgress');
    const verdictBadge = document.getElementById('verdictBadge');
    const verdictText = document.getElementById('verdictText');
    const elapsedTimeVal = document.getElementById('elapsedTimeVal');
    const metricNameVal = document.getElementById('metricNameVal');
    
    const refNodesVal = document.getElementById('refNodesVal');
    const hypNodesVal = document.getElementById('hypNodesVal');
    const refTopConcept = document.getElementById('refTopConcept');
    const hypTopConcept = document.getElementById('hypTopConcept');
    const refVarCount = document.getElementById('refVarCount');
    const hypVarCount = document.getElementById('hypVarCount');
    const refEdgeCount = document.getElementById('refEdgeCount');
    const hypEdgeCount = document.getElementById('hypEdgeCount');
    const refTripleCount = document.getElementById('refTripleCount');
    const hypTripleCount = document.getElementById('hypTripleCount');

    const examplesContainer = document.getElementById('examplesContainer');

    // Tab Navigation
    const navButtons = document.querySelectorAll('.nav-btn');
    const tabContents = document.querySelectorAll('.tab-content');

    navButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            navButtons.forEach(b => b.classList.remove('active'));
            tabContents.forEach(c => c.classList.remove('active'));

            btn.classList.add('active');
            const targetTab = btn.getAttribute('data-tab');
            document.getElementById(targetTab).classList.add('active');
        });
    });

    // Hyperparameter Sliders Sync
    nIterSlider.addEventListener('input', (e) => {
        nIterValue.textContent = e.target.value;
    });

    tauSlider.addEventListener('input', (e) => {
        tauValue.textContent = parseFloat(e.target.value).toFixed(2);
    });

    // Character Counters & Clear Buttons
    const refCharCount = document.getElementById('refCharCount');
    const hypCharCount = document.getElementById('hypCharCount');

    refInput.addEventListener('input', () => {
        refCharCount.textContent = `${refInput.value.length} chars`;
    });
    hypInput.addEventListener('input', () => {
        hypCharCount.textContent = `${hypInput.value.length} chars`;
    });

    document.getElementById('btnClearRef').addEventListener('click', () => {
        refInput.value = '';
        refCharCount.textContent = '0 chars';
    });
    document.getElementById('btnClearHyp').addEventListener('click', () => {
        hypInput.value = '';
        hypCharCount.textContent = '0 chars';
    });

    document.getElementById('btnCopyRef').addEventListener('click', () => {
        navigator.clipboard.writeText(refInput.value);
        alert('Đã sao chép Reference AMR!');
    });
    document.getElementById('btnCopyHyp').addEventListener('click', () => {
        navigator.clipboard.writeText(hypInput.value);
        alert('Đã sao chép Hypothesis AMR!');
    });

    // Load Examples from API
    async function loadExamples() {
        try {
            const res = await fetch('/api/examples');
            const data = await res.json();

            examplesContainer.innerHTML = '';
            data.examples.forEach(ex => {
                const card = document.createElement('div');
                card.className = 'example-card';
                card.innerHTML = `
                    <h4>${ex.title}</h4>
                    <p>${ex.description}</p>
                `;
                card.addEventListener('click', () => {
                    refInput.value = ex.ref;
                    hypInput.value = ex.hyp;
                    nIterSlider.value = ex.n_iter;
                    tauSlider.value = ex.tau;
                    nIterValue.textContent = ex.n_iter;
                    tauValue.textContent = ex.tau;
                    refCharCount.textContent = `${ex.ref.length} chars`;
                    hypCharCount.textContent = `${ex.hyp.length} chars`;
                    runEvaluation();
                });
                examplesContainer.appendChild(card);
            });
        } catch (err) {
            console.error('Failed to load examples:', err);
        }
    }
    loadExamples();

    // Radial Gauge Animate Function
    function setGaugeScore(score, color) {
        // SVG Circle radius = 85, Circumference = 2 * PI * 85 ~= 534
        const circumference = 534;
        const offset = circumference - (score * circumference);
        gaugeProgress.style.strokeDashoffset = offset;
        gaugeProgress.style.stroke = color;

        // Number count-up animation
        let start = 0;
        const duration = 1000;
        const startTime = performance.now();

        function updateNumber(currentTime) {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);
            const currentVal = start + progress * (score - start);
            scoreDisplay.textContent = currentVal.toFixed(4);
            scorePercent.textContent = `${(currentVal * 100).toFixed(1)}%`;

            if (progress < 1) {
                requestAnimationFrame(updateNumber);
            }
        }
        requestAnimationFrame(updateNumber);
    }

    // Run Single Evaluation
    async function runEvaluation() {
        const refVal = refInput.value.trim();
        const hypVal = hypInput.value.trim();

        if (!refVal || !hypVal) {
            alert('⚠️ Vui lòng nhập đầy đủ cả Reference AMR và Hypothesis AMR!');
            return;
        }

        btnEvaluate.disabled = true;
        btnEvaluate.innerHTML = `<i data-lucide="loader" class="spin"></i> Đang tính toán...`;
        lucide.createIcons();

        try {
            const response = await fetch('/api/evaluate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    ref_amr: refVal,
                    hyp_amr: hypVal,
                    num_iterations: parseInt(nIterSlider.value),
                    similarity_threshold_tau: parseFloat(tauSlider.value)
                })
            });

            const data = await response.json();

            if (!response.ok || !data.success) {
                alert(`❌ Lỗi: ${data.message || data.detail || 'Không thể thực hiện đánh giá'}`);
                return;
            }

            // Show results section
            resultsSection.classList.remove('hidden');
            resultsSection.scrollIntoView({ behavior: 'smooth' });

            // Animate Gauge & Verdict
            setGaugeScore(data.score, data.verdict.color);
            verdictText.textContent = data.verdict.text;
            verdictBadge.style.backgroundColor = `${data.verdict.color}22`;
            verdictBadge.style.borderColor = data.verdict.color;
            verdictBadge.style.color = data.verdict.color;

            // Stats breakdown
            elapsedTimeVal.textContent = `${data.elapsed_ms} ms`;
            metricNameVal.textContent = data.metric_name;

            const refS = data.stats.reference;
            const hypS = data.stats.hypothesis;

            refNodesVal.textContent = `${refS.variables_count} concepts`;
            hypNodesVal.textContent = `${hypS.variables_count} concepts`;

            refTopConcept.textContent = refS.top_concept || '-';
            hypTopConcept.textContent = hypS.top_concept || '-';

            refVarCount.textContent = refS.variables_count;
            hypVarCount.textContent = hypS.variables_count;

            refEdgeCount.textContent = refS.edges_count;
            hypEdgeCount.textContent = hypS.edges_count;

            refTripleCount.textContent = refS.total_triples;
            hypTripleCount.textContent = hypS.total_triples;

        } catch (err) {
            alert(`❌ Lỗi kết nối API: ${err.message}`);
        } finally {
            btnEvaluate.disabled = false;
            btnEvaluate.innerHTML = `<i data-lucide="play"></i> Tính Toán Độ Tương Đồng`;
            lucide.createIcons();
        }
    }

    btnEvaluate.addEventListener('click', runEvaluation);
});
