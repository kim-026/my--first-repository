/**
 * AI Resume Screening & Candidate Assessment System
 * Complete Frontend Controller & State Store
 */

const API_BASE = ""; // Relative to host (FastAPI serves both API and static files)

// Global Application State
const state = {
  currentPage: 1,
  companies: [],
  jobs: [],
  activeJobId: null,
  activeCandidateId: null,
  activeUploadId: null,
  activeMatchingId: null,
  extractedData: null,
  matchingData: null,
  mockQuestions: [],
  evaluationData: null,
  profileData: null,
  selectedFile: null,
  compareCandidatesList: []
};

// ==========================================================================
// INITIALIZATION
// ==========================================================================

document.addEventListener("DOMContentLoaded", async () => {
  setupDropzone();
  await loadCompanies();
  await loadJobs();
  await loadDashboardStats();
  await loadDashboardCandidates();

  // Refresh icons
  if (window.lucide) {
    lucide.createIcons();
  }
});

// Toast notification helper
function showToast(message, type = "info") {
  const container = document.getElementById("toast-container");
  if (!container) return;

  const toast = document.createElement("div");
  toast.className = `toast ${type}`;
  toast.innerHTML = `<span>${message}</span>`;
  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = "0";
    setTimeout(() => toast.remove(), 300);
  }, 3500);
}

// Page Navigation & Stepper Controller
function switchPage(pageNumber) {
  state.currentPage = pageNumber;

  // Toggle pages
  document.querySelectorAll(".workflow-page").forEach(page => {
    page.classList.remove("active");
  });
  const targetPage = document.getElementById(`page-11`);
  const activeSection = document.getElementById(`page-${pageNumber}`);
  if (activeSection) {
    activeSection.classList.add("active");
  }

  // Update Stepper buttons
  document.querySelectorAll(".step-btn").forEach(btn => {
    const pageVal = parseInt(btn.getAttribute("data-page"), 10);
    btn.classList.remove("active");
    if (pageVal === pageNumber) {
      btn.classList.add("active");
    } else if (pageVal < pageNumber) {
      btn.classList.add("completed");
    }
  });

  // Re-render icons for dynamic content
  if (window.lucide) {
    lucide.createIcons();
  }

  window.scrollTo({ top: 0, behavior: "smooth" });
}

// ==========================================================================
// PAGE 1: COMPANIES & JOB REQUIREMENTS
// ==========================================================================

async function loadCompanies() {
  try {
    const res = await fetch(`${API_BASE}/api/companies`);
    const companies = await res.json();
    state.companies = companies;

    const select = document.getElementById("company-select");
    select.innerHTML = '<option value="">-- Choose Existing Company --</option>';
    companies.forEach(c => {
      const opt = document.createElement("option");
      opt.value = c.id;
      opt.textContent = `${c.company_name} (${c.industry || "General"})`;
      select.appendChild(opt);
    });

    if (companies.length > 0) {
      select.value = companies[0].id;
    }
  } catch (err) {
    console.error("Error loading companies:", err);
  }
}

async function loadJobs() {
  try {
    const res = await fetch(`${API_BASE}/api/jobs`);
    const jobs = await res.json();
    state.jobs = jobs;

    const shelf = document.getElementById("jobs-list-shelf");
    const countBadge = document.getElementById("available-jobs-count");
    const filterSelect = document.getElementById("filter-job-select");

    if (countBadge) countBadge.textContent = `${jobs.length} Positions`;

    if (filterSelect) {
      filterSelect.innerHTML = '<option value="">All Job Roles</option>';
      jobs.forEach(j => {
        const opt = document.createElement("option");
        opt.value = j.id;
        opt.textContent = `${j.job_title} - ${j.company_name}`;
        filterSelect.appendChild(opt);
      });
    }

    if (shelf) {
      shelf.innerHTML = "";
      if (jobs.length === 0) {
        shelf.innerHTML = `<p class="text-muted text-sm">No positions configured yet.</p>`;
        return;
      }

      jobs.forEach((j, idx) => {
        const isSelected = state.activeJobId ? state.activeJobId === j.id : idx === 0;
        if (isSelected && !state.activeJobId) {
          state.activeJobId = j.id;
          updateActiveJobIndicator(j.job_title, j.company_name);
        }

        const div = document.createElement("div");
        div.className = `job-card-item ${isSelected ? "selected" : ""}`;
        div.style.cssText = `
          border: 1.5px solid ${isSelected ? "var(--primary)" : "var(--border-color)"};
          background: ${isSelected ? "var(--primary-light)" : "#ffffff"};
          border-radius: var(--radius-md);
          padding: 14px 18px;
          margin-bottom: 12px;
          cursor: pointer;
          transition: all 0.2s ease;
        `;
        div.onclick = () => selectActiveJob(j.id, j.job_title, j.company_name);

        const reqSkills = Array.isArray(j.required_skills) ? j.required_skills : [];
        div.innerHTML = `
          <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:6px;">
            <h4 style="font-size:0.95rem; font-weight:700; color:var(--text-main);">${j.job_title}</h4>
            <span class="badge ${isSelected ? "badge-blue" : "badge-purple"}">${isSelected ? "Active Target" : "Select"}</span>
          </div>
          <div style="font-size:0.8rem; color:var(--text-muted); margin-bottom:8px;">${j.company_name} • ${j.experience || "2+ years"}</div>
          <div style="display:flex; flex-wrap:wrap; gap:4px;">
            ${reqSkills.slice(0, 4).map(s => `<span class="tag-badge" style="font-size:0.75rem; padding:2px 8px;">${s}</span>`).join("")}
            ${reqSkills.length > 4 ? `<span class="tag-badge" style="font-size:0.75rem; padding:2px 8px;">+${reqSkills.length - 4} more</span>` : ""}
          </div>
        `;
        shelf.appendChild(div);
      });
    }
  } catch (err) {
    console.error("Error loading jobs:", err);
  }
}

function selectActiveJob(jobId, jobTitle, companyName) {
  state.activeJobId = jobId;
  updateActiveJobIndicator(jobTitle, companyName);
  loadJobs(); // refresh selection visual
  showToast(`Active Target Role set to: ${jobTitle}`, "success");
}

function updateActiveJobIndicator(jobTitle, companyName) {
  const lbl = document.getElementById("active-job-label");
  if (lbl) {
    lbl.textContent = `Target Role: ${jobTitle} (${companyName})`;
  }
}

// Tag Management for Job Requirements Form
const requiredSkillsList = ["Python", "SQL", "Machine Learning", "Docker"];
const optionalSkillsList = ["AWS", "Kubernetes", "FastAPI"];

function renderTags(containerId, list, type) {
  const container = document.getElementById(containerId);
  if (!container) return;
  container.innerHTML = "";
  list.forEach((item, index) => {
    const span = document.createElement("span");
    span.className = `tag-badge ${type === "optional" ? "tag-optional" : ""}`;
    span.innerHTML = `
      ${item}
      <button type="button" class="tag-remove" onclick="removeTag('${containerId}', ${index}, '${type}')">&times;</button>
    `;
    container.appendChild(span);
  });
}

function addSkillTag(tagText, targetType) {
  const trimmed = tagText.trim();
  if (!trimmed) return;
  if (targetType === "required-skills") {
    if (!requiredSkillsList.includes(trimmed)) {
      requiredSkillsList.push(trimmed);
      renderTags("required-skills-tags", requiredSkillsList, "required");
    }
  } else {
    if (!optionalSkillsList.includes(trimmed)) {
      optionalSkillsList.push(trimmed);
      renderTags("optional-skills-tags", optionalSkillsList, "optional");
    }
  }
}

