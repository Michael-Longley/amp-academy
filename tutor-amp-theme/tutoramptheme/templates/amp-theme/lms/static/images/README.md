# Brand Image Assets

Replace the placeholder files in this directory with your actual brand assets before deploying.

| File | Dimensions | Usage |
|---|---|---|
| `logo.png` | ~200×60px recommended | LMS header (dark background variant) |
| `logo-white.png` | ~200×60px recommended | LMS footer (shown on dark background) |
| `favicon.ico` | 16×16, 32×32 multi-size | Browser tab icon |

After replacing images, rebuild the Open edX Docker image:

```bash
tutor config save
tutor images build openedx
tutor local restart
```
