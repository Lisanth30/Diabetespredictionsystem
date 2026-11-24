// Predictor and Compact Live BMI Calculator with 5-Second Medical AI Analysis Animation
document.addEventListener('DOMContentLoaded', () => {
  const bmiInput = document.getElementById('bmi');
  const heightMetric = document.getElementById('calcHeightCm');
  const weightMetric = document.getElementById('calcWeightKg');
  const heightFt = document.getElementById('calcHeightFt');
  const heightIn = document.getElementById('calcHeightIn');
  const weightLbs = document.getElementById('calcWeightLbs');

  const btnMetric = document.getElementById('tabMetric');
  const btnImperial = document.getElementById('tabImperial');
  const sectionMetric = document.getElementById('metricInputs');
  const sectionImperial = document.getElementById('imperialInputs');

  const bmiValueDisplay = document.getElementById('calcBmiValue');
  const bmiBadgeDisplay = document.getElementById('calcBmiBadge');
  const applyBmiBtn = document.getElementById('applyBmiBtn');

  const bmiValueDisplayImp = document.getElementById('calcBmiValueImp');
  const bmiBadgeDisplayImp = document.getElementById('calcBmiBadgeImp');
  const applyBmiBtnImp = document.getElementById('applyBmiBtnImp');

  const toggleBmiHelperBtn = document.getElementById('toggleBmiHelper');
  const bmiHelperContainer = document.getElementById('bmiHelperContainer');

  let activeUnit = 'metric';
  let currentCalculatedBmi = null;

  // Toggle Inline BMI Helper Drawer
  if (toggleBmiHelperBtn && bmiHelperContainer) {
    toggleBmiHelperBtn.addEventListener('click', (e) => {
      e.preventDefault();
      const isHidden = bmiHelperContainer.style.display === 'none' || !bmiHelperContainer.style.display;
      bmiHelperContainer.style.display = isHidden ? 'block' : 'none';
      toggleBmiHelperBtn.innerHTML = isHidden 
        ? '<i class="fa-solid fa-xmark"></i> Close Calculator' 
        : '<i class="fa-solid fa-calculator"></i> Calculate BMI';
      if (isHidden && heightMetric) {
        heightMetric.focus();
      }
    });
  }

  // Toggle Units
  if (btnMetric && btnImperial) {
    btnMetric.addEventListener('click', () => {
      activeUnit = 'metric';
      btnMetric.classList.add('active');
      btnImperial.classList.remove('active');
      if (sectionMetric) sectionMetric.style.display = 'grid';
      if (sectionImperial) sectionImperial.style.display = 'none';
      computeBmi();
    });

    btnImperial.addEventListener('click', () => {
      activeUnit = 'imperial';
      btnImperial.classList.add('active');
      btnMetric.classList.remove('active');
      if (sectionMetric) sectionMetric.style.display = 'none';
      if (sectionImperial) sectionImperial.style.display = 'grid';
      computeBmi();
    });
  }

  function getBmiClassification(bmi) {
    if (bmi < 18.5) return { category: 'Underweight', badgeClass: 'badge-neutral' };
    if (bmi <= 24.9) return { category: 'Normal', badgeClass: 'badge-safe' };
    if (bmi <= 29.9) return { category: 'Overweight', badgeClass: 'badge-caution' };
    return { category: 'Obese', badgeClass: 'badge-danger' };
  }

  function computeBmi() {
    let bmi = 0;
    if (activeUnit === 'metric') {
      const hCm = parseFloat(heightMetric?.value || 0);
      const wKg = parseFloat(weightMetric?.value || 0);
      if (hCm > 50 && wKg > 15) {
        const hM = hCm / 100.0;
        bmi = wKg / (hM * hM);
      }
    } else {
      const ft = parseFloat(heightFt?.value || 0);
      const inches = parseFloat(heightIn?.value || 0);
      const totalInches = (ft * 12) + inches;
      const wLbs = parseFloat(weightLbs?.value || 0);
      if (totalInches > 20 && wLbs > 30) {
        bmi = (wLbs * 703) / (totalInches * totalInches);
      }
    }

    if (bmi > 10 && bmi < 90) {
      currentCalculatedBmi = parseFloat(bmi.toFixed(1));
      const info = getBmiClassification(currentCalculatedBmi);

      // Metric display
      if (bmiValueDisplay) bmiValueDisplay.textContent = currentCalculatedBmi;
      if (bmiBadgeDisplay) {
        bmiBadgeDisplay.textContent = info.category;
        bmiBadgeDisplay.className = `badge ${info.badgeClass}`;
      }
      if (applyBmiBtn) applyBmiBtn.disabled = false;

      // Imperial display
      if (bmiValueDisplayImp) bmiValueDisplayImp.textContent = currentCalculatedBmi;
      if (bmiBadgeDisplayImp) {
        bmiBadgeDisplayImp.textContent = info.category;
        bmiBadgeDisplayImp.className = `badge ${info.badgeClass}`;
      }
      if (applyBmiBtnImp) applyBmiBtnImp.disabled = false;
    } else {
      currentCalculatedBmi = null;
      if (bmiValueDisplay) bmiValueDisplay.textContent = '--.-';
      if (bmiBadgeDisplay) {
        bmiBadgeDisplay.textContent = 'Awaiting Input';
        bmiBadgeDisplay.className = 'badge badge-neutral';
      }
      if (applyBmiBtn) applyBmiBtn.disabled = true;

      if (bmiValueDisplayImp) bmiValueDisplayImp.textContent = '--.-';
      if (bmiBadgeDisplayImp) {
        bmiBadgeDisplayImp.textContent = 'Awaiting Input';
        bmiBadgeDisplayImp.className = 'badge badge-neutral';
      }
      if (applyBmiBtnImp) applyBmiBtnImp.disabled = true;
    }
  }

  // Attach event listeners for real-time BMI calculations
  [heightMetric, weightMetric, heightFt, heightIn, weightLbs].forEach(input => {
    if (input) {
      input.addEventListener('input', computeBmi);
    }
  });

  // Apply BMI to prediction form input
  function applyBmiValue(e) {
    e.preventDefault();
    if (currentCalculatedBmi && bmiInput) {
      bmiInput.value = currentCalculatedBmi;
      bmiInput.style.transition = 'box-shadow 0.3s ease, border-color 0.3s ease';
      bmiInput.style.borderColor = 'var(--primary)';
      bmiInput.style.boxShadow = '0 0 0 4px rgba(79, 70, 229, 0.25)';
      setTimeout(() => {
        bmiInput.style.boxShadow = '';
        bmiInput.style.borderColor = '';
      }, 1200);

      // Close the helper drawer cleanly
      if (bmiHelperContainer) {
        bmiHelperContainer.style.display = 'none';
      }
      if (toggleBmiHelperBtn) {
        toggleBmiHelperBtn.innerHTML = '<i class="fa-solid fa-calculator"></i> Calculate BMI';
      }
    }
  }

  if (applyBmiBtn) applyBmiBtn.addEventListener('click', applyBmiValue);
  if (applyBmiBtnImp) applyBmiBtnImp.addEventListener('click', applyBmiValue);

  // Quick Preset Profiles Auto-Filler (All 8 Dataset Parameters)
  window.loadPresetProfile = function(type) {
    const profiles = {
      optimal: {
        pregnancies: 1,
        glucose: 88,
        blood_pressure: 72,
        skin_thickness: 20,
        insulin: 75,
        bmi: 22.4,
        diabetes_pedigree_function: 0.248,
        age: 26
      },
      moderate: {
        pregnancies: 3,
        glucose: 118,
        blood_pressure: 82,
        skin_thickness: 28,
        insulin: 120,
        bmi: 28.4,
        diabetes_pedigree_function: 0.485,
        age: 41
      },
      elevated: {
        pregnancies: 6,
        glucose: 165,
        blood_pressure: 88,
        skin_thickness: 35,
        insulin: 210,
        bmi: 34.8,
        diabetes_pedigree_function: 0.725,
        age: 52
      }
    };

    const p = profiles[type];
    if (!p) return;

    for (const [id, val] of Object.entries(p)) {
      const el = document.getElementById(id);
      if (el) {
        el.value = val;
        el.style.transition = 'background-color 0.4s ease';
        el.style.backgroundColor = '#eef2ff';
        setTimeout(() => {
          el.style.backgroundColor = '';
        }, 800);
      }
    }
  };

  // ==============================================================================
  // 5-Second Medical AI Analysis Animation Controller
  // ==============================================================================
  const predictForm = document.getElementById('predictionForm');
  const analysisModal = document.getElementById('analysisModal');
  const progressBar = document.getElementById('analysisProgressBar');
  const percentText = document.getElementById('analysisPercentText');
  const countdownText = document.getElementById('analysisCountdownText');
  const statusBadge = document.getElementById('analysisStatusBadge');
  const stepDesc = document.getElementById('analysisStepDesc');
  const submitBtn = document.getElementById('runAnalysisBtn');

  let isSubmitting = false;

  if (predictForm) {
    predictForm.addEventListener('submit', (e) => {
      // If already undergoing 5-second analysis, allow default submit
      if (isSubmitting) return;

      e.preventDefault();

      // 1. Validate Form Inputs (All 8 Dataset Parameters)
      const pregnancies = parseInt(document.getElementById('pregnancies')?.value, 10);
      const glucose = parseFloat(document.getElementById('glucose')?.value);
      const bp = parseFloat(document.getElementById('blood_pressure')?.value);
      const skinThickness = parseFloat(document.getElementById('skin_thickness')?.value);
      const insulin = parseFloat(document.getElementById('insulin')?.value);
      const bmi = parseFloat(document.getElementById('bmi')?.value);
      const dpf = parseFloat(document.getElementById('diabetes_pedigree_function')?.value);
      const age = parseInt(document.getElementById('age')?.value, 10);

      function showFieldWarning(id, message) {
        const field = document.getElementById(id);
        if (field) {
          field.focus();
          field.style.borderColor = 'var(--danger)';
          field.style.boxShadow = '0 0 0 4px rgba(239, 68, 68, 0.2)';
          setTimeout(() => {
            field.style.borderColor = '';
            field.style.boxShadow = '';
          }, 3000);
        }
        alert(message);
      }

      if (isNaN(pregnancies) || pregnancies < 0 || pregnancies > 25) {
        showFieldWarning('pregnancies', 'Please enter a valid number of pregnancies between 0 and 25.');
        return;
      }
      if (isNaN(glucose) || glucose < 40 || glucose > 300) {
        showFieldWarning('glucose', 'Please enter a valid fasting plasma glucose reading between 40 and 300 mg/dL.');
        return;
      }
      if (isNaN(bp) || bp < 30 || bp > 200) {
        showFieldWarning('blood_pressure', 'Please enter a valid diastolic blood pressure between 30 and 200 mm Hg.');
        return;
      }
      if (isNaN(skinThickness) || skinThickness < 0 || skinThickness > 100) {
        showFieldWarning('skin_thickness', 'Please enter a valid triceps skin thickness between 0 and 100 mm.');
        return;
      }
      if (isNaN(insulin) || insulin < 0 || insulin > 900) {
        showFieldWarning('insulin', 'Please enter a valid 2-hour serum insulin value between 0 and 900 μU/mL.');
        return;
      }
      if (isNaN(bmi) || bmi < 10 || bmi > 75) {
        showFieldWarning('bmi', 'Please enter a valid Body Mass Index (BMI) between 10.0 and 75.0 kg/m².');
        return;
      }
      if (isNaN(dpf) || dpf < 0.05 || dpf > 3.0) {
        showFieldWarning('diabetes_pedigree_function', 'Please enter a valid Diabetes Pedigree Function score between 0.05 and 3.0.');
        return;
      }
      if (isNaN(age) || age < 15 || age > 120) {
        showFieldWarning('age', 'Please enter a valid patient age between 15 and 120 years.');
        return;
      }

      // 2. Start 5-Second Analysis Animation
      if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Initializing Analysis Engine...';
      }

      if (analysisModal) {
        analysisModal.style.display = 'flex';
        analysisModal.setAttribute('aria-hidden', 'false');
      }

      const totalDuration = 5000; // Exact 5 seconds
      const startTime = performance.now();

      const stages = [
        {
          threshold: 0.25,
          badge: '<i class="fa-solid fa-microchip"></i> Stage 1 of 4: Normalization',
          desc: 'Standardizing clinical biomarkers via StandardScaler...'
        },
        {
          threshold: 0.50,
          badge: '<i class="fa-solid fa-scale-balanced"></i> Stage 2 of 4: Clinical Standards',
          desc: 'Cross-referencing Fasting Glucose & BMI against ADA & WHO benchmarks...'
        },
        {
          threshold: 0.75,
          badge: '<i class="fa-solid fa-brain"></i> Stage 3 of 4: Logistic Regression',
          desc: 'Computing statistical decision boundaries and risk probability...'
        },
        {
          threshold: 1.00,
          badge: '<i class="fa-solid fa-file-medical"></i> Stage 4 of 4: Report Synthesis',
          desc: 'Finalizing risk stratification & compiling clinical recommendations...'
        }
      ];

      function updateAnimation(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / totalDuration, 1.0);
        const percent = Math.floor(progress * 100);
        const remainingSeconds = Math.max(0, ((totalDuration - elapsed) / 1000)).toFixed(1);

        // Update progress bar & counters
        if (progressBar) progressBar.style.width = `${percent}%`;
        if (percentText) percentText.textContent = `${percent}%`;
        if (countdownText) countdownText.textContent = `${remainingSeconds}s remaining`;

        // Update stages
        let currentStage = stages[stages.length - 1];
        for (const stage of stages) {
          if (progress <= stage.threshold) {
            currentStage = stage;
            break;
          }
        }

        if (statusBadge && statusBadge.innerHTML !== currentStage.badge) {
          statusBadge.innerHTML = currentStage.badge;
        }
        if (stepDesc && stepDesc.textContent !== currentStage.desc) {
          stepDesc.textContent = currentStage.desc;
        }

        if (progress < 1.0) {
          requestAnimationFrame(updateAnimation);
        } else {
          // 5 seconds completed!
          if (statusBadge) {
            statusBadge.innerHTML = '<i class="fa-solid fa-circle-check" style="color: var(--safe);"></i> Analysis Complete!';
          }
          if (stepDesc) {
            stepDesc.textContent = 'Screening successfully analyzed! Redirecting to report...';
          }
          if (countdownText) {
            countdownText.textContent = '0.0s';
          }

          setTimeout(() => {
            isSubmitting = true;
            predictForm.submit();
          }, 350);
        }
      }

      requestAnimationFrame(updateAnimation);
    });
  }

  // ==============================================================================
  // 📸 9. Health Report & Dataset Uploader (CSV / Excel / OCR) Controller
  // ==============================================================================
  const fileInput = document.getElementById('reportFileInput');
  const dropzone = document.getElementById('scannerDropzone');
  const progressWrap = document.getElementById('scannerProgressWrap');
  const progressFill = document.getElementById('scannerProgressFill');
  const statusLabel = document.getElementById('scannerStatusLabel');
  const statusPercent = document.getElementById('scannerStatusPercent');
  const verificationDrawer = document.getElementById('verificationDrawer');
  const verificationGrid = document.getElementById('verificationGrid');
  const detectedCountBadge = document.getElementById('detectedCountBadge');
  const datasetRowSelectorBar = document.getElementById('datasetRowSelectorBar');
  const datasetFileSummary = document.getElementById('datasetFileSummary');
  const datasetRowSelect = document.getElementById('datasetRowSelect');
  const datasetPrevRowBtn = document.getElementById('datasetPrevRowBtn');
  const datasetNextRowBtn = document.getElementById('datasetNextRowBtn');

  let currentExtractedData = {};
  let currentDatasetRows = [];

  if (dropzone && fileInput) {
    // Drag & Drop events
    ['dragenter', 'dragover'].forEach(eventName => {
      dropzone.addEventListener(eventName, (e) => {
        e.preventDefault();
        e.stopPropagation();
        dropzone.classList.add('drag-over');
      }, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
      dropzone.addEventListener(eventName, (e) => {
        e.preventDefault();
        e.stopPropagation();
        dropzone.classList.remove('drag-over');
      }, false);
    });

    dropzone.addEventListener('drop', (e) => {
      const dt = e.dataTransfer;
      const files = dt.files;
      if (files && files.length > 0) {
        processLabReportFile(files[0]);
      }
    });

    fileInput.addEventListener('change', (e) => {
      if (e.target.files && e.target.files.length > 0) {
        processLabReportFile(e.target.files[0]);
        fileInput.value = '';
      }
    });
  }

  function loadDatasetRowIntoDrawer(rowIndex) {
    if (!currentDatasetRows.length) return;
    const clampedIndex = Math.max(0, Math.min(rowIndex, currentDatasetRows.length - 1));
    const row = currentDatasetRows[clampedIndex];
    if (datasetRowSelect) datasetRowSelect.value = String(clampedIndex);
    if (datasetPrevRowBtn) datasetPrevRowBtn.disabled = clampedIndex === 0;
    if (datasetNextRowBtn) datasetNextRowBtn.disabled = clampedIndex === currentDatasetRows.length - 1;

    const mapped = {};
    const keys = ['pregnancies', 'glucose', 'blood_pressure', 'skin_thickness', 'insulin', 'bmi', 'diabetes_pedigree_function', 'age'];
    keys.forEach(k => {
      if (row[k] !== undefined && row[k] !== null) {
        mapped[k] = { value: row[k], confidence: 100 };
      }
    });
    renderVerificationDrawer(mapped, Object.keys(mapped).length, false);
  }

  if (datasetRowSelect) {
    datasetRowSelect.addEventListener('change', () => {
      loadDatasetRowIntoDrawer(parseInt(datasetRowSelect.value, 10) || 0);
    });
  }
  if (datasetPrevRowBtn) {
    datasetPrevRowBtn.addEventListener('click', () => {
      const cur = parseInt(datasetRowSelect?.value || '0', 10);
      loadDatasetRowIntoDrawer(cur - 1);
    });
  }
  if (datasetNextRowBtn) {
    datasetNextRowBtn.addEventListener('click', () => {
      const cur = parseInt(datasetRowSelect?.value || '0', 10);
      loadDatasetRowIntoDrawer(cur + 1);
    });
  }

  window.cancelScanVerification = function() {
    if (verificationDrawer) verificationDrawer.style.display = 'none';
    if (datasetRowSelectorBar) datasetRowSelectorBar.style.display = 'none';
    if (fileInput) fileInput.value = '';
    currentExtractedData = {};
    currentDatasetRows = [];
  };

  window.applyExtractedValues = function() {
    const verifiedInputs = document.querySelectorAll('.verify-val-input');
    let appliedCount = 0;

    verifiedInputs.forEach(input => {
      const fieldName = input.getAttribute('data-field');
      const val = input.value.trim();
      if (!val) return;

      const targetField = document.getElementById(fieldName);
      if (targetField) {
        targetField.value = val;
        // Visual green flash
        targetField.style.transition = 'all 0.3s ease';
        targetField.style.backgroundColor = '#ecfdf5';
        targetField.style.borderColor = '#10b981';
        targetField.style.boxShadow = '0 0 0 3px rgba(16, 185, 129, 0.25)';
        setTimeout(() => {
          targetField.style.backgroundColor = '';
          targetField.style.borderColor = '';
          targetField.style.boxShadow = '';
        }, 2200);
        appliedCount++;
      }
    });

    if (verificationDrawer) verificationDrawer.style.display = 'none';

    // Smooth scroll down to the form
    const formEl = document.getElementById('predictionForm');
    if (formEl) {
      formEl.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }

    // Temporary success alert
    if (dropzone) {
      const originalHtml = dropzone.innerHTML;
      dropzone.innerHTML = `
        <div style="color: #16a34a; font-weight: 700; font-size: 0.95rem; display: flex; align-items: center; justify-content: center; gap: 0.5rem;">
          <i class="fa-solid fa-circle-check" style="font-size: 1.3rem;"></i>
          <span>Successfully applied ${appliedCount} extracted values to screening form!</span>
        </div>
      `;
      setTimeout(() => {
        dropzone.innerHTML = originalHtml;
      }, 4000);
    }
  };

  function processLabReportFile(file) {
    if (!file) return;

    if (progressWrap) progressWrap.style.display = 'block';
    if (verificationDrawer) verificationDrawer.style.display = 'none';

    // Simulated progress stages
    let pct = 15;
    if (progressFill) progressFill.style.width = `${pct}%`;
    if (statusPercent) statusPercent.textContent = `${pct}%`;
    if (statusLabel) statusLabel.textContent = `Reading document: ${file.name}...`;

    const progressInterval = setInterval(() => {
      if (pct < 85) {
        pct += 12;
        if (progressFill) progressFill.style.width = `${pct}%`;
        if (statusPercent) statusPercent.textContent = `${pct}%`;
        if (pct > 50 && statusLabel) {
          statusLabel.textContent = 'OCR analyzing biochemical indicators (Glucose, BP, BMI)...';
        }
      }
    }, 250);

    const formData = new FormData();
    formData.append('report_file', file);

    fetch('/api/scan-report', {
      method: 'POST',
      body: formData
    })
    .then(res => res.json())
    .then(data => {
      clearInterval(progressInterval);
      if (progressFill) progressFill.style.width = '100%';
      if (statusPercent) statusPercent.textContent = '100%';
      if (statusLabel) statusLabel.textContent = 'Biomarkers parsed successfully!';

      setTimeout(() => {
        if (progressWrap) progressWrap.style.display = 'none';
        if (data.success && data.data && data.data.extracted && data.data.detected_count > 0) {
          if (data.data.is_dataset && Array.isArray(data.data.dataset_rows) && data.data.dataset_rows.length > 0) {
            currentDatasetRows = data.data.dataset_rows;
            if (datasetFileSummary) {
              datasetFileSummary.textContent = `${data.filename || 'Dataset'} (${currentDatasetRows.length} records)`;
            }
            if (datasetRowSelect) {
              datasetRowSelect.innerHTML = currentDatasetRows.map((row, idx) => {
                const g = row.glucose !== undefined ? `Glu: ${row.glucose}` : '';
                const bmi = row.bmi !== undefined ? `BMI: ${row.bmi}` : '';
                const age = row.age !== undefined ? `Age: ${row.age}` : '';
                const summary = [g, bmi, age].filter(Boolean).join(', ');
                return `<option value="${idx}">Row #${row._row_num || (idx + 1)}${summary ? ' — ' + summary : ''}</option>`;
              }).join('');
            }
            if (datasetRowSelectorBar) {
              datasetRowSelectorBar.style.display = 'flex';
            }
            loadDatasetRowIntoDrawer(0);
          } else {
            currentDatasetRows = [];
            if (datasetRowSelectorBar) datasetRowSelectorBar.style.display = 'none';
            renderVerificationDrawer(data.data.extracted, data.data.detected_count, true);
          }
        } else {
          alert(data.error || 'No recognized clinical markers found in file. Please check the file format or column headers.');
        }
      }, 450);
    })
    .catch(err => {
      clearInterval(progressInterval);
      if (progressWrap) progressWrap.style.display = 'none';
      alert('Error during file processing. Please verify the file or enter parameters manually.');
      console.error(err);
    });
  }

  function renderVerificationDrawer(extracted, count) {
    currentExtractedData = extracted;
    if (!verificationGrid || !verificationDrawer) return;

    if (detectedCountBadge) {
      detectedCountBadge.textContent = `${count} Markers Extracted`;
    }

    const fieldMetadata = [
      { key: 'pregnancies', label: 'Pregnancies', icon: 'person-breastfeeding', normal: '0–3' },
      { key: 'glucose', label: 'Glucose (mg/dL)', icon: 'droplet', normal: '70–99 mg/dL' },
      { key: 'blood_pressure', label: 'Blood Pressure (mm Hg)', icon: 'heart-pulse', normal: '60–80 mm Hg' },
      { key: 'skin_thickness', label: 'Skin Thickness (mm)', icon: 'ruler', normal: '10–25 mm' },
      { key: 'insulin', label: 'Insulin (μU/mL)', icon: 'vial', normal: '16–166 μU/mL' },
      { key: 'bmi', label: 'BMI (kg/m²)', icon: 'weight-scale', normal: '18.5–24.9' },
      { key: 'diabetes_pedigree_function', label: 'Diabetes Pedigree Function', icon: 'dna', normal: '0.08–0.45' },
      { key: 'age', label: 'Age (years)', icon: 'user', normal: 'Adult' }
    ];

    let html = '';
    fieldMetadata.forEach(item => {
      const match = extracted[item.key];
      const isFound = Boolean(match);
      const val = isFound ? match.value : '';

      html += `
        <div class="verify-param-card ${isFound ? 'found' : ''}">
          <div style="display: flex; justify-content: space-between; align-items: center;">
            <span class="verify-label">
              <i class="fa-solid fa-${item.icon}" style="color: var(--primary);"></i> ${item.label}
            </span>
            ${isFound 
              ? `<span style="font-size: 0.7rem; color: #16a34a; font-weight: 700;"><i class="fa-solid fa-check"></i> ${match.confidence}%</span>` 
              : `<span style="font-size: 0.7rem; color: #94a3b8;">Not in report</span>`
            }
          </div>
          <input 
            type="number" 
            step="any" 
            class="verify-val-input" 
            data-field="${item.key}" 
            value="${val}" 
            placeholder="Manual input"
          >
          <span style="font-size: 0.685rem; color: var(--text-light);">Ref: ${item.normal}</span>
        </div>
      `;
    });

    verificationGrid.innerHTML = html;
    verificationDrawer.style.display = 'block';
  }
});

