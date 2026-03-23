SELECT "database", COUNT(*) AS "num_docs", MAX("date") AS "last_updated"
FROM public.uploaded_document
GROUP BY "database"
ORDER BY MAX("date") DESC NULLS LAST, COUNT(*) DESC;
