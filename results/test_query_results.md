# Test-query results (produced by `python main.py test`)

- Generated: 2026-09-25 08:30
- Embedding model: `intfloat/multilingual-e5-small`
- Generator: `gemini` · top-k = 4 · vector DB: ChromaDB (cosine)
- Retrieval filter: `kind ∈ {prose, table_row}` (quiz/TOC/cover chunks excluded)

## Query 1 (Hindi)

| Field | Value |
|---|---|
| Query | SLV-III ने किस उपग्रह को कक्षा में स्थापित किया और किस वर्ष? |
| Answer | SLV-III ने जुलाई 1980 में रोहिणी उपग्रह को कक्षा में स्थापित किया [chunk 30, 78]। |
| Source (citation) | page: 8 · section: "इसरो के वर्ष और SLV-III" · chunk_id: 30 · score: 0.89<br>page: 17 · section: "जीवन-रेखा (टाइमलाइन)" · chunk_id: 78 · score: 0.87 |
| Expected (from document) | रोहिणी उपग्रह, 1980 |

Other retrieved chunks:

- page: 8 · section: "इसरो के वर्ष और SLV-III" · chunk_id: 29 · score: 0.88 — अगले वर्ष जब मिशन सफल हुआ, तो धवन पीछे हट गए और श्रेय कलाम को लेने दिया। यह विरोधाभास — एक नेता जो विफलता को आ…
- page: 20 · section: "संस्थाओं एवं शब्दों की शब्दावली" · chunk_id: 93 · score: 0.87 — शब्द: SLV-III; अर्थ: उपग्रह प्रक्षेपण यान — भारत का पहला स्वदेशी कक्षीय रॉकेट।…

## Query 2 (Hindi)

| Field | Value |
|---|---|
| Query | कलाम को भारत रत्न किस वर्ष प्राप्त हुआ? |
| Answer | कलाम को भारत रत्न 1997 में प्रदान किया गया था [chunk 99]। |
| Source (citation) | page: 20 · section: "संस्थाओं एवं शब्दों की शब्दावली" · chunk_id: 99 · score: 0.85 |
| Expected (from document) | 1997 |

Other retrieved chunks:

- page: 16 · section: "पुरस्कार एवं सम्मान" · chunk_id: 66 · score: 0.85 — कलाम को भारत के सर्वोच्च नागरिक सम्मान तथा अनेक अंतरराष्ट्रीय मान्यताएँ प्राप्त हुईं। कुछ प्रमुख:…
- page: 4 · section: "रामेश्वरम में बचपन" · chunk_id: 10 · score: 0.84 — कलाम का जन्म 15 अक्टूबर 1931 को तमिलनाडु के दक्षिण-पूर्वी तट के निकट पम्बन द्वीप पर स्थित मंदिर-नगरी रामेश्वरम…
- page: 3 · section: "ए.पी.जे. अब्दुल कलाम कौन थे?" · chunk_id: 6 · score: 0.84 — कलाम का जीवन एक असंभव-सी यात्रा थी: दक्षिण भारत के एक छोटे-से द्वीपीय कस्बे से, जहाँ बचपन में वे परिवार की मदद…

## Query 3 (Hindi)

| Field | Value |
|---|---|
| Query | पोखरण-II में कलाम की क्या भूमिका थी? |
| Answer | पोखरण-II (1998) में, कलाम ने रक्षा मंत्री के वैज्ञानिक सलाहकार और डीआरडीओ के प्रमुख के रूप में परमाणु ऊर्जा विभाग के वैज्ञानिकों के साथ मिलकर एक केंद्रीय संगठनात्मक भूमिका निभाई थी [chunk 39]। |
| Source (citation) | page: 10 · section: "पोखरण-II: 1998 के परमाणु परीक्षण" · chunk_id: 39 · score: 0.87 |
| Expected (from document) | केंद्रीय संगठनात्मक भूमिका |

Other retrieved chunks:

- page: 10 · section: "पोखरण-II: 1998 के परमाणु परीक्षण" · chunk_id: 40 · score: 0.86 — ये परीक्षण कड़ी गोपनीयता और सटीक समन्वय के साथ किए गए, और इन्होंने भारत की सामरिक स्थिति में एक मोड़ अंकित किय…
- page: 10 · section: "पोखरण-II: 1998 के परमाणु परीक्षण" · chunk_id: 41 · score: 0.86 — कलाम के लिए ये उस दशकों लंबे प्रयास की परिणति थे जिसका उद्देश्य देश को उन क्षेत्रों में तकनीकी रूप से आत्मनिर्…
- page: 10 · section: "पोखरण-II: 1998 के परमाणु परीक्षण" · chunk_id: 42 · score: 0.85 — अग्नि की उड़ान में वर्णित अवधि के अंत के निकट आने के कारण, ये परीक्षण संस्मरण को एक "मंज़िल पर पहुँचने" का भाव…

