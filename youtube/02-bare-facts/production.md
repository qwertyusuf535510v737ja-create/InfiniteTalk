# Bare Facts — ishlab chiqarish quvuri

Skriptdan tayyor videogacha. Har video shu yo'ldan o'tadi.
Bir video uchun taxminiy vaqt: 8–12 soat, shundan 2–4 soati render.

---

## Bosqich 1 — Skript (2–4 soat)

Skript `scripts/NN-nom.md` faylida yoziladi va quyidagilarni o'z ichiga oladi:
sarlavha variantlari, thumbnail brief, to'liq matn ekran ko'rsatmalari bilan,
manbalar ro'yxati, aniqlik eslatmalari va tavsif shabloni.

**Qat'iy qoida:** har bir raqam manbadan olinadi. Manba topilmagan raqam
skriptdan chiqariladi, yumshatilmaydi.

Birinchi 15 sekund alohida yoziladi va ovoz bilan uch marta tinglab ko'riladi.
Agar u savol bilan boshlansa — qayta yoziladi. Javob bilan boshlanishi kerak.

## Bosqich 2 — Ovoz (30–60 daqiqa)

Skript matnidan faqat narratsiya qismi ajratiladi (ekran ko'rsatmalari emas).

```bash
# Ekran ko'rsatmalari va sarlavhalarni tashlab, toza narratsiya chiqarish
sed -n '/^## SKRIPT/,/^## Manbalar/p' youtube/02-bare-facts/scripts/01-death-zone.md \
  | grep -v '^\*\*\[' | grep -v '^###' | grep -v '^---' | grep -v '^\*\*\[PAUZA\]' \
  > /tmp/narration_01.txt
```

Ovoz uchun TTS yoki jonli yozuv. Talablar:
- Temp sekin, 145–155 so'z/daqiqa
- Raqam aytilganda oldida qisqa pauza
- Hissiy bo'yoq yo'q — shifokor ohangi

Natija: `audio/01-death-zone.wav`, 16 kHz yoki undan yuqori, mono.

## Bosqich 3 — Avatar (2–4 soat render)

Bare Facts portfeldagi yagona avatar kanali. Prezenter rasmi hamma videoda
bir xil bo'ladi — bu kanalning tanib olinishi uchun muhim.

Kirish JSON tayyorlanadi (`examples/single_example_image.json` shaklida):
prezenter rasmi yo'li, audio fayl yo'li va prompt.

```bash
python generate_infinitetalk.py \
    --ckpt_dir weights/Wan2.1-I2V-14B-480P \
    --wav2vec_dir 'weights/chinese-wav2vec2-base' \
    --infinitetalk_dir weights/InfiniteTalk/single/infinitetalk.safetensors \
    --input_json youtube/02-bare-facts/inputs/01-death-zone.json \
    --size infinitetalk-720 \
    --sample_steps 40 \
    --mode streaming \
    --motion_frame 9 \
    --save_file youtube/02-bare-facts/out/01-death-zone
```

**Eslatma:** `--max_frame_num` standart 1000 kadr (~40 sekund). 15 daqiqalik
video uchun ovoz bo'laklarga bo'linadi va `streaming` rejimida ketma-ket
render qilinadi, keyin montajda ulanadi. Uzun bitta renderga urinmang —
xotira yetmaydi va xato bo'lsa hammasi qaytadan ketadi.

Amaliy yo'l: prezenter faqat kirish, bo'lim boshlari va yakunda ko'rinadi
(jami 3–4 daqiqa). Qolgan vaqt ilmiy grafika va diagramma. Bu ham render
vaqtini to'rt baravar qisqartiradi, ham videoni ko'rishga qiziqarliroq qiladi.

## Bosqich 4 — Vizual material (3–5 soat)

Ekran ko'rsatmalari bo'yicha. Uch turdagi material:

| Tur | Qayerdan | Eslatma |
|-----|----------|---------|
| Diagramma va animatsiya | O'zimiz yasaymiz | Kanalning asosiy vizual tili |
| Ilmiy grafika va jadval | Manbadagi ma'lumotdan qayta chiziladi | Skrinshot emas, qayta chiziladi |
| Arxiv foto va video | Litsenziyasi tekshirilgan manbalar | Litsenziya yozib qo'yiladi |

**Qoida:** boshqa YouTube kanalidan material olinmaydi. Hech qachon.
Bu qayta ishlatilgan kontent siyosatiga tushadi va monetizatsiyani yo'qotadi.

## Bosqich 5 — Montaj

- Birinchi 30 sekundda kesim tezligi yuqori: har 2–3 sekundda yangi kadr
- Raqam aytilganda u ekranda paydo bo'ladi, aytilgandan 0,3 sekund keyin emas, aniq bir vaqtda
- Musiqa: past chastotali ambient, −24 dB. Raqam aytilganda musiqa 3 dB pasayadi
- Bo'lim kartalari orasida 0,5 sekundlik to'liq sukunat
- Yakuniy 20 sekund: keyingi video anonsi va end screen

## Bosqich 6 — Chiqarishdan oldingi tekshiruv

`channel-setup.md` dagi ro'yxat bajariladi. Qo'shimcha:

- [ ] Narratsiyadagi har bir raqam ekrandagi raqam bilan mos
- [ ] Manbalar havolalari ochilib tekshirilgan
- [ ] Sintetik kontent belgisi qo'yilgan
- [ ] Thumbnail 2 xil o'lchamda ko'rilgan: to'liq ekran va telefon ro'yxatidagi kichik ko'rinish
- [ ] Birinchi 15 sekund ovozsiz ham tushunarli (ko'pchilik ovozsiz boshlaydi)

## Bosqich 7 — Chiqargandan keyin

- Birinchi 2 soat: har bir izohga javob berish. Bu YouTube'ga signal beradi
- 48 soatdan keyin: CTR va o'rtacha ko'rish davomiyligini yozib olish
- CTR 4% dan past bo'lsa: thumbnail almashtiriladi, sarlavha emas
- O'rtacha ko'rish 40% dan past bo'lsa: keyingi videoda hook qayta ishlanadi
- Raqamlar `youtube/02-bare-facts/results.md` ga yoziladi

## Rus tiliga dublyaj (6-oydan keyin)

Asl video chiqqandan 2 hafta keyin, faqat 500K+ ko'rish olgan videolar uchun.
InfiniteTalk lip-sync bilan rus ovozi ustiga qo'yiladi. Alohida kanal emas —
YouTube'ning ko'p tilli audio treki sifatida qo'shiladi.

Sabab: rus RPM'i $1 200/1M, ingliz $6 000/1M. Alohida kanal ochish va uni
noldan o'stirish shu farqni qoplamaydi. Audio trek esa deyarli bepul.
