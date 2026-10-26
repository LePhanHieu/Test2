(() => {
  const $ = (selector) => document.querySelector(selector);
  const escapeHtml = (value) => String(value ?? "").replace(/[&<>"']/g, (char) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[char]);
  const display = (value) => value === null || value === undefined || value === "" ? "—" : escapeHtml(value);
  const fmtDate = (date) => date ? new Date(date).toLocaleDateString("vi-VN") : "—";
  const statusLabels = { CREATED: "Mới tạo", UPLOADED: "Đã tải ảnh", ANALYZED: "Đã phân tích", REVIEWED: "Đã đánh giá", COMPLETED: "Hoàn thành" };
  let page = 1;
  let pages = 1;
  let requestId = 0;
  let searchTimer;

  async function getJson(url) {
    const response = await fetch(url, { credentials: "same-origin", headers: { Accept: "application/json" } });
    const data = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(data.message || data.description || "Không thể tải dữ liệu ca khám.");
    return data;
  }

  async function loadAdminCases() {
    const id = ++requestId;
    const params = new URLSearchParams({ page: String(page) });
    [["search", "#case-search"], ["status", "#case-status"], ["doctor", "#case-doctor"], ["start", "#case-from"], ["end", "#case-to"]].forEach(([name, field]) => {
      if ($(field).value.trim()) params.set(name, $(field).value.trim());
    });
    $("#case-count").textContent = "Đang tải danh sách...";
    try {
      const data = await getJson(`/api/admin/cases?${params}`);
      if (id !== requestId) return;
      $("#case-total").textContent = Number(data.metrics.total).toLocaleString("vi-VN");
      $("#case-processing").textContent = Number(data.metrics.processing).toLocaleString("vi-VN");
      $("#case-completed").textContent = Number(data.metrics.completed).toLocaleString("vi-VN");
      const doctorSelect = $("#case-doctor");
      const selected = doctorSelect.value;
      doctorSelect.replaceChildren(new Option("Tất cả bác sĩ", ""), ...(data.doctors || []).map((doctor) => new Option(doctor.name, doctor.id)));
      doctorSelect.value = selected;
      page = data.page;
      pages = data.pages;
      $("#case-count").textContent = `Tìm thấy ${data.total} ca khám`;
      $("#case-page").textContent = `Trang ${page}/${pages}`;
      $("#case-prev").disabled = page <= 1;
      $("#case-next").disabled = page >= pages;
      $("#admin-cases-table").innerHTML = data.cases.length ? data.cases.map((item) => `<tr><td><b>${display(item.code)}</b></td><td>${display(item.patient)}</td><td>${display(item.doctor)}</td><td>${fmtDate(item.created_at)}</td><td><span class="status-chip ${item.status === "COMPLETED" ? "success" : "warning"}">${display(statusLabels[item.status] || item.status)}</span></td><td><button type="button" class="text-btn" data-view-case="${item.id}">Xem chi tiết</button></td></tr>`).join("") : '<tr><td colspan="6" class="loading">Không có ca khám phù hợp. Hãy thử xóa bộ lọc.</td></tr>';
    } catch (error) {
      if (id !== requestId) return;
      $("#case-count").textContent = "Không tải được dữ liệu.";
      $("#admin-cases-table").innerHTML = `<tr><td colspan="6" class="loading">${escapeHtml(error.message)}</td></tr>`;
    }
  }

  async function openCaseDetail(caseId) {
    const modal = $("#admin-case-modal");
    modal.classList.add("open");
    $("#admin-case-detail").textContent = "Đang tải chi tiết...";
    try {
      const item = await getJson(`/api/admin/cases/${caseId}`);
      if (!modal.classList.contains("open")) return;
      $("#case-detail-title").textContent = `Ca khám ${item.code}`;
      const overview = `<div class="case-detail-info"><p><b>Bệnh nhân:</b> ${display(item.patient)}</p><p><b>Bác sĩ:</b> ${display(item.doctor)}</p><p><b>Ngày tạo:</b> ${fmtDate(item.created_at)}</p><p><b>Vị trí tổn thương:</b> ${display(item.lesion_location)}</p><p><b>Trạng thái:</b> ${display(statusLabels[item.status] || item.status)}</p></div>`;
      const images = (item.images || []).map((image) => `<figure><img src="${image.url}" alt="Ảnh Dermoscopy" loading="lazy"/><figcaption>${display(image.filename)} · ${display(image.status)}</figcaption></figure>`).join("");
      const analyses = (item.analyses || []).map((analysis) => `<div class="case-analysis"><b>Phân tích #${analysis.id} · ${display(analysis.status)}</b><p>Diện tích: ${display(analysis.area)} px² · Chu vi: ${display(analysis.perimeter)} px · Tỷ lệ: ${analysis.ratio == null ? "—" : (analysis.ratio * 100).toFixed(2) + "%"}</p>${(analysis.results || []).map((result) => `<p>${display(result.model)}: ${display(result.class)} · Độ tin cậy: ${result.probability == null ? "—" : (result.probability * 100).toFixed(2) + "%"}</p>`).join("")}${analysis.gradcam_url ? `<img src="${analysis.gradcam_url}" alt="Grad-CAM" loading="lazy"/>` : ""}${analysis.contour_url ? `<img src="${analysis.contour_url}" alt="Khoanh vùng tổn thương" loading="lazy"/>` : ""}</div>`).join("");
      const reviews = (item.reviews || []).map((review) => `<div class="case-analysis"><b>${display(review.doctor)} · ${display(review.status)}</b><p>Ghi chú: ${display(review.note)}</p><p>Kết luận: ${display(review.conclusion)}</p><p>Khuyến nghị: ${display(review.recommendation)}</p></div>`).join("");
      $("#admin-case-detail").innerHTML = `${overview}<h3>Ảnh Dermoscopy</h3><div class="case-images">${images || "Chưa có ảnh."}</div><h3>Kết quả phân tích đã lưu</h3>${analyses || "Chưa có kết quả."}<h3>Nhận xét bác sĩ</h3>${reviews || "Chưa có nhận xét."}`;
    } catch (error) { $("#admin-case-detail").textContent = error.message; }
  }

  const changed = () => { page = 1; loadAdminCases(); };
  $("#case-search").addEventListener("input", () => { clearTimeout(searchTimer); searchTimer = setTimeout(changed, 250); });
  ["#case-status", "#case-doctor", "#case-from", "#case-to"].forEach((field) => $(field).addEventListener("change", changed));
  $("#case-reset").addEventListener("click", () => { ["#case-search", "#case-status", "#case-doctor", "#case-from", "#case-to"].forEach((field) => { $(field).value = ""; }); changed(); });
  $("#case-prev").addEventListener("click", () => { if (page > 1) { page--; loadAdminCases(); } });
  $("#case-next").addEventListener("click", () => { if (page < pages) { page++; loadAdminCases(); } });
  $("#admin-cases-table").addEventListener("click", (event) => { const button = event.target.closest("[data-view-case]"); if (button) openCaseDetail(button.dataset.viewCase); });
  $("#close-case-detail").addEventListener("click", () => $("#admin-case-modal").classList.remove("open"));
  $("#admin-case-modal").addEventListener("click", (event) => { if (event.target.id === "admin-case-modal") event.currentTarget.classList.remove("open"); });
  window.loadAdminCases = loadAdminCases;
})();