function removeTag(containerId, index, type) {
  if (type === "required") {
    requiredSkillsList.splice(index, 1);
    renderTags("required-skills-tags", requiredSkillsList, "required");
  } else {
    optionalSkillsList.splice(index, 1);
    renderTags("optional-skills-tags", optionalSkillsList, "optional");
  }
}

function handleTagKeyDown(e, targetType) {
  if (e.key === "Enter" || e.key === ",") {
    e.preventDefault();
    const input = e.target;
    addSkillTag(input.value, targetType);
    input.value = "";
  }
}

// Initial tags render
renderTags("required-skills-tags", requiredSkillsList, "required");
renderTags("optional-skills-tags", optionalSkillsList, "optional");

async function handleSaveJob(e) {
  e.preventDefault();
  const companyId = parseInt(document.getElementById("company-select").value, 10);
  const jobTitle = document.getElementById("job-title-input").value.trim();
  const experience = document.getElementById("job-experience-input").value.trim();
  const education = document.getElementById("job-education-input").value.trim();
  const description = document.getElementById("job-description-input").value.trim();

  if (!companyId) {
    showToast("Please choose or create a company first.", "error");
    return;
  }
  if (!jobTitle) {
    showToast("Please enter a job title.", "error");
    return;
  }
  if (requiredSkillsList.length === 0) {
    showToast("Please add at least one required skill.", "error");
    return;
  }

  try {
    const res = await fetch(`${API_BASE}/api/jobs`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        company_id: companyId,
        job_title: jobTitle,
        required_skills: requiredSkillsList,
        optional_skills: optionalSkillsList,
        experience,
        education,
        job_description: description
      })
    });
    const result = await res.json();
    showToast(`Job requirement '${jobTitle}' created successfully!`, "success");
    state.activeJobId = result.id;
    await loadJobs();
  } catch (err) {
    console.error("Save job error:", err);
    showToast("Failed to save job requirements.", "error");
  }
}

function loadSampleJobPreset(index) {
  if (index === 0) {
    // Senior ML Engineer
    document.getElementById("job-title-input").value = "Senior Machine Learning Engineer";
    document.getElementById("job-experience-input").value = "3+ years";
    document.getElementById("job-education-input").value = "Master's or Bachelor's in Computer Science";
    document.getElementById("job-description-input").value = "Lead the architecture and deployment of enterprise machine learning pipelines, deep learning models, and real-time inference microservices.";
    requiredSkillsList.length = 0;
    requiredSkillsList.push("Python", "SQL", "Machine Learning", "Deep Learning", "PyTorch", "Docker");
    renderTags("required-skills-tags", requiredSkillsList, "required");
    optionalSkillsList.length = 0;
    optionalSkillsList.push("AWS", "Kubernetes", "FastAPI", "NLP");
    renderTags("optional-skills-tags", optionalSkillsList, "optional");
  } else {
    // Full-Stack Engineer
    document.getElementById("job-title-input").value = "Full-Stack Software Engineer (React / Python)";
    document.getElementById("job-experience-input").value = "2+ years";
    document.getElementById("job-education-input").value = "Bachelor's in Computer Science or STEM";
    document.getElementById("job-description-input").value = "Build high-reliability financial portals and APIs with rich interactive React user interfaces and Python backend services.";
    requiredSkillsList.length = 0;
    requiredSkillsList.push("Python", "React", "JavaScript", "SQL", "PostgreSQL", "REST API");
    renderTags("required-skills-tags", requiredSkillsList, "required");
    optionalSkillsList.length = 0;
    optionalSkillsList.push("Docker", "TypeScript", "FastAPI", "AWS");
    renderTags("optional-skills-tags", optionalSkillsList, "optional");
  }
  showToast("Preset loaded into form. Click 'Save & Select' to register.", "info");
}

function toggleNewCompanyModal() {
  const modal = document.getElementById("modal-new-company");
  modal.classList.toggle("active");
}

async function handleCreateCompany(e) {
  e.preventDefault();
  const name = document.getElementById("new-company-name").value.trim();
  const industry = document.getElementById("new-company-industry").value.trim();
  const website = document.getElementById("new-company-website").value.trim();
  const desc = document.getElementById("new-company-desc").value.trim();

  if (!name) return;

  try {
    const res = await fetch(`${API_BASE}/api/companies`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ company_name: name, industry, website, description: desc })
    });
    const result = await res.json();
    showToast(`Company '${name}' registered!`, "success");
    toggleNewCompanyModal();
    await loadCompanies();
    document.getElementById("company-select").value = result.id;
  } catch (err) {
    showToast("Failed to create company", "error");
  }
}

// ==========================================================================
// PAGE 2: RESUME UPLOAD & PARSING
// ==========================================================================

function setupDropzone() {
  const dropzone = document.getElementById("resume-dropzone");
  if (!dropzone) return;

  ["dragenter", "dragover"].forEach(name => {
    dropzone.addEventListener(name, (e) => {
      e.preventDefault();
      e.stopPropagation();
      dropzone.classList.add("dragover");
    });
  });

  ["dragleave", "drop"].forEach(name => {
    dropzone.addEventListener(name, (e) => {
      e.preventDefault();
      e.stopPropagation();
      dropzone.classList.remove("dragover");
    });
  });

  dropzone.addEventListener("drop", (e) => {
    const files = e.dataTransfer.files;
    if (files.length > 0) {
      selectFile(files[0]);
    }
  });
}

function triggerFileInput() {
  document.getElementById("resume-file-input").click();
}

function handleFileSelected(e) {
  if (e.target.files.length > 0) {
    selectFile(e.target.files[0]);
  }
}

function selectFile(file) {
  state.selectedFile = file;
  const disp = document.getElementById("selected-file-display");
  const nameLbl = document.getElementById("selected-file-name");
  const sizeLbl = document.getElementById("selected-file-size");

  disp.style.display = "inline-flex";
  nameLbl.textContent = file.name;
  sizeLbl.textContent = `(${(file.size / 1024).toFixed(1)} KB)`;
}

function clearSelectedFile(e) {
  e.stopPropagation();
  state.selectedFile = null;
  document.getElementById("resume-file-input").value = "";
  document.getElementById("selected-file-display").style.display = "none";
}