## Query 4 (English)

| Field | Value |
|---|---|
| Query | Which institution did Kalam attend to study aeronautical engineering? |
| Answer | कलाम ने वैमानिकी इंजीनियरिंग पढ़ने के लिए चेन्नई के मद्रास इंस्टीट्यूट ऑफ टेक्नोलॉजी (एमआईटी) में प्रवेश लिया [chunk 19]। |
| Source (citation) | page: 6 · section: "कॉलेज के वर्ष और उड़ान का आकर्षण" · chunk_id: 19 · score: 0.84 |
| Expected (from document) | Madras Institute of Technology (MIT), Chennai |

Other retrieved chunks:

- page: 6 · section: "कॉलेज के वर्ष और उड़ान का आकर्षण" · chunk_id: 21 · score: 0.81 — एमआईटी में उनका सामना कठोर शिक्षकों से हुआ जिन्होंने उन्हें ख़ूब परिश्रम करवाया। एक प्रसिद्ध प्रसंग में, एक पर…
- page: 7 · section: "वैज्ञानिक करियर के पहले कदम" · chunk_id: 23 · score: 0.80 — कलाम ने अपना व्यावसायिक जीवन भारत के रक्षा प्रतिष्ठान के अंग, तकनीकी विकास एवं उत्पादन निदेशालय में आरंभ किया,…
- page: 8 · section: "इसरो के वर्ष और SLV-III" · chunk_id: 27 · score: 0.79 — इसरो में कलाम उपग्रह प्रक्षेपण यान — SLV-III — के निर्माण की परियोजना का नेतृत्व करने तक पहुँचे, जो भारत का पह…

## Query 5 (English)

| Field | Value |
|---|---|
| Query | Who co-wrote the autobiography, and in what year was it published? |
| Answer | यह आत्मकथा वैज्ञानिक अरुण तिवारी के साथ मिलकर लिखी गई थी और 1999 में प्रकाशित हुई थी [chunk 8]। |
| Source (citation) | page: 3 · section: "ए.पी.जे. अब्दुल कलाम कौन थे?" · chunk_id: 8 · score: 0.79 |
| Expected (from document) | Arun Tiwari; 1999 |

Other retrieved chunks:

- page: 3 · section: "ए.पी.जे. अब्दुल कलाम कौन थे?" · chunk_id: 7 · score: 0.78 — उन्होंने लगभग चार दशक भारत के अंतरिक्ष एवं रक्षा अनुसंधान के केंद्र में बिताए — पहले भारतीय अंतरिक्ष अनुसंधान …
- page: 22 · section: "त्वरित तथ्य-सारांश" · chunk_id: 112 · score: 0.78 — क्षेत्र: आत्मकथा; तथ्य: अग्नि की उड़ान (1999), अरुण तिवारी के साथ…
- page: 17 · section: "जीवन-रेखा (टाइमलाइन)" · chunk_id: 82 · score: 0.78 — वर्ष: 1999; पड़ाव: अग्नि की उड़ान प्रकाशित (अरुण तिवारी के साथ)।…

## Query 6 (English)

| Field | Value |
|---|---|
| Query | How and where did Kalam die in 2015? |
| Answer | 2015 में कलाम का निधन 27 जुलाई को शिलांग के भारतीय प्रबंधन संस्थान में विद्यार्थियों को व्याख्यान देते समय हुआ था [chunk 64, chunk 85]। |
| Source (citation) | page: 15 · section: "अंतिम क्षण तक शिक्षक (2007–2015)" · chunk_id: 64 · score: 0.80 |
| Expected (from document) | Collapsed while lecturing at IIM Shillong (27 July 2015) |

Other retrieved chunks:

- page: 17 · section: "जीवन-रेखा (टाइमलाइन)" · chunk_id: 85 · score: 0.80 — वर्ष: 2015; पड़ाव: 27 जुलाई को शिलांग में विद्यार्थियों को व्याख्यान देते हुए निधन।…
- page: 22 · section: "त्वरित तथ्य-सारांश" · chunk_id: 105 · score: 0.80 — क्षेत्र: निधन; तथ्य: 27 जुलाई 2015, शिलांग, मेघालय (आयु 83)…
- page: 15 · section: "अंतिम क्षण तक शिक्षक (2007–2015)" · chunk_id: 62 · score: 0.76 — 2007 में राष्ट्रपति पद छोड़ने के बाद, कलाम उस काम की ओर लौटे जो उन्हें सबसे प्रिय था: शिक्षण। वे भारतीय प्रबंध…
