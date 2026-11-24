// HealthGuard AI - Main JavaScript & World-Class Animation System

document.addEventListener('DOMContentLoaded', () => {
  // 1. Mobile Navigation Toggle (Public Top Navbar)
  const mobileToggle = document.getElementById('mobileToggle');
  const navLinks = document.getElementById('navLinks');

  if (mobileToggle && navLinks) {
    mobileToggle.addEventListener('click', () => {
      navLinks.classList.toggle('show');
    });
  }

  // 1b. Side Navigation Bar Controller (Desktop Collapse + Mobile Drawer)
  const appSidebar = document.getElementById('appSidebar');
  const sidebarCollapseBtn = document.getElementById('sidebarCollapseBtn');
  const sidebarMobileToggle = document.getElementById('sidebarMobileToggle');
  const sidebarCloseBtn = document.getElementById('sidebarCloseBtn');
  const sidebarOverlay = document.getElementById('sidebarOverlay');

  if (appSidebar) {
    const setMobileDrawer = (isOpen) => {
      appSidebar.classList.toggle('open', isOpen);
      if (sidebarOverlay) sidebarOverlay.classList.toggle('show', isOpen);
      if (sidebarMobileToggle) sidebarMobileToggle.setAttribute('aria-expanded', String(isOpen));
      document.body.style.overflow = isOpen ? 'hidden' : '';
    };

    if (sidebarCollapseBtn) {
      const syncCollapseTitle = () => {
        const collapsed = document.body.classList.contains('sidebar-collapsed');
        sidebarCollapseBtn.setAttribute('title', collapsed ? 'Expand Sidebar' : 'Collapse Sidebar');
        sidebarCollapseBtn.setAttribute('aria-expanded', String(!collapsed));
      };
      syncCollapseTitle();

      sidebarCollapseBtn.addEventListener('click', () => {
        document.body.classList.toggle('sidebar-collapsed');
        const collapsed = document.body.classList.contains('sidebar-collapsed');
        try {
          localStorage.setItem('hg_sidebar_collapsed', String(collapsed));
        } catch (e) {}
        syncCollapseTitle();
        setTimeout(() => window.dispatchEvent(new Event('resize')), 280);
      });
    }

    if (sidebarMobileToggle) {
      sidebarMobileToggle.addEventListener('click', () => {
        const willOpen = !appSidebar.classList.contains('open');
        setMobileDrawer(willOpen);
      });
    }

    if (sidebarCloseBtn) {
      sidebarCloseBtn.addEventListener('click', () => setMobileDrawer(false));
    }

    if (sidebarOverlay) {
      sidebarOverlay.addEventListener('click', () => setMobileDrawer(false));
    }

    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && appSidebar.classList.contains('open')) {
        setMobileDrawer(false);
      }
    });

    window.addEventListener('resize', () => {
      if (window.innerWidth > 992 && appSidebar.classList.contains('open')) {
        setMobileDrawer(false);
      }
    });
  }

  // 2. Auto-dismiss Flash Alerts with Smooth Fade-Out
  const alerts = document.querySelectorAll('.alert');
  alerts.forEach(alert => {
    setTimeout(() => {
      alert.style.transition = 'all 0.5s cubic-bezier(0.4, 0, 0.2, 1)';
      alert.style.opacity = '0';
      alert.style.transform = 'translateY(-10px)';
      setTimeout(() => alert.remove(), 500);
    }, 6000);

    const closeBtn = alert.querySelector('.alert-close');
    if (closeBtn) {
      closeBtn.addEventListener('click', () => {
        alert.style.transition = 'all 0.3s ease';
        alert.style.opacity = '0';
        alert.style.transform = 'scale(0.95)';
        setTimeout(() => alert.remove(), 300);
      });
    }
  });

  // 3. Universal Click Ripple Micro-Animation for all buttons across all pages
  document.addEventListener('click', (e) => {
    const btn = e.target.closest('.btn, button[type="submit"], .btn-action-plan-cta, .action-view-btn');
    if (!btn) return;

    const rect = btn.getBoundingClientRect();
    const ripple = document.createElement('span');
    ripple.className = 'btn-ripple';
    const size = Math.max(rect.width, rect.height) * 2.2;
    ripple.style.width = ripple.style.height = `${size}px`;
    ripple.style.left = `${e.clientX - rect.left - size / 2}px`;
    ripple.style.top = `${e.clientY - rect.top - size / 2}px`;
    btn.appendChild(ripple);

    setTimeout(() => {
      ripple.remove();
    }, 650);
  });

  // 4. World-Class Top Loading Progress Bar Controller
  const topProgressBar = document.getElementById('topProgressBar');
  if (topProgressBar) {
    // Initial page load finish animation
    topProgressBar.style.width = '100%';
    topProgressBar.style.opacity = '1';
    setTimeout(() => {
      topProgressBar.style.opacity = '0';
      setTimeout(() => {
        topProgressBar.style.width = '0%';
      }, 400);
    }, 300);

    // Trigger on internal navigation link clicks
    document.addEventListener('click', (e) => {
      const link = e.target.closest('a[href]');
      if (!link) return;
      const href = link.getAttribute('href');
      
      // Ignore anchors, external links, javascript:, or new tab links
      if (!href || href.startsWith('#') || href.startsWith('javascript:') || link.target === '_blank') return;
      if (href.startsWith('http') && !href.includes(window.location.host)) return;

      topProgressBar.style.opacity = '1';
      topProgressBar.style.width = '70%';
    });

    // Trigger on form submissions
    document.addEventListener('submit', () => {
      topProgressBar.style.opacity = '1';
      topProgressBar.style.width = '85%';
    });
  }

  // 5. Top-Class Biometric Precision Cursor & Ambient Follower (Desktop/Fine Pointers)
  const cursorGlow = document.getElementById('biometricCursorGlow');
  const cursorDot = document.getElementById('biometricCursorDot');

  if (cursorGlow && cursorDot && window.matchMedia('(pointer: fine)').matches) {
    let mouseX = -500;
    let mouseY = -500;
    let glowX = -500;
    let glowY = -500;
    let dotX = -500;
    let dotY = -500;
    let cursorVisible = false;

    window.addEventListener('mousemove', (e) => {
      mouseX = e.clientX;
      mouseY = e.clientY;

      if (!cursorVisible) {
        cursorVisible = true;
        cursorGlow.style.opacity = '1';
        cursorDot.style.opacity = '1';
        glowX = mouseX;
        glowY = mouseY;
        dotX = mouseX;
        dotY = mouseY;
      }
    });

    document.addEventListener('mouseleave', () => {
      cursorVisible = false;
      cursorGlow.style.opacity = '0';
      cursorDot.style.opacity = '0';
    });

    // Smooth Lerp Physics Animation Loop
    function renderCursor() {
      if (cursorVisible) {
        glowX += (mouseX - glowX) * 0.12;
        glowY += (mouseY - glowY) * 0.12;
        dotX += (mouseX - dotX) * 0.45;
        dotY += (mouseY - dotY) * 0.45;

        cursorGlow.style.transform = `translate3d(${glowX}px, ${glowY}px, 0) translate(-50%, -50%)`;
        cursorDot.style.transform = `translate3d(${dotX}px, ${dotY}px, 0) translate(-50%, -50%)`;
      }
      requestAnimationFrame(renderCursor);
    }
    requestAnimationFrame(renderCursor);

    // Interactive Hover States
    const interactiveSelectors = 'a, button, input, select, textarea, .btn, .card, .habit-item, .factor-card';
    document.addEventListener('mouseover', (e) => {
      if (e.target.closest(interactiveSelectors)) {
        document.body.classList.add('cursor-hover');
      }
    });

    document.addEventListener('mouseout', (e) => {
      if (e.target.closest(interactiveSelectors)) {
        document.body.classList.remove('cursor-hover');
      }
    });

    document.addEventListener('mousedown', () => {
      document.body.classList.add('cursor-active');
    });

    document.addEventListener('mouseup', () => {
      document.body.classList.remove('cursor-active');
    });
  }

  // 6. Interactive 3D Perspective Card Tilt & Spotlight Coordinates
  const tiltCards = document.querySelectorAll('.card, .kpi-card, .admin-kpi-card, .feature-box, .factor-card, .stat-item, .hero-stat-card');
  tiltCards.forEach(card => {
    card.addEventListener('mousemove', (e) => {
      const rect = card.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;

      // Spotlight illumination CSS coordinates
      card.style.setProperty('--mouse-x', `${x}px`);
      card.style.setProperty('--mouse-y', `${y}px`);

      // Gentle 3D perspective tilt
      const centerX = rect.width / 2;
      const centerY = rect.height / 2;
      const rotateX = ((y - centerY) / centerY) * -6; // max 6 deg
      const rotateY = ((x - centerX) / centerX) * 6;  // max 6 deg

      card.style.transform = `perspective(1000px) rotateX(${rotateX.toFixed(2)}deg) rotateY(${rotateY.toFixed(2)}deg) translateY(-3px)`;
    });

    card.addEventListener('mouseleave', () => {
      card.style.transform = 'perspective(1000px) rotateX(0deg) rotateY(0deg) translateY(0)';
    });
  });

  // 7. Button Magnetic Micro-Pull Effect
  const magneticButtons = document.querySelectorAll('.btn, .btn-action-plan-cta, .action-view-btn, .nav-logout-btn');
  magneticButtons.forEach(btn => {
    btn.addEventListener('mousemove', (e) => {
      const rect = btn.getBoundingClientRect();
      const x = e.clientX - (rect.left + rect.width / 2);
      const y = e.clientY - (rect.top + rect.height / 2);
      btn.style.transform = `translate3d(${x * 0.15}px, ${y * 0.15}px, 0)`;
    });

    btn.addEventListener('mouseleave', () => {
      btn.style.transform = '';
    });
  });

  // 8. Live Animated Telemetry Number Counters (Count-up)
  function animateNumberCounter(el) {
    const originalText = el.textContent.trim();
    // Match numbers with optional decimal and commas
    const match = originalText.match(/^([^\d]*)([\d,]+(?:\.\d+)?)(.*)$/);
    if (!match) return;

    const prefix = match[1] || '';
    const rawNumberStr = match[2].replace(/,/g, '');
    const suffix = match[3] || '';
    const targetNum = parseFloat(rawNumberStr);

    if (isNaN(targetNum)) return;

    const isDecimal = rawNumberStr.includes('.');
    const decimalPlaces = isDecimal ? rawNumberStr.split('.')[1].length : 0;
    const duration = 1400; // ms
    const startTime = performance.now();

    el.classList.add('telemetry-counter-animated', 'telemetry-counting');

    function updateCounter(currentTime) {
      const elapsed = currentTime - startTime;
      const progress = Math.min(elapsed / duration, 1);
      // Ease out cubic
      const easedProgress = 1 - Math.pow(1 - progress, 3);
      const currentVal = targetNum * easedProgress;

      let formattedVal = isDecimal ? currentVal.toFixed(decimalPlaces) : Math.round(currentVal).toString();
      
      // Preserve commas if original had them
      if (rawNumberStr.length > 3 && !isDecimal) {
        formattedVal = parseInt(formattedVal, 10).toLocaleString();
      }

      el.textContent = `${prefix}${formattedVal}${suffix}`;

      if (progress < 1) {
        requestAnimationFrame(updateCounter);
      } else {
        el.textContent = originalText;
        el.classList.remove('telemetry-counting');
      }
    }

    requestAnimationFrame(updateCounter);
  }

  // 9. Scroll-Driven Reveal Micro-Animations & Telemetry Trigger (Intersection Observer)
  if ('IntersectionObserver' in window) {
    // Reveal Cards
    const revealElements = document.querySelectorAll('.card, .admin-kpi-card, .kpi-card, .feature-box, .stat-item');
    const revealObserver = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add('revealed-in-view');
          revealObserver.unobserve(entry.target);
        }
      });
    }, { threshold: 0.08 });

    revealElements.forEach(el => {
      el.classList.add('reveal-on-scroll');
      revealObserver.observe(el);
    });

    // Telemetry Counter Observer
    const counterElements = document.querySelectorAll('.admin-kpi-val, .kpi-val, .stat-number, .score-val, .metric-value, .hero-stat-value, .risk-score-badge, .kpi-stat-value');
    const counterObserver = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          animateNumberCounter(entry.target);
          counterObserver.unobserve(entry.target);
        }
      });
    }, { threshold: 0.2 });

    counterElements.forEach(el => counterObserver.observe(el));
  }
});