async function handleResumeUploadSubmit(e) {
  e.preventDefault();
  if (!state.selectedFile) {
    showToast("Please select or drop a resume document first.", "error");
    return;
  }

  const btn = document.getElementById("btn-submit-upload");
  btn.disabled = true;
  btn.innerHTML = `<i data-lucide="loader" class="spin"></i> Extracting Resume Data...`;
  if (window.lucide) lucide.createIcons();

  const nameVal = document.getElementById("candidate-name-input").value.trim();
  const emailVal = document.getElementById("candidate-email-input").value.trim();
  const phoneVal = document.getElementById("candidate-phone-input").value.trim();

  const formData = new FormData();
  formData.append("file", state.selectedFile);
  formData.append("candidate_name", nameVal);
  formData.append("candidate_email", emailVal);
  formData.append("candidate_phone", phoneVal);

  try {
    const res = await fetch(`${API_BASE}/api/upload-resume`, {
      method: "POST",
      body: formData
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Upload error");
    }

    const data = await res.json();
    state.activeCandidateId = data.candidate_id;
    state.activeUploadId = data.upload_id;
    state.extractedData = data.extracted_data;

    showToast(`Resume uploaded & parsed successfully for ${data.candidate_name}!`, "success");
    renderExtractionPage(data);
    switchPage(3);
  } catch (err) {
    console.error("Upload error:", err);
    showToast(err.message, "error");
  } finally {
    btn.disabled = false;
    btn.innerHTML = `<i data-lucide="arrow-right"></i> Upload & Extract Resume`;
    if (window.lucide) lucide.createIcons();
  }
}

async function loadSampleResumePreset(filename) {
  try {
    showToast(`Loading pre-configured demo resume: ${filename}...`, "info");
    const res = await fetch(`${API_BASE}/api/sample-resumes/load/${filename}`, {
      method: "POST"
    });
    if (!res.ok) throw new Error("Failed to load sample resume");
    const data = await res.json();

    state.activeCandidateId = data.candidate_id;
    state.activeUploadId = data.upload_id;
    state.extractedData = data.extracted_data;

    showToast(`Demo resume loaded for ${data.candidate_name}!`, "success");
    renderExtractionPage({
      candidate_id: data.candidate_id,
      upload_id: data.upload_id,
      candidate_name: data.candidate_name,
      candidate_email: data.extracted_data.personal_details.email,
      filename: filename,
      extracted_data: data.extracted_data,
      raw_text_preview: "Loaded from verified system sample dataset."
    });
    switchPage(3);
  } catch (err) {
    console.error("Load sample resume error:", err);
    showToast("Error loading demo resume", "error");
  }
}

// ==========================================================================
// PAGE 3: RESUME EXTRACTION DISPLAY
// ==========================================================================

function renderExtractionPage(data) {
  const container = document.getElementById("extraction-content-area");
  if (!container) return;

  const ext = data.extracted_data;
  const p = ext.personal_details || {};
  const techSkills = ext.technical_skills || [];
  const softSkills = ext.soft_skills || [];
  const educations = ext.education || [];
  const experiences = ext.experience || [];
  const certs = ext.certifications || [];

  container.innerHTML = `
    <!-- Top Hero Banner -->
    <div class="candidate-overview-card">
      <div class="candidate-avatar-group">
        <div class="candidate-avatar">${p.name ? p.name.charAt(0).toUpperCase() : "C"}</div>
        <div class="candidate-meta">
          <h3>${p.name || "Candidate"}</h3>
          <div class="candidate-meta-contact">
            <span><i data-lucide="mail"></i> ${p.email || "email@example.com"}</span>
            <span><i data-lucide="phone"></i> ${p.phone || "N/A"}</span>
            <span><i data-lucide="map-pin"></i> ${p.location || "USA"}</span>
            ${p.linkedin ? `<span><i data-lucide="linkedin"></i> ${p.linkedin}</span>` : ""}
            ${p.github ? `<span><i data-lucide="github"></i> ${p.github}</span>` : ""}
          </div>
        </div>
      </div>
      <div style="text-align:right;">
        <span class="badge badge-green" style="font-size:0.85rem; padding:6px 14px;">Parsed & Verified</span>
        <div style="font-size:0.8rem; color:#c7d2fe; margin-top:6px;">Total Exp: ${ext.total_experience_years || 2.0} years</div>
      </div>
    </div>

    <!-- Left Column: Skills & Certifications -->
    <div>
      <div class="card shadow-sm mb-4">
        <div class="card-header">
          <h3><i data-lucide="code-2"></i> Technical Skills Identified (${techSkills.length})</h3>
          <span class="badge badge-blue">AI Extracted</span>
        </div>
        <div class="card-body">
          <div class="skills-cloud">
            ${techSkills.map(s => `
              <span class="skill-pill technical" title="${s.category || 'Skill'}">
                <i data-lucide="cpu"></i> ${s.skill_name}
              </span>
            `).join("")}
          </div>
        </div>
      </div>

      <div class="card shadow-sm mb-4">
        <div class="card-header">
          <h3><i data-lucide="users"></i> Soft Skills & Competencies (${softSkills.length})</h3>
          <span class="badge badge-purple">AI Extracted</span>
        </div>
        <div class="card-body">
          <div class="skills-cloud">
            ${softSkills.map(s => `
              <span class="skill-pill soft">
                <i data-lucide="check"></i> ${s.skill_name}
              </span>
            `).join("")}
          </div>
        </div>
      </div>

      ${certs.length > 0 ? `
      <div class="card shadow-sm">
        <div class="card-header">
          <h3><i data-lucide="award"></i> Certifications Verified (${certs.length})</h3>
        </div>
        <div class="card-body">
          <ul style="list-style:none; padding:0;">
            ${certs.map(c => `
              <li style="display:flex; align-items:center; gap:10px; margin-bottom:10px;">
                <i data-lucide="badge-check" style="color:var(--success);"></i>
                <div>
                  <strong>${c.cert_name}</strong>
                  <div class="text-muted text-xs">${c.issuer || "Accredited"} • ${c.year || "2023"}</div>
                </div>
              </li>
            `).join("")}
          </ul>
        </div>
      </div>
      ` : ""}
    </div>

    <!-- Right Column: Experience Timeline & Education -->
    <div>
      <div class="card shadow-sm mb-4">
        <div class="card-header">
          <h3><i data-lucide="briefcase"></i> Work Experience Timeline</h3>
        </div>
        <div class="card-body">
          ${experiences.map(exp => `
            <div class="timeline-item">
              <div class="timeline-dot"></div>
              <div class="timeline-title">${exp.job_title}</div>
              <div class="timeline-subtitle">${exp.company} • ${exp.duration}</div>
              <div class="timeline-desc">${exp.work_experience}</div>
            </div>
          `).join("")}
        </div>
      </div>

      <div class="card shadow-sm">
        <div class="card-header">
          <h3><i data-lucide="graduation-cap"></i> Education Credentials</h3>
        </div>
        <div class="card-body">
          ${educations.map(edu => `
            <div class="timeline-item">
              <div class="timeline-dot" style="background:var(--secondary);"></div>
              <div class="timeline-title">${edu.degree} in ${edu.field_of_study}</div>
              <div class="timeline-subtitle" style="color:var(--secondary);">${edu.school} • Class of ${edu.graduation_year}</div>
            </div>
          `).join("")}
        </div>
      </div>
    </div>
  `;

  if (window.lucide) lucide.createIcons();
}

async function proceedToMatching() {
  if (!state.activeUploadId) {
    showToast("Please upload a resume first.", "error");
    switchPage(2);
    return;
  }
  if (!state.activeJobId) {
    if (state.jobs.length > 0) {
      state.activeJobId = state.jobs[0].id;
    } else {
      showToast("Please select or configure a job requirement first.", "error");
      switchPage(1);
      return;
    }
  }

  showToast("Calculating candidate skill matching...", "info");

  try {
    const res = await fetch(`${API_BASE}/api/match/${state.activeUploadId}/${state.activeJobId}`, {
      method: "POST"
    });
    if (!res.ok) throw new Error("Matching calculation failed");
    const data = await res.json();
    state.matchingData = data;
    state.activeMatchingId = data.matching_id;

    renderMatchingPage(data);
    renderSkillGapPage(data);
    switchPage(4);
  } catch (err) {
    console.error("Matching error:", err);
    showToast("Failed to run matching analysis.", "error");
  }
}

// ==========================================================================
// PAGE 4: RESUME MATCHING DISPLAY
// ==========================================================================

function renderMatchingPage(data) {
  const container = document.getElementById("matching-content-area");
  if (!container) return;

  const matchPct = data.match_percentage || 0;
  const strokeOffset = 471 - (471 * matchPct) / 100;

  container.innerHTML = `
    <div class="matching-grid">
      <!-- Left: Circular Match Gauge -->
      <div class="card gauge-card shadow-sm">
        <h3 style="margin-bottom:14px; font-size:1.1rem; color:var(--text-main);">Overall Match Score</h3>
        
        <div class="gauge-container">
          <svg class="gauge-svg" viewBox="0 0 160 160">
            <defs>
              <linearGradient id="gauge-gradient" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stop-color="#4f46e5" />
                <stop offset="100%" stop-color="#7c3aed" />
              </linearGradient>
            </defs>
            <circle class="gauge-bg" cx="80" cy="80" r="65" />
            <circle class="gauge-progress" cx="80" cy="80" r="65"
              stroke-dasharray="471"
              stroke-dashoffset="${strokeOffset}" />
          </svg>
          <div class="gauge-center-text">
            <span class="gauge-percent">${matchPct}%</span>
            <span class="gauge-label">${matchPct >= 80 ? "High Match" : (matchPct >= 65 ? "Good Match" : "Moderate")}</span>
          </div>
        </div>

        <div style="font-size:0.85rem; color:var(--text-muted); margin-top:8px;">
          Position: <strong>${data.job_title}</strong><br>
          Company: ${data.company_name}
        </div>
      </div>

      <!-- Right: Split View (Matching Skills vs Missing Skills) -->
      <div>
        <div class="skills-comparison-split">
          <!-- Matching Skills Section -->
          <div class="match-box matched-box">
            <div class="match-box-title">
              <span><i data-lucide="check-circle-2"></i> MATCHING SKILLS (${data.matching_skills.length})</span>
              <span class="badge badge-green">Verified</span>
            </div>
            <div>
              ${data.matching_skills.length === 0 ? `<p class="text-muted text-sm">No exact required skill matches found.</p>` : ""}
              ${data.matching_skills.map(m => `
                <span class="skill-match-tag matched">
                  <i data-lucide="check"></i> ${m.skill}
                </span>
              `).join("")}
            </div>
          </div>

          <!-- Missing Skills Section -->
          <div class="match-box missing-box">
            <div class="match-box-title">
              <span><i data-lucide="x-circle"></i> MISSING SKILLS (${data.missing_skills.length})</span>
              <span class="badge badge-red">Skill Gap</span>
            </div>
            <div>
              ${data.missing_skills.length === 0 ? `<p style="color:#065f46; font-size:0.85rem; font-weight:600;">✓ All mandatory skills covered!</p>` : ""}
              ${data.missing_skills.map(m => `
                <span class="skill-match-tag missing">
                  <i data-lucide="x"></i> ${m.skill}
                </span>
              `).join("")}
            </div>
          </div>
        </div>

        ${data.optional_matched && data.optional_matched.length > 0 ? `
        <div class="card shadow-sm mb-4" style="background:#faf5ff; border-color:#e9d5ff;">
          <div class="card-body" style="padding:14px 20px;">
            <div style="font-weight:700; color:#6b21a8; font-size:0.88rem; margin-bottom:8px;">
              <i data-lucide="sparkles"></i> BONUS / OPTIONAL SKILLS MATCHED (${data.optional_matched.length}):
            </div>
            <div style="display:flex; flex-wrap:wrap; gap:6px;">
              ${data.optional_matched.map(opt => `
                <span class="tag-badge tag-optional">${opt}</span>
              `).join("")}
            </div>
          </div>
        </div>
        ` : ""}

        <!-- Explanation & Strengths -->
        <div class="explanation-card shadow-sm">
          <h4 style="font-size:1.05rem; margin-bottom:10px; display:flex; align-items:center; gap:8px;">
            <i data-lucide="file-check"></i> Matching Analysis & Explanation
          </h4>
          <p style="color:var(--text-body); font-size:0.92rem; line-height:1.6; margin-bottom:16px;">
            ${data.explanation}
          </p>

          <h5 style="font-size:0.95rem; margin-bottom:8px; color:var(--text-main);">Demonstrated Strengths:</h5>
          <ul class="strengths-list">
            ${(data.strengths || []).map(s => `<li>✓ ${s}</li>`).join("")}
          </ul>
        </div>
      </div>
    </div>
  `;

  if (window.lucide) lucide.createIcons();
}

// ==========================================================================
// PAGE 5: SKILL GAP SUMMARY
// ==========================================================================

function renderSkillGapPage(data) {
  const container = document.getElementById("skill-gap-content-area");
  if (!container) return;

  const gap = data.skill_gap_details || {};
  const possessed = gap.already_possessed || [];
  const missing = gap.missing_skills || [];
  const improvements = gap.needed_improvements || [];
  const roadmap = gap.learning_roadmap || [];

  container.innerHTML = `
    <div class="skill-gap-grid">
      <!-- 1. Skills candidate already has -->
      <div class="gap-column-card shadow-sm">
        <h4 style="color:#065f46;"><i data-lucide="check-check"></i> Skills Already Possessed (${possessed.length})</h4>
        <p class="text-muted text-xs mb-3">Skills validated from the candidate's verified document.</p>
        <div style="display:flex; flex-wrap:wrap; gap:6px; max-height:300px; overflow-y:auto;">
          ${possessed.map(s => `<span class="tag-badge" style="background:#ecfdf5; color:#065f46; border-color:#a7f3d0;">${s}</span>`).join("")}
        </div>
      </div>

      <!-- 2. Skills required but missing -->
      <div class="gap-column-card shadow-sm">
        <h4 style="color:#991b1b;"><i data-lucide="alert-triangle"></i> Required But Missing (${missing.length})</h4>
        <p class="text-muted text-xs mb-3">Mandatory role requirements absent from candidate resume.</p>
        ${missing.length === 0 ? `<p style="color:#065f46; font-size:0.88rem;">No critical skills missing!</p>` : ""}
        <div>
          ${missing.map(m => `
            <div style="background:#fef2f2; border:1px solid #fecaca; border-radius:var(--radius-md); padding:10px; margin-bottom:8px;">
              <strong style="color:#991b1b; font-size:0.9rem;">${m.skill}</strong>
              <div class="text-xs text-muted mt-1">Priority: High • Required by company</div>
            </div>
          `).join("")}
        </div>
      </div>

      <!-- 3. Skills that need improvement -->
      <div class="gap-column-card shadow-sm">
        <h4 style="color:#b45309;"><i data-lucide="trending-up"></i> Suggested Improvements (${improvements.length})</h4>
        <p class="text-muted text-xs mb-3">Targeted actions recommended to achieve 100% role parity.</p>
        ${improvements.length === 0 ? `<p class="text-muted text-xs">Profile currently fully satisfies role.</p>` : ""}
        <div>
          ${improvements.map(imp => `
            <div style="background:#fffbeb; border:1px solid #fde68a; border-radius:var(--radius-md); padding:10px; margin-bottom:8px;">
              <strong style="color:#92400e; font-size:0.88rem;">${imp.skill}</strong>
              <div style="font-size:0.8rem; color:#78350f; margin-top:4px;">${imp.recommended_action}</div>
            </div>
          `).join("")}
        </div>
      </div>
    </div>

    <!-- Personalized Learning Roadmap -->
    <div class="roadmap-timeline shadow-sm">
      <h3 style="font-size:1.15rem; margin-bottom:16px; display:flex; align-items:center; gap:8px;">
        <i data-lucide="map"></i> Structured Candidate Upskilling Roadmap
      </h3>
      <div>
        ${roadmap.map((step, idx) => `
          <div class="roadmap-step">
            <div class="roadmap-num">${idx + 1}</div>
            <div style="align-self:center;">
              <h5 style="font-size:0.95rem; color:var(--text-main);">${step}</h5>
            </div>
          </div>
        `).join("")}
      </div>
    </div>
  `;

  if (window.lucide) lucide.createIcons();
}

// ==========================================================================
// PAGE 6: MOCK ASSESSMENT (QUESTIONS FROM CANDIDATE SKILLS)
// ==========================================================================

async function proceedToAssessment(forceRegenerate = false) {
  if (!state.activeCandidateId) {
    showToast("Please upload a candidate resume first.", "error");
    switchPage(2);
    return;
  }

  showToast("Generating questions based strictly on candidate's extracted skills...", "info");

  try {
    const url = `${API_BASE}/api/assessment/questions/${state.activeCandidateId}?force_regenerate=${forceRegenerate}&matching_id=${state.activeMatchingId || ""}`;
    const res = await fetch(url);
    if (!res.ok) throw new Error("Failed to generate questions");
    const questions = await res.json();
    state.mockQuestions = questions;

    renderQuestionsPage(questions);
    renderAnswersPortal(questions);
    switchPage(6);
  } catch (err) {
    console.error("Assessment questions error:", err);
    showToast("Failed to fetch questions.", "error");
  }
}

function regenerateMockQuestions() {
  proceedToAssessment(true);
}

function renderQuestionsPage(questions) {
  const container = document.getElementById("questions-preview-area");
  if (!container) return;

  container.innerHTML = `
    <div class="alert-info-banner" style="background:#eef2ff; border:1px solid #c7d2fe; border-radius:var(--radius-lg); padding:16px 20px; margin-bottom:24px; display:flex; align-items:center; gap:12px;">
      <i data-lucide="info" style="color:var(--primary); width:24px; height:24px; flex-shrink:0;"></i>
      <div style="font-size:0.9rem; color:#1e1b4b;">
        <strong>Verified Candidate-Centric Question Logic:</strong> The ${questions.length} mock questions below are generated directly from the candidate's extracted skills (${[...new Set(questions.map(q => q.skill_name))].join(", ")}), testing real-world applied capabilities.
      </div>
    </div>

    ${questions.map((q, idx) => `
      <div class="question-card">
        <div class="question-header">
          <span class="question-skill-badge"><i data-lucide="target"></i> Assessed Skill: ${q.skill_name}</span>
          <span class="question-type-badge">${q.question_type} • ${q.difficulty}</span>
        </div>
        <div class="question-text">Q${idx + 1}. ${q.question}</div>
        ${q.sample_answer_hint ? `<div class="question-hint"><strong>Evaluation Focus:</strong> ${q.sample_answer_hint}</div>` : ""}
      </div>
    `).join("")}
  `;

  if (window.lucide) lucide.createIcons();
}

// ==========================================================================
// PAGE 7: CANDIDATE ANSWERS PORTAL
// ==========================================================================

function renderAnswersPortal(questions) {
  const container = document.getElementById("answers-portal-area");
  if (!container) return;

  container.innerHTML = `
    <form id="form-submit-answers" onsubmit="handleAnswersSubmission(event)">
      ${questions.map((q, idx) => `
        <div class="question-card">
          <div class="question-header">
            <span class="question-skill-badge"><i data-lucide="code"></i> Q${idx + 1} (${q.skill_name})</span>
            <span class="question-type-badge">${q.question_type}</span>
          </div>
          <div class="question-text">${q.question}</div>
          <div class="form-group" style="margin-top:14px; margin-bottom:0;">
            <label for="ans-${q.question_id}">Your Answer / Solution:</label>
            <textarea id="ans-${q.question_id}" class="form-control answer-textarea" rows="4" placeholder="Type your technical explanation, architectural approach, or code snippet here..." required></textarea>
          </div>
        </div>
      `).join("")}

      <div class="form-actions mt-4" style="display:flex; justify-content:space-between; align-items:center;">
        <button type="button" class="btn btn-secondary" onclick="fillDemoAnswers()">
          <i data-lucide="sparkles"></i> Auto-Fill Realistic Demo Answers
        </button>
        <button type="submit" class="btn btn-primary btn-lg" id="btn-submit-answers">
          <i data-lucide="check-circle"></i> Submit Answers for AI Evaluation
        </button>
      </div>
    </form>
  `;

  if (window.lucide) lucide.createIcons();
}

function fillDemoAnswers() {
  const demoAnswers = {
    "python": "Generators in Python use lazy evaluation via the 'yield' keyword, producing items one at a time on demand rather than allocating the entire sequence in memory. This reduces memory footprint to O(1). For large datasets, def stream_rows(file): for line in file: yield parse(line).",
    "sql": "WITH Ranked AS (SELECT *, DENSE_RANK() OVER (PARTITION BY department_id ORDER BY salary DESC) as rank_num FROM employees) SELECT * FROM Ranked WHERE rank_num <= 3; Window functions compute partitions without collapsing rows like GROUP BY.",
    "machine learning": "The bias-variance tradeoff balances underfitting and overfitting. High bias lacks model complexity, while high variance overfits noise. I employ L1 Lasso regularization for feature sparsity, L2 Ridge for weight shrinkage, Dropout in deep neural networks, and 5-Fold cross-validation.",
    "pytorch": "PyTorch constructs dynamic DAGs (directed acyclic graphs) on the fly during the forward pass. Tensors retain gradient history. We invoke optimizer.zero_grad() because gradients accumulate by default in PyTorch, which is useful in RNNs but causes corrupted gradients across batch steps if not cleared.",
    "docker": "For production containers, I use multi-stage builds with minimal alpine or distroless images, copy only wheel artifacts from the build phase, execute under a non-root UID, and place rarely-changing dependency layers first to leverage Docker layer caching.",
    "react": "React reconciliation utilizes fiber trees to perform heuristic O(n) Virtual DOM diffing. useMemo memoizes computed values across renders, useCallback preserves function reference identities, and React.memo prevents component tree re-evaluation unless incoming shallow props mutate.",
    "javascript": "JavaScript is single-threaded with an event loop. Synchronous code executes on the call stack. Completed Promises queue into the Microtask Queue, while setTimeout callbacks enter the Macrotask Queue. The engine drains microtasks exhaustively before yielding to the next macrotask.",
    "kubernetes": "Deployments declare desired state and manage ReplicaSets, which maintain pod replica counts. Readiness probes prevent traffic routing through ClusterIP until containers pass initialization checks, and Liveness probes restart deadlocked pods.",
    "aws": "A multi-AZ AWS architecture deploys an Application Load Balancer across public subnets, EC2 Auto Scaling or ECS containers in private subnets, and an Amazon RDS PostgreSQL cluster with synchronous Multi-AZ standby replica failover."
  };

  state.mockQuestions.forEach(q => {
    const textarea = document.getElementById(`ans-${q.question_id}`);
    if (textarea) {
      const skillLower = q.skill_name.toLowerCase();
      let matchedAns = "";
      for (const [key, ans] of Object.entries(demoAnswers)) {
        if (skillLower.includes(key) || key.includes(skillLower)) {
          matchedAns = ans;
          break;
        }
      }
      if (!matchedAns) {
        matchedAns = `In my production experience with ${q.skill_name}, we architected high-performance pipelines following industry standards, implementing automated tests, error logging, and performance benchmarks to verify scalability.`;
      }
      textarea.value = matchedAns;
    }
  });

  showToast("Realistic answers pre-filled across all questions!", "success");
}

async function handleAnswersSubmission(e) {
  e.preventDefault();
  const btn = document.getElementById("btn-submit-answers");
  btn.disabled = true;
  btn.innerHTML = `<i data-lucide="loader" class="spin"></i> Evaluating Answers with AI...`;
  if (window.lucide) lucide.createIcons();

  const answersPayload = [];
  state.mockQuestions.forEach(q => {
    const val = document.getElementById(`ans-${q.question_id}`).value.trim();
    answersPayload.push({
      question_id: q.question_id,
      answer: val
    });
  });

  try {
    const res = await fetch(`${API_BASE}/api/assessment/submit`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        candidate_id: state.activeCandidateId,
        matching_id: state.activeMatchingId,
        answers: answersPayload
      })
    });

    if (!res.ok) throw new Error("Evaluation submission failed");
    const data = await res.json();
    state.evaluationData = data;

    showToast("Assessment successfully scored and evaluated!", "success");
    renderEvaluationPage(data);
    renderPerformancePage(data.performance);
    switchPage(8);
  } catch (err) {
    console.error("Submission error:", err);
    showToast("Error evaluating answers.", "error");
  } finally {
    btn.disabled = false;
    btn.innerHTML = `<i data-lucide="check-circle"></i> Submit Answers for AI Evaluation`;
    if (window.lucide) lucide.createIcons();
  }
}

