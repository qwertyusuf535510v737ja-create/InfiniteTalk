# Kirish fayllari

Har bir video uchun bitta JSON. Shakl `examples/single_example_image.json` bilan bir xil.

- `prompt` — prezenter va sahna tavsifi. **Hamma videoda bir xil qoladi**,
  chunki prezenter ko'rinishi kanalning tanib olinishi uchun o'zgarmasligi kerak.
- `cond_video` — prezenter rasmi. Bitta rasm, `assets/presenter.png`.
- `cond_audio.person1` — ovoz fayli. Uzun narratsiya bo'laklarga bo'linadi,
  har bo'lak uchun alohida JSON va alohida render (`-part01`, `-part02`, ...).

`assets/` va `audio/` papkalari git'ga qo'shilmaydi — ular katta fayllar.