// ==============================================================================
// 🌐 7. Tamil + English Health Assistant Engine
// ==============================================================================
const HEALTH_KNOWLEDGE = {
  bmi: {
    title: "What is BMI? • BMI என்றால் என்ன?",
    english: `
      <strong>Body Mass Index (BMI)</strong> is an international screening metric evaluating weight relative to height (kg/m²).<br><br>
      • <strong>Normal Weight:</strong> 18.5 – 24.9 kg/m²<br>
      • <strong>Overweight:</strong> 25.0 – 29.9 kg/m²<br>
      • <strong>Obese Category:</strong> 30.0 kg/m² or higher<br><br>
      <em>Why it matters for Diabetes:</em> Visceral abdominal fat cells release fatty acids and inflammatory cytokines that impair insulin signaling (Insulin Resistance). Losing just 5–7% of total body weight can restore glucose uptake.
    `,
    tamil: `
      <strong>BMI (உடல் நிறை குறியீட்டெண்)</strong> என்பது ஒருவரது உயரத்திற்கு ஏற்ப அவரது உடல் எடை சரியாக உள்ளதா என்பதை அளவிடும் சர்வதேச மருத்துவ முறையாகும் (kg/m²).<br><br>
      • <strong>சீரான எடை:</strong> 18.5 – 24.9 kg/m²<br>
      • <strong>அதிக எடை:</strong> 25.0 – 29.9 kg/m²<br>
      • <strong>உடல் பருமன்:</strong> 30.0 kg/m² அல்லது அதற்கு மேல்<br><br>
      <em>நீரிழிவுக்கு இது ஏன் முக்கியம்:</em> அதிகப்படியான உடல் கொழுப்பு (குறிப்பாக வயிற்றுப்பகுதி தொப்பை) இன்சுலின் எதிர்ப்பை (Insulin Resistance) உருவாக்குகிறது. இதனால் கணையத்தால் சுரக்கப்படும் இன்சுலினை செல்கள் ஏற்க முடியாமல் ரத்தத்தில் சர்க்கரை கூடுகிறது. உடல் எடையில் 5-7% குறைப்பது நீரிழிவு அபாயத்தை பாதியாக குறைக்கும்.
    `
  },
  glucose: {
    title: "What does glucose mean? • குளுக்கோஸ் என்றால் என்ன?",
    english: `
      <strong>Blood Glucose</strong> is the fundamental sugar circulating in your bloodstream, supplying cellular fuel to your brain, muscles, and tissues.<br><br>
      • <strong>Normal Fasting Glucose:</strong> 70 – 99 mg/dL<br>
      • <strong>Prediabetes (Impaired Glucose):</strong> 100 – 125 mg/dL<br>
      • <strong>Diabetes Diagnostic Range:</strong> ≥ 126 mg/dL (confirmed on 2 clinical tests)<br><br>
      <em>Clinical Context:</em> If fasting glucose is above 100 mg/dL, early intervention with low-glycemic nutrition, brisk walking, and weight control can effectively reverse readings back to normal.
    `,
    tamil: `
      <strong>குளுக்கோஸ் (Glucose)</strong> என்பது நமது உடலின் முதன்மை ஆற்றல் மூலமான இரத்த சர்க்கரை ஆகும். நாம் உண்ணும் கார்போஹைட்ரேட் உணவுகள் செரிக்கப்பட்டு குளுக்கோஸாக ரத்தத்தில் கலக்கிறது.<br><br>
      • <strong>இயல்பான அளவு (வெறும் வயிற்றில்):</strong> 70 – 99 mg/dL<br>
      • <strong>ஆரம்ப நிலை (Prediabetes):</strong> 100 – 125 mg/dL<br>
      • <strong>நீரிழிவு நிலை (Diabetes):</strong> 126 mg/dL அல்லது அதற்கு மேல் (மருத்துவ உறுதிப்படுத்தல் தேவை)<br><br>
      <em>மருத்துவ விளக்கம்:</em> உங்கள் வெறும் வயிற்று சர்க்கரை 100 mg/dL-க்கு மேல் இருந்தால், இப்போதே முறையான உணவுக்கட்டுப்பாடு மற்றும் நடைப்பயிற்சியை தொடங்கினால் சர்க்கரை அளவை மீண்டும் இயல்பு நிலைக்கு கொண்டு வர முடியும்.
    `
  },
  prediction: {
    title: "What does my prediction result mean? • எனது கணிப்பு முடிவு என்ன குறிக்கிறது?",
    english: `
      Your screening prediction is an <strong>algorithmic statistical likelihood (0% to 100%)</strong> calculated using your biological markers (glucose, BMI, age, blood pressure, etc.).<br><br>
      • <strong>It does NOT mean you have diabetes!</strong> This is an early screening assessment, not a formal medical diagnosis.<br>
      • <strong>High Risk (≥65%):</strong> Identifies elevated biomarkers above reference limits. You should schedule an appointment with your physician for confirmatory lab tests (HbA1c & FPG).<br>
      • <strong>Moderate Risk (35–65%):</strong> Reflects borderline biomarkers that respond exceptionally well to lifestyle improvements.<br>
      • <strong>Low Risk (<35%):</strong> Reflects optimal metabolic health. Continue annual preventative health checks.
    `,
    tamil: `
      உங்கள் கணிப்பு முடிவு என்பது உங்கள் இரத்த சர்க்கரை, BMI, வயது மற்றும் இரத்த அழுத்தம் போன்ற குறிப்பான்களை ஆய்வு செய்து உருவாக்கப்பட்ட <strong>புள்ளிவிவர அபாய மதிப்பீடு (Statistical Screening)</strong> மட்டுமே.<br><br>
      • <strong>உங்களுக்கு நீரிழிவு நோய் உள்ளது என்று இது பொருள்படாது!</strong> இது ஒரு ஆரம்ப கட்ட எச்சரிக்கை வழிகாட்டி மட்டுமே, இறுதி மருத்துவ சான்றல்ல.<br>
      • <strong>அதிக அபாயம் (High Risk):</strong> உடலில் சில முக்கிய குறிப்பான்கள் இயல்பான அளவை விட அதிகமாக உள்ளன. உடனே மருத்துவரை அணுகி HbA1c ரத்த பரிசோதனை செய்து ஆலோசனை பெற வேண்டும்.<br>
      • <strong>மிதமான அபாயம் (Moderate Risk):</strong> சில குறிப்பான்கள் எல்லைக்கோட்டில் உள்ளன. உணவுமுறை மற்றும் உடற்பயிற்சி மூலம் இதை எளிதில் மாற்றலாம்.<br>
      • <strong>குறைந்த அபாயம் (Low Risk):</strong> உங்கள் தற்போதைய உடலியல் குறியீடுகள் இயல்பாக உள்ளன. நல்ல பழக்கவழக்கங்களைத் தொடரவும்.
    `
  },
  prevention: {
    title: "How to lower diabetes risk? • நீரிழிவு அபாயத்தை எப்படிக் குறைப்பது?",
    english: `
      Major clinical trials (such as the Diabetes Prevention Program) show lifestyle habits reduce Type 2 Diabetes onset by up to <strong>58%</strong>:<br><br>
      1. <strong>Targeted Weight Reduction:</strong> Losing 5% to 7% of total weight restores cellular insulin sensitivity.<br>
      2. <strong>Brisk Physical Activity:</strong> 150 minutes of moderate exercise weekly (e.g. 30 mins walking 5 days/week).<br>
      3. <strong>Low Glycemic Nutrition:</strong> Emphasize leafy greens, legumes, millets, whole grains; eliminate sugary sodas and refined grains.<br>
      4. <strong>Restorative Sleep:</strong> Aim for 7–8 hours of uninterrupted sleep to balance cortisol and insulin levels.
    `,
    tamil: `
      உலகளாவிய மருத்துவ ஆராய்ச்சிகள் தகுந்த வாழ்க்கை முறை மாற்றங்கள் மூலம் நீரிழிவு நோயை <strong>58% வரை தடுக்க முடியும்</strong> என்று நிரூபித்துள்ளன:<br><br>
      1. <strong>எடை குறைப்பு:</strong> உங்கள் உடல் எடையில் 5% முதல் 7% வரை குறைப்பது இன்சுலின் சுரப்பை மீண்டும் சீராக்கும்.<br>
      2. <strong>தினசரி உடற்பயிற்சி:</strong> வாரத்திற்கு 150 நிமிடங்கள் (தினமும் 30 நிமிடம் வீதம் 5 நாட்கள்) வேகமான நடைப்பயிற்சி.<br>
      3. <strong>உணவு முறை:</strong> காய்கறிகள், கீரைகள், பாசிப்பயறு, சிறுதானியங்களை அதிகம் சேர்க்கவும்; இனிப்பு பானங்கள், மைதா மற்றும் துரித உணவுகளைத் தவிர்க்கவும்.<br>
      4. <strong>நல்ல தூக்கம்:</strong> தினமும் 7-8 மணிநேர ஆழ்ந்த தூக்கம் உடலின் மெட்டபாலிசத்தை சீராக வைக்கும்.
    `
  },
  insulin: {
    title: "What is Insulin? • இன்சுலின் என்றால் என்ன?",
    english: `
      <strong>Insulin</strong> is a hormone produced by the beta cells of your pancreas. It functions like a biological key, allowing circulating blood glucose to enter cells for energy production.<br><br>
      In Type 2 Diabetes or Prediabetes, cells become resistant to insulin ("Insulin Resistance"). The pancreas initially pumps extra insulin to compensate until beta cells tire, causing blood glucose to climb.
    `,
    tamil: `
      <strong>இன்சுலின் (Insulin)</strong> என்பது கணையத்தில் உள்ள பீட்டா செல்களால் உற்பத்தி செய்யப்படும் ஒரு முக்கிய ஹார்மோன் ஆகும். இது ஒரு சாவி போல செயல்பட்டு இரத்தத்தில் உள்ள சர்க்கரையை நமது செல்களுக்குள் அனுப்பி ஆற்றலாக மாற்றுகிறது.<br><br>
      செல்கள் இன்சுலினின் பேச்சை கேட்காமல் மறுக்கும் நிலையை 'இன்சுலின் எதிர்ப்பு' (Insulin Resistance) என்கிறோம். இதனால் கணையம் அதிகமாக உழைத்து சோர்வடையும் போது ரத்த சர்க்கரை அளவு உயர்கிறது.
    `
  }
};

