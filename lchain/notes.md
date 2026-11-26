```
SELECT c.name, count(e.id)
FROM langchain_pg_collection c
LEFT JOIN langchain_pg_embedding e ON e.collection_id = c.uuid
GROUP BY c.name;
```