// ==========================================================================
// PAGE 8: ANSWER EVALUATION DISPLAY
// ==========================================================================

function renderEvaluationPage(data) {
  const container = document.getElementById("evaluation-content-area");
  if (!container) return;

  const answers = data.evaluated_answers || [];

  container.innerHTML = `
    <div style="margin-bottom:20px;">
      <h3 style="font-size:1.2rem; color:var(--text-main);">Individual Question Rubric Scores</h3>
      <p class="text-muted text-sm">Graded based on technical accuracy, concept coverage, clarity, and practical examples.</p>
    </div>

    ${answers.map((ans, idx) => `
      <div class="eval-card shadow-sm">
        <div class="eval-score-banner">
          <div>
            <span class="badge badge-purple">Q${idx + 1} • ${ans.skill_name}</span>
            <h4 style="font-size:1.05rem; margin-top:6px;">${ans.question}</h4>
          </div>
          <div style="text-align:right;">
            <div class="eval-score-num">${ans.score} / 10</div>
            <span class="badge ${ans.score >= 8 ? "badge-green" : (ans.score >= 6 ? "badge-blue" : "badge-amber")}">
              ${ans.score >= 8 ? "Strong Answer" : (ans.score >= 6 ? "Satisfactory" : "Needs Depth")}
            </span>
          </div>
        </div>

        <div style="background:#f8fafc; border-radius:var(--radius-md); padding:12px 16px; margin-bottom:14px; font-size:0.88rem;">
          <strong style="color:var(--text-muted); display:block; margin-bottom:4px;">Candidate's Submission:</strong>
          <span style="color:var(--text-body); font-style:italic;">"${ans.answer}"</span>
        </div>

        <div class="eval-detail-row">
          <span class="eval-detail-label"><i data-lucide="message-square"></i> AI Feedback:</span>
          <span>${ans.feedback}</span>
        </div>

        <div class="eval-detail-row">
          <span class="eval-detail-label"><i data-lucide="check-circle"></i> Technical Correctness & Relevance:</span>
          <span>${ans.correctness_relevance}</span>
        </div>

        <div class="eval-detail-row">
          <span class="eval-detail-label" style="color:#b45309;"><i data-lucide="lightbulb"></i> Areas for Improvement:</span>
          <span style="color:#92400e;">${ans.improvement_suggestions}</span>
        </div>
      </div>
    `).join("")}
  `;

  if (window.lucide) lucide.createIcons();
}

