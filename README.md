# 複利人生實驗室

台灣理財教育內容站 — ETF、券商開戶、信用卡、保險的白話完整解析。
每天一個讓錢自動工作的方法。

## 結構

- `posts/` — 20 篇理財長文（HTML）
- `index.html` — 首頁
- `concepts/brokers/comparisons/cards/insurance.html` — 5 個分類索引頁
- `assets/style.css` — 設計系統（淺色．柔和藍綠．Noto Sans TC）
- `build.py` — 由 `passive-income-projects/03-affiliate-marketing/content/*.md` 重建全站

## 重建

```bash
python build.py
```

文章內標示「聯盟連結待補」處，未來填入真實聯盟連結後重跑 `build.py` 即可。

## 免責

所有內容僅供投資理財教育與資訊分享，不構成投資建議。
