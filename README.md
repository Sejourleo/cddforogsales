# ToB 客户拜访 AI 背调 Skill

这是一个可公开分享的 Hermes skill 页面，用于把公开信息转化为销售拜访前的客户判断、痛点假设、决策链猜测、开场话术和验证问题。

公网页面：

```text
https://sejourleo.github.io/cddforogsales/
```

## 文件

- `index.html`：可扫码阅读的静态页面。
- `SKILL.md`：Hermes skill 原文。
- `references/chinese-company-lookup-tactics.md`：中文企业查询策略参考资料。
- `qr.png` / `qr.svg`：指向公网页面的二维码。
- `share-card.png`：适合发微信群、飞书、PPT 或文档的二维码分享卡片。
- `build_share.py`：重新生成页面、二维码和分享卡片的构建脚本。

## 重新生成

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install "qrcode[pil]>=7.4,<8" "pillow>=10,<12"
python build_share.py --url https://sejourleo.github.io/cddforogsales/
```

GitHub Pages 会通过 `.github/workflows/pages.yml` 自动发布。
