# Retrieval evaluation

Embedding model `intfloat/multilingual-e5-small` · k = 5. A hit = a retrieved chunk containing ALL gold substrings for the query (see `rag/queries.py`).

| Configuration | hit@1 | hit@3 | hit@5 | MRR |
|---|---|---|---|---|
| kind filter ON (default) | 0.83 | 1.00 | 1.00 | 0.92 |
| kind filter OFF (naive) | 0.83 | 1.00 | 1.00 | 0.92 |

| Configuration | Lang | Query | Rank of first gold chunk |
|---|---|---|---|
| kind filter ON (default) | hi | SLV-III ने किस उपग्रह को कक्षा में स्थापित किया और किस वर्ष? | 1 |
| kind filter ON (default) | hi | कलाम को भारत रत्न किस वर्ष प्राप्त हुआ? | 2 |
| kind filter ON (default) | hi | पोखरण-II में कलाम की क्या भूमिका थी? | 1 |
| kind filter ON (default) | en | Which institution did Kalam attend to study aeronautical engineering? | 1 |
| kind filter ON (default) | en | Who co-wrote the autobiography, and in what year was it published? | 1 |
| kind filter ON (default) | en | How and where did Kalam die in 2015? | 1 |
| kind filter OFF (naive) | hi | SLV-III ने किस उपग्रह को कक्षा में स्थापित किया और किस वर्ष? | 1 |
| kind filter OFF (naive) | hi | कलाम को भारत रत्न किस वर्ष प्राप्त हुआ? | 2 |
| kind filter OFF (naive) | hi | पोखरण-II में कलाम की क्या भूमिका थी? | 1 |
| kind filter OFF (naive) | en | Which institution did Kalam attend to study aeronautical engineering? | 1 |
| kind filter OFF (naive) | en | Who co-wrote the autobiography, and in what year was it published? | 1 |
| kind filter OFF (naive) | en | How and where did Kalam die in 2015? | 1 |