let currentAssistantLang = 'bilingual';

window.openHealthAssistant = function() {
  const modal = document.getElementById('healthAssistantModal');
  if (modal) {
    modal.style.display = 'flex';
    const input = document.getElementById('assistantQueryInput');
    if (input) setTimeout(() => input.focus(), 100);
  }
};

window.closeHealthAssistant = function() {
  const modal = document.getElementById('healthAssistantModal');
  if (modal) modal.style.display = 'none';
};

window.setAssistantLang = function(lang) {
  currentAssistantLang = lang;
  const buttons = document.querySelectorAll('.assistant-lang-btn');
  buttons.forEach(btn => {
    btn.classList.toggle('active', btn.getAttribute('data-lang') === lang);
  });

  // Re-render visibility for all rendered bilingual boxes
  applyLanguageVisibility();
};

function applyLanguageVisibility() {
  const englishBlocks = document.querySelectorAll('.english-block');
  const tamilBlocks = document.querySelectorAll('.tamil-block');

  if (currentAssistantLang === 'bilingual') {
    englishBlocks.forEach(b => b.style.display = 'block');
    tamilBlocks.forEach(b => b.style.display = 'block');
  } else if (currentAssistantLang === 'en') {
    englishBlocks.forEach(b => b.style.display = 'block');
    tamilBlocks.forEach(b => b.style.display = 'none');
  } else if (currentAssistantLang === 'ta') {
    englishBlocks.forEach(b => b.style.display = 'none');
    tamilBlocks.forEach(b => b.style.display = 'block');
  }
}