// ==========================================================================
// PAGE 9: PERFORMANCE SCORECARD
// ==========================================================================

function renderPerformancePage(perf) {
  const container = document.getElementById("performance-content-area");
  if (!container) return;

  const total = perf.total_score || 0;
  const max = perf.maximum_score || 50;
  const pct = perf.percentage_score || 0;
  const tier = perf.overall_performance || "Qualified";
  const scores = perf.scores_breakdown || [];
  const strong = perf.strong_areas || [];
  const improvement = perf.improvement_areas || [];

  container.innerHTML = `
    <!-- Top Big Scorecard Banner -->
    <div class="scorecard-banner">
      <div style="text-transform:uppercase; letter-spacing:0.1em; font-size:0.85rem; opacity:0.9;">Candidate Assessment Scorecard</div>
      <div class="scorecard-total">${total} <span style="font-size:1.8rem; font-weight:500; opacity:0.8;">/ ${max}</span></div>
      <div style="font-size:1.25rem; font-weight:700; margin-bottom:12px;">Overall Score: ${pct}%</div>
      <div class="performance-tier-pill">Status: ${tier}</div>
    </div>

    <!-- Per-Question Score Breakdown Cards -->
    <h3 style="font-size:1.1rem; margin-bottom:14px; color:var(--text-main);">Question-by-Question Score Breakdown</h3>
    <div class="scores-breakdown-grid">
      ${scores.map(s => `
        <div class="score-mini-card shadow-sm">
          <div style="font-size:0.75rem; text-transform:uppercase; color:var(--text-muted); font-weight:700;">Q${s.question_index} (${s.skill})</div>
          <div class="score-mini-num" style="color:var(--primary); margin:6px 0;">${s.score}<span style="font-size:0.9rem; font-weight:500; color:var(--text-muted);">/10</span></div>
          <div class="progress-bar-bg" style="background:#e2e8f0; height:6px; border-radius:99px; overflow:hidden;">
            <div style="background:var(--primary); height:100%; width:${(s.score / 10) * 100}%;"></div>
          </div>
        </div>
      `).join("")}
    </div>

    <!-- Strong Areas vs Improvement Areas -->
    <div class="grid-2-col">
      <div class="card shadow-sm">
        <div class="card-header">
          <h3><i data-lucide="check-check" style="color:var(--success);"></i> Key Technical Strengths</h3>
        </div>
        <div class="card-body">
          <ul style="list-style:none; padding:0;">
            ${strong.map(st => `
              <li style="display:flex; align-items:flex-start; gap:8px; margin-bottom:10px; font-size:0.9rem;">
                <i data-lucide="check" style="color:var(--success); width:18px; height:18px; flex-shrink:0; margin-top:2px;"></i>
                <span>${st}</span>
              </li>
            `).join("")}
          </ul>
        </div>
      </div>

      <div class="card shadow-sm">
        <div class="card-header">
          <h3><i data-lucide="trending-up" style="color:var(--warning);"></i> Areas for Development</h3>
        </div>
        <div class="card-body">
          <ul style="list-style:none; padding:0;">
            ${improvement.map(imp => `
              <li style="display:flex; align-items:flex-start; gap:8px; margin-bottom:10px; font-size:0.9rem;">
                <i data-lucide="arrow-up-right" style="color:var(--warning); width:18px; height:18px; flex-shrink:0; margin-top:2px;"></i>
                <span>${imp}</span>
              </li>
            `).join("")}
          </ul>
        </div>
      </div>
    </div>
  `;

  if (window.lucide) lucide.createIcons();
}

