# YouTube trend kuzatuvchi

YouTube Data API v3 orqali tanlangan mamlakatlarda (standart: AQSh, Buyuk Britaniya, Rossiya)
hozir eng ko'p ko'rilayotgan videolarni har kuni yig'ib, kategoriya va kanal bo'yicha
hisobot beradi. Tashqi kutubxona kerak emas, Python 3.9+ yetarli.

## 1. API kalit olish (bepul, 5 daqiqa)

1. https://console.cloud.google.com ga kiring, yangi loyiha oching.
2. "APIs & Services" > "Library" > **YouTube Data API v3** ni yoqing.
3. "Credentials" > "Create credentials" > **API key**. Kalitni nusxalang.
4. Kalitni muhit o'zgaruvchisiga qo'ying:

```bash
export YOUTUBE_API_KEY="AIza..."
```

Kunlik bepul kvota 10 000 birlik. Bitta `fetch` (3 mamlakat, 200 tadan video)
taxminan 15 birlik sarflaydi.

## 2. Ishga tushirish

```bash
# Bugungi trendlarni olish va ekranga qisqa hisobot chiqarish
python3 tools/youtube_trends/yt_trends.py fetch

# Boshqa mamlakatlar, kamroq video
python3 tools/youtube_trends/yt_trends.py fetch --regions US,CA,AU --max 100

# Yig'ilgan kunlar bo'yicha hisobot (so'nggi 14 kun)
python3 tools/youtube_trends/yt_trends.py report --days 14
```

## 2a. Yo'nalish bo'yicha qidiruv (asosiy vosita)

`fetch` beradigan umumiy trend charti asosan o'yin va musiqa. Foydali kontent u yerga
kam chiqadi, shuning uchun o'z yo'nalishingizni `search` bilan o'lchang: kalit so'z bo'yicha
so'nggi N kunda chop etilgan va eng ko'p ko'rilgan videolar, kanallar bilan.

```bash
# So'nggi 7 kunda "interesting facts" bo'yicha eng ko'p ko'rilgan videolar (AQSh, ingliz)
python3 tools/youtube_trends/yt_trends.py search "interesting facts"

# Faqat Education kategoriyasi, 30 kun, 4-20 daqiqalik videolar
python3 tools/youtube_trends/yt_trends.py search "interesting facts" --category education --days 30 --duration medium

# Rus auditoriyasi uchun xuddi shu
python3 tools/youtube_trends/yt_trends.py search "интересные факты" --region RU --lang ru --days 30

# Boshqa mavzular
python3 tools/youtube_trends/yt_trends.py search "explained" --category education --days 14
python3 tools/youtube_trends/yt_trends.py search "what if" --category science --days 30
```

Har `search` ~102 birlik sarflaydi, kuniga ~90 ta qidiruv bepul. Natijalar
`data/search_YYYY-MM-DD.csv` ga yoziladi, `query` ustunida qaysi so'rov ekani turadi.

Kategoriya nomlari: `education, science, howto, entertainment, people, news, comedy, gaming`.

Jonli efirlar (`is_live=yes`) hisobotlardan chiqarib tashlanadi, chunki ular soatlik
ko'rish tezligini sun'iy oshiradi. CSV da ular saqlanib qoladi.

CSV fayllar `tools/youtube_trends/data/trends_YYYY-MM-DD.csv` ga yoziladi. Bir kunda
bir necha marta ishga tushirsangiz, qatorlar shu kunning fayliga qo'shilib boradi.

## 3. Har kuni avtomatik yig'ish (cron)

```bash
crontab -e
# Har kuni 09:00 da
0 9 * * * cd /path/to/InfiniteTalk && YOUTUBE_API_KEY="AIza..." python3 tools/youtube_trends/yt_trends.py fetch --quiet >> tools/youtube_trends/cron.log 2>&1
```

## Hisobotda nima bor

- **Kategoriya bo'yicha VPH**: qaysi kategoriya hozir eng tez ko'rish yig'ayotgani.
- **Format**: long va short nisbati.
- **Eng tez uchgan videolar**: soatiga ko'rish (VPH) bo'yicha top-10, kanal va sarlavha bilan.
- **`report`**: bir necha kunlik ma'lumotdan kategoriya ulushi, barqaror kanallar
  (turli kunlarda turli videolari bilan chiqqanlar) va davrdagi eng tez uchgan videolar.

## CSV ustunlari

`snapshot_date, snapshot_time_utc, region, rank, video_id, title, channel_id,
channel_title, category, format, duration_sec, published_at, hours_since_publish,
view_count, like_count, comment_count, views_per_hour, engagement_rate, is_live, query, url`

`format`: davomiyligi 3 daqiqagacha bo'lgan videolar `short`, qolganlari `long`.