window.askAssistant = function(topicKey) {
  const item = HEALTH_KNOWLEDGE[topicKey];
  if (!item) return;

  const contentBody = document.getElementById('assistantContentBody');
  if (!contentBody) return;

  const cardHtml = `
    <div class="assistant-answer-card">
      <div class="assistant-answer-title">
        <i class="fa-solid fa-circle-check" style="color: var(--primary);"></i>
        <span>${item.title}</span>
      </div>
      <div class="bilingual-box">
        <div class="lang-block english-block">
          <span class="lang-tag-pill">English</span>
          <div>${item.english}</div>
        </div>
        <div class="lang-block tamil-block">
          <span class="lang-tag-pill">தமிழ்</span>
          <div>${item.tamil}</div>
        </div>
      </div>
    </div>
  `;

  contentBody.innerHTML = cardHtml + contentBody.innerHTML;
  applyLanguageVisibility();
  contentBody.scrollTop = 0;
};

window.handleAssistantKey = function(e) {
  if (e.key === 'Enter') {
    handleAssistantSubmit();
  }
};

window.handleAssistantSubmit = function() {
  const input = document.getElementById('assistantQueryInput');
  if (!input) return;
  const query = input.value.trim().toLowerCase();
  if (!query) return;

  input.value = '';

  // Intelligent Keyword Matching
  let matchedKey = null;
  if (query.includes('bmi') || query.includes('weight') || query.includes('height') || query.includes('உடல்') || query.includes('எடை')) {
    matchedKey = 'bmi';
  } else if (query.includes('glucose') || query.includes('sugar') || query.includes('fasting') || query.includes('குளுக்கோஸ்') || query.includes('சர்க்கரை')) {
    matchedKey = 'glucose';
  } else if (query.includes('predict') || query.includes('result') || query.includes('meaning') || query.includes('கணிப்பு') || query.includes('முடிவு')) {
    matchedKey = 'prediction';
  } else if (query.includes('prevent') || query.includes('lower') || query.includes('diet') || query.includes('exercise') || query.includes('தடுக்க') || query.includes('குறைக்க')) {
    matchedKey = 'prevention';
  } else if (query.includes('insulin') || query.includes('இன்சுலின்')) {
    matchedKey = 'insulin';
  } else {
    // Default to prediction & glucose advice
    matchedKey = 'prediction';
  }

  askAssistant(matchedKey);
};


