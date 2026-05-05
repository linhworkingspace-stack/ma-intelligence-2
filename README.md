# 📊 M&A Financial Intelligence Newsletter

Newsletter tự động hằng ngày về **M&A · Due Diligence · Tài chính · Kế toán · Thuế · Kinh tế vĩ mô**.

Chạy mỗi sáng 6:30 giờ VN → tạo trang web → gửi email với link đọc.

---

## ⚡ Setup (30 phút, làm 1 lần)

### Bước 1 — Tạo GitHub repository

1. Vào [github.com](https://github.com) → **New repository**
2. Đặt tên: `ma-intelligence` (hoặc tên bất kỳ)
3. Để **Public** (GitHub Pages miễn phí cần public)
4. Bỏ tick "Add README" → **Create repository**
5. Upload toàn bộ thư mục này lên repo (kéo thả hoặc dùng git)

### Bước 2 — Lấy Gemini API Key (miễn phí)

1. Vào [aistudio.google.com](https://aistudio.google.com)
2. Đăng nhập bằng Google account
3. Click **Get API Key** → **Create API key**
4. Copy key (dạng: `AIza...`)

### Bước 3 — Lấy Gmail App Password

> Dùng để gửi email. Không dùng password Gmail thật.

1. Vào [myaccount.google.com/security](https://myaccount.google.com/security)
2. Bật **2-Step Verification** (nếu chưa bật)
3. Tìm **App passwords** → Create
4. Chọn app: **Mail**, device: **Other** → đặt tên "MA Newsletter"
5. Copy 16 ký tự (dạng: `xxxx xxxx xxxx xxxx`)

### Bước 4 — Thêm Secrets vào GitHub

1. Vào repo GitHub → **Settings** → **Secrets and variables** → **Actions**
2. Click **New repository secret**, thêm lần lượt:

| Secret Name | Giá trị |
|---|---|
| `GEMINI_API_KEY` | Key từ bước 2 |
| `EMAIL_FROM` | Gmail của bạn (vd: linh@gmail.com) |
| `EMAIL_TO` | Email nhận (có thể giống EMAIL_FROM) |
| `EMAIL_PASSWORD` | App password từ bước 3 (không có dấu cách) |

### Bước 5 — Bật GitHub Pages

1. Vào repo → **Settings** → **Pages**
2. Source: **Deploy from a branch**
3. Branch: **main** / **master**, Folder: **/docs**
4. Click **Save**
5. Sau ~2 phút sẽ có URL dạng: `https://[username].github.io/ma-intelligence/`

### Bước 6 — Chạy thử

1. Vào repo → **Actions** → **Generate Daily Newsletter**
2. Click **Run workflow** → **Run workflow**
3. Chờ ~2-3 phút → xem log
4. Vào URL GitHub Pages để xem kết quả
5. Kiểm tra email

---

## 🕐 Lịch chạy tự động

Mặc định: **6:30 sáng mỗi ngày** (giờ VN).

Để thay đổi, sửa dòng `cron` trong `.github/workflows/newsletter.yml`:
```yaml
- cron: '30 23 * * *'   # 23:30 UTC = 06:30 ICT
```

---

## 📰 Nguồn tin

| Nguồn | Chủ đề | Ngôn ngữ |
|---|---|---|
| Axios Pro Rata | M&A, PE, VC deals | Tiếng Anh |
| The Middle Market | Mid-size M&A, PE | Tiếng Anh |
| PitchBook News | PE/VC data-driven | Tiếng Anh |
| Harvard Law Corp Gov | Pháp lý M&A, Governance | Tiếng Anh |
| Thời báo Tài chính VN | Chính sách tài chính, thuế | Tiếng Việt |
| Tạp chí Kế toán & Kiểm toán | Thông tư, nghị định, chuẩn mực | Tiếng Việt |
| Tạp chí Tài chính DN | Góc nhìn doanh nghiệp | Tiếng Việt |
| VnEconomy | Kinh tế vĩ mô, FDI, thị trường vốn | Tiếng Việt |

---

## 💰 Chi phí

**Hoàn toàn miễn phí:**
- GitHub Actions: 2,000 phút/tháng (dùng ~3 phút/ngày = ~90 phút/tháng)
- GitHub Pages: Miễn phí với public repo
- Gemini API: Free tier 1,500 requests/ngày
- Gmail SMTP: Miễn phí

---

## 🔧 Tùy chỉnh

Sửa file `scripts/generate.py`:
- **Thêm/bỏ nguồn**: Sửa mảng `SOURCES`
- **Thêm từ khóa lọc**: Sửa `keywords` trong từng source
- **Đổi giờ gửi**: Sửa `cron` trong workflow file
- **Đổi màu sắc**: Sửa `CAT_COLORS` trong hàm `build_html`
