SELECT
    ud."database",
    COUNT(DISTINCT ud.id)                                                          AS "num_docs",
    MAX(ud."date")                                                                 AS "last_updated",
    STRING_AGG(DISTINCT UPPER(COALESCE(ud."language", 'RU')), '/'
        ORDER BY UPPER(COALESCE(ud."language", 'RU')))                            AS "languages",
    COUNT(DISTINCT dsc.id)                                                         AS "num_chunks",
    COUNT(DISTINCT CASE WHEN t.chunk_id IS NOT NULL THEN dsc.id END)              AS "relevant_chunks",
    ROUND(
        100.0 * COUNT(DISTINCT CASE WHEN t.chunk_id IS NOT NULL THEN dsc.id END)
        / NULLIF(COUNT(DISTINCT dsc.id), 0),
        1
    )                                                                              AS "relevant_pct"
FROM public.uploaded_document ud
LEFT JOIN public.document_section ds ON ud.id = ds.uploaded_document_id
LEFT JOIN public.document_section_chunk dsc ON ds.id = dsc.document_section_id
LEFT JOIN (
    SELECT chunk_id FROM public.taxonomy
    UNION
    SELECT chunk_id FROM public.taxonomy_annotation
    WHERE is_relevant = true AND "HLTP" IS NOT NULL
) t ON dsc.id = t.chunk_id
GROUP BY ud."database"
ORDER BY MAX(ud."date") DESC NULLS LAST, COUNT(DISTINCT ud.id) DESC;