async function proceedToFullProfile() {
  if (!state.activeCandidateId) {
    showToast("No active candidate selected.", "error");
    return;
  }

  showToast("Compiling full 360° candidate dossier profile...", "info");

  try {
    const res = await fetch(`${API_BASE}/api/candidate-profile/${state.activeCandidateId}`);
    if (!res.ok) throw new Error("Failed to load profile");
    const profile = await res.json();
    state.profileData = profile;

    renderCandidateProfile(profile);
    switchPage(10);
  } catch (err) {
    console.error("Profile error:", err);
    showToast("Error loading candidate profile", "error");
  }
}

// ==========================================================================
// PAGE 10: CANDIDATE 360° PROFILE DOSSIER
// ==========================================================================

function renderCandidateProfile(p) {
  const container = document.getElementById("profile-content-area");
  if (!container) return;

  const match = p.matching || {};
  const perf = p.performance || {};
  const qas = p.assessment_qa || [];

  container.innerHTML = `
    <div class="profile-card">
      <!-- Profile Header -->
      <div style="display:flex; justify-content:space-between; align-items:flex-start; border-bottom:2px solid #f1f5f9; padding-bottom:24px;">
        <div style="display:flex; gap:20px; align-items:center;">
          <div class="candidate-avatar" style="background:var(--primary); color:#ffffff; width:76px; height:76px; font-size:2rem;">
            ${p.name ? p.name.charAt(0).toUpperCase() : "C"}
          </div>
          <div>
            <h2 style="font-size:1.8rem; color:var(--text-main);">${p.name}</h2>
            <div style="color:var(--text-muted); font-size:0.95rem; margin-top:4px;">
              Applied For: <strong style="color:var(--primary);">${match.job_title || "General Candidate"}</strong> at ${match.company_name || "Company"}
            </div>
            <div style="display:flex; gap:16px; margin-top:8px; font-size:0.85rem; color:var(--text-muted);">
              <span><i data-lucide="mail"></i> ${p.email}</span>
              <span><i data-lucide="phone"></i> ${p.phone}</span>
              <span><i data-lucide="map-pin"></i> ${p.location}</span>
            </div>
          </div>
        </div>

        <div style="text-align:right;">
          <span class="badge ${perf.overall_performance === 'Exceptional' ? 'badge-green' : 'badge-blue'}" style="font-size:0.9rem; padding:6px 16px;">
            ${perf.overall_performance || "Evaluated"}
          </span>
          <div style="font-size:1.8rem; font-weight:800; font-family:var(--font-heading); color:var(--primary); margin-top:6px;">
            ${match.match_percentage || 0}% Match
          </div>
          <div class="text-xs text-muted">Assessment: ${perf.total_score || 0}/${perf.maximum_score || 50} (${perf.percentage_score || 0}%)</div>
        </div>
      </div>

      <!-- Section 1: Resume & Personal Details -->
      <div class="profile-section-title"><i data-lucide="file-text"></i> Resume & Background Information</div>
      <div class="grid-2-col">
        <div>
          <h5 style="margin-bottom:8px;">Education Timeline:</h5>
          ${(p.education || []).map(e => `
            <div style="margin-bottom:8px; font-size:0.88rem;">
              <strong>${e.degree}</strong> - ${e.school} (${e.graduation_year})
            </div>
          `).join("")}
        </div>
        <div>
          <h5 style="margin-bottom:8px;">Experience Overview:</h5>
          ${(p.experience || []).map(exp => `
            <div style="margin-bottom:8px; font-size:0.88rem;">
              <strong>${exp.job_title}</strong> at ${exp.company} (${exp.duration})
            </div>
          `).join("")}
        </div>
      </div>

      <!-- Section 2: Extracted Skills & Certifications -->
      <div class="profile-section-title"><i data-lucide="code"></i> Extracted Skills & Certifications</div>
      <div style="display:flex; flex-wrap:wrap; gap:6px; margin-bottom:14px;">
        ${(p.all_skills || []).map(s => `<span class="tag-badge">${s}</span>`).join("")}
      </div>

      <!-- Section 3: Matching Analysis & Skill Gaps -->
      <div class="profile-section-title"><i data-lucide="git-compare"></i> Job Match & Skill Gap Breakdown</div>
      <div class="skills-comparison-split" style="margin-bottom:14px;">
        <div class="match-box matched-box" style="padding:14px;">
          <strong>Matching Mandatory Skills (${(match.matching_skills || []).length}):</strong>
          <div style="margin-top:8px;">
            ${(match.matching_skills || []).map(m => `<span class="skill-match-tag matched">${m.skill || m}</span>`).join("")}
          </div>
        </div>
        <div class="match-box missing-box" style="padding:14px;">
          <strong>Missing Required Skills (${(match.missing_skills || []).length}):</strong>
          <div style="margin-top:8px;">
            ${(match.missing_skills || []).length === 0 ? `<span style="color:#065f46; font-size:0.85rem;">None (Full Coverage)</span>` : ""}
            ${(match.missing_skills || []).map(m => `<span class="skill-match-tag missing">${m.skill || m}</span>`).join("")}
          </div>
        </div>
      </div>

      <!-- Section 4: Mock Questions, Answers & Assessment Scores -->
      <div class="profile-section-title"><i data-lucide="award"></i> Skill-Based Mock Assessment Q&A</div>
      <div>
        ${qas.map((qa, idx) => `
          <div style="border:1px solid #e2e8f0; border-radius:var(--radius-md); padding:16px; margin-bottom:14px; background:#fcfdfe;">
            <div style="display:flex; justify-content:space-between; margin-bottom:8px;">
              <span class="badge badge-purple">Q${idx + 1} • Skill: ${qa.skill_name}</span>
              <strong style="color:var(--primary); font-size:1rem;">Score: ${qa.score}/10</strong>
            </div>
            <div style="font-weight:600; font-size:0.95rem; margin-bottom:6px;">${qa.question}</div>
            <div style="background:#ffffff; border:1px solid #e2e8f0; border-radius:var(--radius-sm); padding:10px; font-size:0.88rem; font-style:italic; margin-bottom:8px;">
              "${qa.answer}"
            </div>
            <div style="font-size:0.84rem; color:var(--text-muted);">
              <strong>Feedback:</strong> ${qa.feedback}
            </div>
          </div>
        `).join("")}
      </div>

      <!-- Section 5: Overall Performance Analysis -->
      <div class="profile-section-title"><i data-lucide="clipboard-check"></i> Overall Recruiter Assessment</div>
      <div style="background:#f8fafc; border-left:4px solid var(--primary); padding:16px 20px; border-radius:var(--radius-md); font-size:0.92rem; line-height:1.6;">
        ${perf.performance_analysis || "Candidate demonstrated solid mastery across technical benchmarks."}
      </div>
    </div>
  `;

  if (window.lucide) lucide.createIcons();
}

// ==========================================================================
// PAGE 11: RECRUITER DASHBOARD
// ==========================================================================

async function loadDashboardStats() {
  try {
    const res = await fetch(`${API_BASE}/api/dashboard/stats`);
    const stats = await res.json();

    document.getElementById("kpi-total-candidates").textContent = stats.total_candidates || 0;
    document.getElementById("kpi-total-jobs").textContent = stats.total_jobs || 0;
    document.getElementById("kpi-avg-match").textContent = `${stats.average_match_percentage || 0}%`;
    document.getElementById("kpi-shortlisted").textContent = stats.shortlisted_candidates || 0;
  } catch (err) {
    console.error("Dashboard stats error:", err);
  }
}

let allDashboardCandidates = [];

async function loadDashboardCandidates() {
  const search = document.getElementById("dashboard-search-input") ? document.getElementById("dashboard-search-input").value.trim() : "";
  const jobId = document.getElementById("filter-job-select") ? document.getElementById("filter-job-select").value : "";
  const sort = document.getElementById("filter-sort-select") ? document.getElementById("filter-sort-select").value : "match_percentage";

  try {
    const params = new URLSearchParams();
    if (search) params.append("search", search);
    if (jobId) params.append("job_id", jobId);
    if (sort) params.append("sort_by", sort);

    const res = await fetch(`${API_BASE}/api/dashboard/candidates?${params.toString()}`);
    const list = await res.json();
    allDashboardCandidates = list;

    const tbody = document.getElementById("candidates-table-body");
    if (!tbody) return;
    tbody.innerHTML = "";

    if (list.length === 0) {
      tbody.innerHTML = `<tr><td colspan="8" style="text-align:center; padding:30px; color:var(--text-muted);">No candidates matching the current filters.</td></tr>`;
      return;
    }

    list.forEach(c => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td>
          <div style="font-weight:700; color:var(--text-main);">${c.name}</div>
          <div class="text-xs text-muted">${c.email}</div>
        </td>
        <td>
          <div style="font-weight:600;">${c.job_applied_for}</div>
          <div class="text-xs text-muted">${c.company_name}</div>
        </td>
        <td>
          <span style="font-weight:800; font-family:var(--font-heading); font-size:1.05rem; color:${c.match_percentage >= 80 ? 'var(--success)' : (c.match_percentage >= 65 ? 'var(--primary)' : 'var(--danger)')};">
            ${c.match_percentage}%
          </span>
        </td>
        <td>
          <span class="badge badge-green">${(c.matching_skills || []).length} Matched</span>
          <div class="text-xs text-muted mt-1">${(c.matching_skills || []).slice(0, 2).join(", ")}${c.matching_skills.length > 2 ? '...' : ''}</div>
        </td>
        <td>
          <span class="badge ${c.missing_skills.length === 0 ? 'badge-green' : 'badge-red'}">
            ${c.missing_skills.length === 0 ? 'None' : `${c.missing_skills.length} Gaps`}
          </span>
          <div class="text-xs text-muted mt-1">${(c.missing_skills || []).slice(0, 2).join(", ")}</div>
        </td>
        <td>
          <strong>${c.assessment_score} / ${c.maximum_score}</strong>
          <div class="text-xs text-muted">${c.score_percentage}%</div>
        </td>
        <td>
          <span class="badge ${c.performance === 'Exceptional' ? 'badge-green' : (c.performance === 'Strong Hire' ? 'badge-blue' : 'badge-amber')}">
            ${c.performance}
          </span>
        </td>
        <td>
          <div style="display:flex; gap:6px;">
            <button class="btn btn-outline btn-sm" onclick="viewCandidateDetails(${c.candidate_id})" title="View Complete 360° Profile">
              <i data-lucide="eye"></i> Profile
            </button>
            <button class="btn btn-outline btn-sm" onclick="toggleCompareCandidate(${c.candidate_id})" title="Add to side-by-side comparison">
              <i data-lucide="git-merge"></i> Compare
            </button>
          </div>
        </td>
      `;
      tbody.appendChild(tr);
    });

    if (window.lucide) lucide.createIcons();
  } catch (err) {
    console.error("Dashboard candidate table error:", err);
  }
}

function handleDashboardSearch() {
  loadDashboardCandidates();
}

function viewCandidateDetails(candidateId) {
  state.activeCandidateId = candidateId;
  proceedToFullProfile();
}

// Side-by-Side Candidate Comparison
function toggleCompareCandidate(candidateId) {
  const idx = state.compareCandidatesList.indexOf(candidateId);
  if (idx > -1) {
    state.compareCandidatesList.splice(idx, 1);
    showToast("Removed from comparison", "info");
  } else {
    if (state.compareCandidatesList.length >= 3) {
      showToast("You can compare up to 3 candidates at a time.", "warning");
      return;
    }
    state.compareCandidatesList.push(candidateId);
    showToast("Candidate added to comparison view!", "success");
  }

  renderCandidateComparison();
}

async function renderCandidateComparison() {
  const section = document.getElementById("comparison-section");
  const container = document.getElementById("comparison-content-area");
  if (!section || !container) return;

  if (state.compareCandidatesList.length === 0) {
    section.style.display = "none";
    return;
  }

  section.style.display = "block";
  container.innerHTML = `<div class="loading-state"><i data-lucide="loader" class="spin"></i> Loading comparison...</div>`;
  if (window.lucide) lucide.createIcons();

  try {
    const profiles = await Promise.all(
      state.compareCandidatesList.map(id => fetch(`${API_BASE}/api/candidate-profile/${id}`).then(r => r.json()))
    );

    container.innerHTML = `
      <div class="comparison-grid">
        ${profiles.map(p => {
          const match = p.matching || {};
          const perf = p.performance || {};
          return `
            <div class="comparison-card shadow-sm">
              <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
                <h4 style="font-size:1.15rem; color:var(--text-main);">${p.name}</h4>
                <button class="btn-icon" onclick="toggleCompareCandidate(${p.candidate_id})"><i data-lucide="x"></i></button>
              </div>

              <div style="background:#eef2ff; border-radius:var(--radius-md); padding:12px; text-align:center; margin-bottom:16px;">
                <div style="font-size:1.8rem; font-weight:800; color:var(--primary); font-family:var(--font-heading);">${match.match_percentage || 0}%</div>
                <div class="text-xs text-muted">Role Match: ${match.job_title || "Role"}</div>
              </div>

              <div style="margin-bottom:12px; font-size:0.88rem;">
                <strong>Assessment Marks:</strong> ${perf.total_score || 0} / ${perf.maximum_score || 50} (${perf.percentage_score || 0}%)<br>
                <strong>Evaluation Tier:</strong> <span class="badge badge-purple">${perf.overall_performance || "N/A"}</span>
              </div>

              <div style="margin-bottom:12px; font-size:0.88rem;">
                <strong>Matching Skills (${(match.matching_skills || []).length}):</strong>
                <div style="display:flex; flex-wrap:wrap; gap:4px; margin-top:4px;">
                  ${(match.matching_skills || []).map(m => `<span class="tag-badge" style="font-size:0.75rem; background:#ecfdf5; color:#065f46; border-color:#a7f3d0;">${m.skill || m}</span>`).join("")}
                </div>
              </div>

              <div style="margin-bottom:12px; font-size:0.88rem;">
                <strong>Missing Skills (${(match.missing_skills || []).length}):</strong>
                <div style="display:flex; flex-wrap:wrap; gap:4px; margin-top:4px;">
                  ${(match.missing_skills || []).length === 0 ? `<span class="text-xs text-muted">None</span>` : ""}
                  ${(match.missing_skills || []).map(m => `<span class="tag-badge" style="font-size:0.75rem; background:#fef2f2; color:#991b1b; border-color:#fecaca;">${m.skill || m}</span>`).join("")}
                </div>
              </div>

              <div style="margin-top:16px;">
                <button class="btn btn-primary btn-sm" style="width:100%;" onclick="viewCandidateDetails(${p.candidate_id})">
                  View Full Dossier
                </button>
              </div>
            </div>
          `;
        }).join("")}
      </div>
    `;

    if (window.lucide) lucide.createIcons();
    section.scrollIntoView({ behavior: "smooth" });
  } catch (err) {
    console.error("Comparison render error:", err);
  }
}

function clearCandidateComparison() {
  state.compareCandidatesList = [];
  const section = document.getElementById("comparison-section");
  if (section) section.style.display = "none";
}

// Export CSV
function exportDashboardCSV() {
  if (allDashboardCandidates.length === 0) {
    showToast("No candidate records to export.", "warning");
    return;
  }

  const headers = ["Candidate ID", "Name", "Email", "Phone", "Target Job", "Company", "Match Percentage", "Assessment Score", "Max Score", "Performance Tier"];
  const rows = allDashboardCandidates.map(c => [
    c.candidate_id,
    `"${c.name}"`,
    `"${c.email}"`,
    `"${c.phone}"`,
    `"${c.job_applied_for}"`,
    `"${c.company_name}"`,
    c.match_percentage,
    c.assessment_score,
    c.maximum_score,
    `"${c.performance}"`
  ]);

  const csvContent = "data:text/csv;charset=utf-8," + [headers.join(","), ...rows.map(e => e.join(","))].join("\n");
  const encodedUri = encodeURI(csvContent);
  const link = document.createElement("a");
  link.setAttribute("href", encodedUri);
  link.setAttribute("download", `Candidate_Assessment_Report_${new Date().toISOString().slice(0, 10)}.csv`);
  document.body.appendChild(link);
  link.click();
  link.remove();

  showToast("Candidate report downloaded as CSV!", "success");
}
